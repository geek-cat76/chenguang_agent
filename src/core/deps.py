from fastapi import Depends, Query
from redis.asyncio import Redis
from sqlalchemy.orm import raiseload
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import get_db
from src.infra.redis_cache import get_redis_client
from src.core.exceptions import BizException
from src.utils.jwt_utils import verify_jwt, oauth2_scheme
from src.utils.permission_cache import PermissionCache
from src.modules.user.model import User


_RBAC_PERMISSIONS_ATTR = "_rbac_permission_codes"


class PageParams:
    """通用分页参数，通过 Depends 注入到接口中。"""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        keyword: str | None = Query(None, description="搜索关键词"),
    ):
        self.page = page
        self.page_size = page_size
        self.keyword = keyword

    @property
    def offset(self) -> int:
        """计算 SQL OFFSET。"""
        return (self.page - 1) * self.page_size


def _collect_user_rbac(user: User) -> tuple[set[str], set[str]]:
    permissions: set[str] = set()
    roles: set[str] = set()
    for role in user.roles:
        roles.add(role.code)
        permissions.update(permission.code for permission in role.permissions)
    return permissions, roles


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> User:
    """从 JWT token 中解析当前登录用户，用于保护接口"""
    try:
        payload = verify_jwt(token)
        user_id = int(payload.get("id"))
    except Exception:
        raise BizException(code=401, message="未登录或 token 已过期")

    permission_cache = PermissionCache(redis)
    cached_permissions = await permission_cache.get_permissions(user_id)

    # A cache hit only needs the user row for status validation. Prevent the
    # model-level selectin relationships from loading the whole RBAC graph.
    options = (raiseload(User.roles),) if cached_permissions is not None else ()
    user = await db.get(User, user_id, options=options)
    if not user:
        raise BizException(code=401, message="用户不存在")
    if not user.is_active:
        raise BizException(code=401, message="账号已被禁用")

    if cached_permissions is None:
        permissions, roles = _collect_user_rbac(user)
        await permission_cache.set_user_cache(user.id, permissions, roles)
        cached_permissions = permissions

    # Reuse the snapshot in downstream permission dependencies. This avoids a
    # second Redis read racing with TTL expiry or cache invalidation.
    setattr(user, _RBAC_PERMISSIONS_ATTR, cached_permissions)

    return user


def require_permission(permission_code: str):
    """
    返回一个 FastAPI 依赖函数，用于校验当前用户是否拥有指定权限。

    使用方式：Depends(require_permission("user:list"))
    """
    async def _check(
        current_user: User = Depends(get_current_user),
        redis: Redis = Depends(get_redis_client),
    ) -> User:
        # 1. 超级管理员直接放行
        if current_user.is_superuser:
            return current_user

        # 2. 优先读缓存；未命中时从 ORM 关系重建权限和角色两个 Key
        user_permissions = getattr(current_user, _RBAC_PERMISSIONS_ATTR, None)
        if user_permissions is None:
            permission_cache = PermissionCache(redis)
            user_permissions = await permission_cache.get_permissions(current_user.id)
        if user_permissions is None:
            user_permissions, roles = _collect_user_rbac(current_user)
            await permission_cache.set_user_cache(
                current_user.id,
                user_permissions,
                roles,
            )

        # 3. 检查目标权限是否在集合中
        if permission_code not in user_permissions:
            raise BizException(code=403, message=f"无权限: {permission_code}")

        return current_user

    return _check
