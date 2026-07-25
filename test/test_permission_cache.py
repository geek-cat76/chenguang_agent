import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, sentinel

import pytest

import src.core.deps as deps
import src.infra.database as database_module
from src.core.deps import require_permission
from src.core.exceptions import BizException
from src.infra.database import run_after_commit_callbacks
from src.modules.permission.service import PermissionService
from src.modules.role.service import RoleService
from src.modules.user.service import UserService
from src.utils.permission_cache import (
    CACHE_TTL,
    PERM_CACHE_PREFIX,
    ROLE_CACHE_PREFIX,
    PermissionCache,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


class FakePipeline:
    def __init__(self, redis, transaction):
        self.redis = redis
        self.transaction = transaction
        self.commands = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    def set(self, key, value, ex=None):
        self.commands.append((key, value, ex))
        return self

    async def execute(self):
        for key, value, ttl in self.commands:
            await self.redis.set(key, value, ex=ttl)
        return [True] * len(self.commands)


class FakeRedis:
    def __init__(self):
        self.data = {}
        self.expirations = {}
        self.delete_calls = []
        self.pipelines = []

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value
        self.expirations[key] = ex
        return True

    async def delete(self, *keys):
        self.delete_calls.append(keys)
        deleted = 0
        for key in keys:
            if key in self.data:
                deleted += 1
                del self.data[key]
                self.expirations.pop(key, None)
        return deleted

    def pipeline(self, transaction=True):
        pipeline = FakePipeline(self, transaction)
        self.pipelines.append(pipeline)
        return pipeline


class EventRedis(FakeRedis):
    def __init__(self, events):
        super().__init__()
        self.events = events

    async def delete(self, *keys):
        self.events.append("invalidate")
        return await super().delete(*keys)


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def scalars(self):
        return self

    def all(self):
        return list(self.values)


class AffectedUsersDB:
    def __init__(self, user_ids, events=None):
        self.user_ids = user_ids
        self.events = events
        self.statements = []
        self.info = {}

    async def execute(self, statement):
        self.statements.append(statement)
        if self.events is not None:
            self.events.append("lookup")
        return FakeScalarResult(self.user_ids)


class GetUserDB:
    def __init__(self, user):
        self.user = user
        self.get_calls = []

    async def get(self, model, user_id, *, options=()):
        self.get_calls.append((model, user_id, options))
        return self.user


class TransactionSession:
    def __init__(self, events):
        self.events = events
        self.info = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def commit(self):
        self.events.append("commit")

    async def rollback(self):
        self.events.append("rollback")


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("permissions", "roles"),
    [
        ({"user:list", "role:list"}, {"admin", "developer"}),
        (set(), set()),
    ],
)
async def test_set_user_cache_round_trips_both_keys(permissions, roles):
    redis = FakeRedis()
    cache = PermissionCache(redis)

    await cache.set_user_cache(7, permissions, roles)

    permission_key = f"{PERM_CACHE_PREFIX}7"
    role_key = f"{ROLE_CACHE_PREFIX}7"
    assert set(json.loads(redis.data[permission_key])) == permissions
    assert set(json.loads(redis.data[role_key])) == roles
    assert redis.expirations == {
        permission_key: CACHE_TTL,
        role_key: CACHE_TTL,
    }
    assert redis.pipelines[0].transaction is True
    assert await cache.get_permissions(7) == permissions
    assert await cache.get_roles(7) == roles


@pytest.mark.anyio
async def test_cached_empty_sets_are_hits_not_misses():
    redis = FakeRedis()
    cache = PermissionCache(redis)
    await cache.set_user_cache(8, set(), set())

    assert await cache.get_permissions(8) == set()
    assert await cache.get_roles(8) == set()
    assert await cache.get_permissions(404) is None
    assert await cache.get_roles(404) is None


@pytest.mark.anyio
async def test_delete_user_cache_batch_removes_both_keys_for_each_user():
    redis = FakeRedis()
    cache = PermissionCache(redis)
    for user_id in (1, 2, 3):
        await cache.set_user_cache(
            user_id,
            {f"permission:{user_id}"},
            {f"role:{user_id}"},
        )

    await cache.delete_user_cache_batch([1, 3])

    assert redis.delete_calls[-1] == (
        f"{PERM_CACHE_PREFIX}1",
        f"{ROLE_CACHE_PREFIX}1",
        f"{PERM_CACHE_PREFIX}3",
        f"{ROLE_CACHE_PREFIX}3",
    )
    assert await cache.get_permissions(1) is None
    assert await cache.get_roles(1) is None
    assert await cache.get_permissions(3) is None
    assert await cache.get_roles(3) is None
    assert await cache.get_permissions(2) == {"permission:2"}
    assert await cache.get_roles(2) == {"role:2"}

    delete_call_count = len(redis.delete_calls)
    await cache.delete_user_cache_batch([])
    assert len(redis.delete_calls) == delete_call_count


@pytest.mark.anyio
async def test_require_permission_populates_both_keys_on_cache_miss():
    redis = FakeRedis()
    permission = SimpleNamespace(code="article:read")
    role = SimpleNamespace(code="editor", permissions=[permission])
    user = SimpleNamespace(id=21, is_superuser=False, roles=[role])

    checked_user = await require_permission("article:read")(
        current_user=user,
        redis=redis,
    )

    assert checked_user is user
    cache = PermissionCache(redis)
    assert await cache.get_permissions(user.id) == {"article:read"}
    assert await cache.get_roles(user.id) == {"editor"}


@pytest.mark.anyio
async def test_require_permission_treats_cached_empty_permissions_as_a_hit():
    class RolesMustNotBeRead:
        def __iter__(self):
            raise AssertionError("ORM roles were read despite a permission cache hit")

    redis = FakeRedis()
    cache = PermissionCache(redis)
    await cache.set_user_cache(22, set(), {"viewer"})
    user = SimpleNamespace(id=22, is_superuser=False, roles=RolesMustNotBeRead())

    with pytest.raises(BizException) as exc_info:
        await require_permission("article:write")(
            current_user=user,
            redis=redis,
        )

    assert exc_info.value.code == 403
    assert exc_info.value.message == "无权限: article:write"


@pytest.mark.anyio
async def test_get_current_user_cache_hit_uses_raiseload_without_rewriting_cache(
    monkeypatch,
):
    redis = FakeRedis()
    cache = PermissionCache(redis)
    await cache.set_user_cache(71, {"article:read"}, {"viewer"})
    initial_pipeline_count = len(redis.pipelines)
    initial_cache = dict(redis.data)

    user = SimpleNamespace(id=71, is_active=True)
    db = GetUserDB(user)
    raiseload = Mock(return_value=sentinel.roles_option)
    monkeypatch.setattr(deps, "raiseload", raiseload)
    monkeypatch.setattr(deps, "verify_jwt", lambda token: {"id": "71"})

    current_user = await deps.get_current_user(
        token="cached-token",
        db=db,
        redis=redis,
    )

    assert current_user is user
    raiseload.assert_called_once_with(deps.User.roles)
    assert db.get_calls == [
        (deps.User, 71, (sentinel.roles_option,)),
    ]
    assert len(redis.pipelines) == initial_pipeline_count
    assert redis.data == initial_cache


@pytest.mark.anyio
async def test_get_current_user_cache_miss_loads_graph_and_writes_both_sets(
    monkeypatch,
):
    redis = FakeRedis()
    read_permission = SimpleNamespace(code="article:read")
    write_permission = SimpleNamespace(code="article:write")
    user = SimpleNamespace(
        id=72,
        is_active=True,
        roles=[
            SimpleNamespace(
                code="editor",
                permissions=[read_permission, write_permission],
            ),
            SimpleNamespace(code="viewer", permissions=[read_permission]),
        ],
    )
    db = GetUserDB(user)
    raiseload = Mock(return_value=sentinel.roles_option)
    monkeypatch.setattr(deps, "raiseload", raiseload)
    monkeypatch.setattr(deps, "verify_jwt", lambda token: {"id": 72})

    current_user = await deps.get_current_user(
        token="uncached-token",
        db=db,
        redis=redis,
    )

    assert current_user is user
    raiseload.assert_not_called()
    assert db.get_calls == [(deps.User, 72, ())]
    cache = PermissionCache(redis)
    assert await cache.get_permissions(72) == {"article:read", "article:write"}
    assert await cache.get_roles(72) == {"editor", "viewer"}
    assert redis.pipelines[-1].transaction is True


@pytest.mark.anyio
async def test_permission_check_reuses_request_snapshot_if_cache_is_invalidated(
    monkeypatch,
):
    class RolesMustNotBeRead:
        def __iter__(self):
            raise AssertionError("ORM roles were read after a request-level cache hit")

    redis = FakeRedis()
    cache = PermissionCache(redis)
    await cache.set_user_cache(73, {"article:read"}, {"viewer"})
    user = SimpleNamespace(
        id=73,
        is_active=True,
        is_superuser=False,
        roles=RolesMustNotBeRead(),
    )
    db = GetUserDB(user)
    monkeypatch.setattr(deps, "raiseload", Mock(return_value=sentinel.roles_option))
    monkeypatch.setattr(deps, "verify_jwt", lambda token: {"id": 73})

    current_user = await deps.get_current_user(
        token="cached-token",
        db=db,
        redis=redis,
    )
    await cache.delete_user_cache(73)

    checked_user = await require_permission("article:read")(
        current_user=current_user,
        redis=redis,
    )

    assert checked_user is current_user
    assert await cache.get_permissions(73) is None


@pytest.mark.anyio
async def test_get_db_runs_cache_invalidation_after_commit(monkeypatch):
    events = []
    session = TransactionSession(events)
    monkeypatch.setattr(database_module, "AsyncSessionLocal", lambda: session)

    async def invalidate():
        events.append("invalidate")

    dependency = database_module.get_db()
    yielded_session = await anext(dependency)
    database_module.add_after_commit_callback(yielded_session, invalidate)

    with pytest.raises(StopAsyncIteration):
        await anext(dependency)

    assert events == ["commit", "invalidate"]


@pytest.mark.anyio
async def test_user_service_assign_roles_invalidates_that_users_two_keys():
    redis = FakeRedis()
    cache = PermissionCache(redis)
    await cache.set_user_cache(31, {"article:read"}, {"viewer"})
    await cache.set_user_cache(32, {"article:write"}, {"editor"})

    assigned_roles = [SimpleNamespace(id=2), SimpleNamespace(id=3)]
    user = SimpleNamespace(id=31, roles=[])
    db = SimpleNamespace(info={})
    service = UserService(db=db, redis=redis)
    service.repo = SimpleNamespace(
        get_by_id=AsyncMock(return_value=user),
        update=AsyncMock(return_value=user),
    )
    service.role_repo = SimpleNamespace(
        get_by_ids=AsyncMock(return_value=assigned_roles),
    )

    result = await service.assign_roles(31, [2, 3])

    assert result is user
    assert user.roles == assigned_roles
    service.repo.update.assert_awaited_once_with(user)
    assert await cache.get_permissions(31) is None

    # Simulate a concurrent request refilling stale data before the DB commit.
    await cache.set_user_cache(31, {"stale:permission"}, {"viewer"})

    await run_after_commit_callbacks(db)

    assert redis.delete_calls[-1] == (
        f"{PERM_CACHE_PREFIX}31",
        f"{ROLE_CACHE_PREFIX}31",
    )
    assert await cache.get_permissions(31) is None
    assert await cache.get_roles(31) is None
    assert await cache.get_permissions(32) == {"article:write"}
    assert await cache.get_roles(32) == {"editor"}


@pytest.mark.anyio
async def test_role_service_assign_permissions_invalidates_all_affected_users():
    redis = FakeRedis()
    cache = PermissionCache(redis)
    for user_id in (41, 42, 99):
        await cache.set_user_cache(user_id, {"old:permission"}, {"member"})

    db = AffectedUsersDB([41, 42])
    role = SimpleNamespace(id=5, permissions=[])
    permissions = [SimpleNamespace(id=7), SimpleNamespace(id=8)]
    service = RoleService(db=db, redis=redis)
    service.repo = SimpleNamespace(
        get_by_id=AsyncMock(return_value=role),
        update=AsyncMock(return_value=role),
    )
    service.permission_repo = SimpleNamespace(
        get_by_ids=AsyncMock(return_value=permissions),
    )

    result = await service.assign_permissions(5, [7, 8])

    assert result is role
    assert role.permissions == permissions
    assert len(db.statements) == 1
    assert await cache.get_permissions(41) is None

    await cache.set_user_cache(41, {"stale:permission"}, {"member"})
    await cache.set_user_cache(42, {"stale:permission"}, {"member"})

    await run_after_commit_callbacks(db)

    assert redis.delete_calls[-1] == (
        f"{PERM_CACHE_PREFIX}41",
        f"{ROLE_CACHE_PREFIX}41",
        f"{PERM_CACHE_PREFIX}42",
        f"{ROLE_CACHE_PREFIX}42",
    )
    assert await cache.get_permissions(41) is None
    assert await cache.get_permissions(42) is None
    assert await cache.get_permissions(99) == {"old:permission"}


@pytest.mark.anyio
async def test_delete_role_collects_affected_users_before_delete_and_invalidation():
    events = []
    redis = EventRedis(events)
    db = AffectedUsersDB([51, 52], events)
    service = RoleService(db=db, redis=redis)

    async def delete_by_id(role_id):
        assert role_id == 6
        events.append("delete")

    service.repo = SimpleNamespace(delete_by_id=AsyncMock(side_effect=delete_by_id))

    await service.delete_role(6)
    cache = PermissionCache(redis)
    await cache.set_user_cache(51, {"stale:permission"}, {"member"})
    await cache.set_user_cache(52, {"stale:permission"}, {"member"})
    events.append("stale_refill")
    events.append("commit")
    await run_after_commit_callbacks(db)

    assert events == [
        "lookup",
        "delete",
        "invalidate",
        "stale_refill",
        "commit",
        "invalidate",
    ]
    expected_keys = (
        f"{PERM_CACHE_PREFIX}51",
        f"{ROLE_CACHE_PREFIX}51",
        f"{PERM_CACHE_PREFIX}52",
        f"{ROLE_CACHE_PREFIX}52",
    )
    assert redis.delete_calls == [expected_keys, expected_keys]
    assert await cache.get_permissions(51) is None
    assert await cache.get_permissions(52) is None


@pytest.mark.anyio
async def test_delete_permission_collects_affected_users_before_delete_and_invalidation():
    events = []
    redis = EventRedis(events)
    db = AffectedUsersDB([61, 62], events)
    permission = SimpleNamespace(id=9)
    service = PermissionService(db=db, redis=redis)

    async def get_by_id(permission_id):
        assert permission_id == 9
        events.append("get")
        return permission

    async def delete(deleted_permission):
        assert deleted_permission is permission
        events.append("delete")

    service.repo = SimpleNamespace(
        get_by_id=AsyncMock(side_effect=get_by_id),
        delete=AsyncMock(side_effect=delete),
    )

    await service.delete_permission(9)
    cache = PermissionCache(redis)
    await cache.set_user_cache(61, {"stale:permission"}, {"member"})
    await cache.set_user_cache(62, {"stale:permission"}, {"member"})
    events.append("stale_refill")
    events.append("commit")
    await run_after_commit_callbacks(db)

    assert events == [
        "get",
        "lookup",
        "delete",
        "invalidate",
        "stale_refill",
        "commit",
        "invalidate",
    ]
    expected_keys = (
        f"{PERM_CACHE_PREFIX}61",
        f"{ROLE_CACHE_PREFIX}61",
        f"{PERM_CACHE_PREFIX}62",
        f"{ROLE_CACHE_PREFIX}62",
    )
    assert redis.delete_calls == [expected_keys, expected_keys]
    assert await cache.get_permissions(61) is None
    assert await cache.get_permissions(62) is None
