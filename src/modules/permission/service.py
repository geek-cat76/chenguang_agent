from functools import partial

from src.core.exceptions import BizException
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.permission.model import Permission
from src.modules.permission.repository import PermissionRepository
from src.modules.permission.schema import PermissionCreate, PermissionUpdate
from src.core.base_schema import PageResult
from src.core.deps import PageParams
from src.modules.role.model import role_permissions, user_roles
from src.utils.permission_cache import PermissionCache
from src.infra.database import add_after_commit_callback

class PermissionService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.repo = PermissionRepository(db)
        self.db = db
        self.permission_cache = PermissionCache(redis) if redis else None

    async def _get_affected_user_ids(self, permission_id: int) -> list[int]:
        stmt = (
            select(user_roles.c.user_id)
            .select_from(
                user_roles.join(
                    role_permissions,
                    role_permissions.c.role_id == user_roles.c.role_id,
                )
            )
            .where(role_permissions.c.permission_id == permission_id)
            .distinct()
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_permission(self, data: PermissionCreate) -> Permission:
        # 1. 检查 code 是否已存在，已存在则抛 BizException
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise BizException(code=400, message="权限码已经存在")

        # 2. 创建 Permission 对象
        permission = Permission(
            code=data.code,
            name=data.name,
            description=data.description
        )
        # 3. 调用 repo.create() 创建权限
        await self.repo.create(permission)
        return permission

    async def get_permission(self, permission_id: int) -> Permission:
        # 查不到抛 BizException(code=404)
        permission = await self.repo.get_by_id(permission_id)
        if not permission:
            raise BizException(code=404, message="权限不存在")
        return permission

    async def list_permissions(self, params: PageParams) -> PageResult:
        items, total = await self.repo.search_page(
            offset=params.offset,
            limit=params.page_size,
            keyword=params.keyword,
        )
        return PageResult(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
        )

    async def update_permission(self, permission_id: int, data: PermissionUpdate) -> Permission:
        # 1. 查找权限，不存在抛异常
        permission = await self.get_permission(permission_id)
        if not permission:
            raise BizException(code=404, message="权限不存在")
        # 2. 只更新 data 中非 None 的字段
        if data.name is not None:
            permission.name = data.name
        if data.description is not None:
            permission.description = data.description
        # 3. 调用 repo.update()
        await self.repo.update(permission)
        return permission

    async def delete_permission(self, permission_id: int) -> None:
        # 1. 查找权限，不存在抛异常
        permission = await self.get_permission(permission_id)
        if not permission:
            raise BizException(code=404, message="权限不存在")
        affected_user_ids = await self._get_affected_user_ids(permission_id)

        # 2. 调用 repo.delete()
        await self.repo.delete(permission)
        if self.permission_cache and affected_user_ids:
            await self.permission_cache.delete_user_cache_batch(affected_user_ids)
            add_after_commit_callback(
                self.db,
                partial(
                    self.permission_cache.delete_user_cache_batch,
                    affected_user_ids,
                ),
            )
        return None
