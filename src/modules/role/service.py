from functools import partial

from redis.asyncio import Redis
from sqlalchemy import select
from src.core.exceptions import BizException
from src.modules.role.schema import RoleUpdate
from src.modules.role.model import Role, user_roles
from src.modules.role.schema import RoleCreate
from src.modules.permission.repository import PermissionRepository
from src.modules.role.repository import RoleRepository
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.base_schema import PageResult
from src.core.deps import PageParams
from src.utils.permission_cache import PermissionCache
from src.infra.database import add_after_commit_callback

class RoleService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.repo = RoleRepository(db)
        self.permission_repo = PermissionRepository(db)
        self.db = db
        self.permission_cache = PermissionCache(redis) if redis else None

    async def _get_affected_user_ids(self, role_id: int) -> list[int]:
        stmt = select(user_roles.c.user_id).where(user_roles.c.role_id == role_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_role(self, data: RoleCreate) -> Role:
        # 检查 code 是否已存在
        role = await self.repo.get_by_code(data.code)
        if role:
            raise BizException(f"角色 {data.code}-{data.name} 已经存在")

        role = Role(**data.model_dump())
        role = await self.repo.create(role)
        return role

    async def get_role(self, role_id: int) -> Role:
        # 查不到抛异常
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise BizException(f"角色 {role_id} 不存在")
        return role

    async def list_roles(self, params: PageParams) -> PageResult:
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

    async def update_role(self, role_id: int, data: RoleUpdate) -> Role:
        # 查不到抛异常
        role = await self.get_role(role_id)
        if not role:
            raise BizException(f"角色 {role_id} 不存在")
        role.name = data.name or role.name
        role.description = data.description or role.description
        role = await self.repo.update(role)
        return role

    async def delete_role(self, role_id: int) -> None:
        affected_user_ids = await self._get_affected_user_ids(role_id)
        await self.repo.delete_by_id(role_id)
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

    async def assign_permissions(self, role_id: int, permission_ids: list[int]) -> Role:
        # 这是本节的重点方法！
        # 1. 查找角色，不存在抛异常
        role = await self.get_role(role_id)
        if not role:
            raise BizException(f"角色 {role_id} 不存在")
        # 2. 根据 permission_ids 批量查询 Permission 对象
        permission_list = await self.permission_repo.get_by_ids(permission_ids)
        
        # 3. 校验：如果查到的数量 != 传入的数量，说明有无效 ID，抛异常
        if len(permission_list) != len(permission_ids):
            raise BizException(f"权限 ID 列表中包含无效 ID")
        
        # 4. 直接替换角色的权限列表：role.permissions = permission_list
        role.permissions = permission_list

        # 5. flush + refresh
        await self.repo.update(role)
        affected_user_ids = await self._get_affected_user_ids(role_id)
        if self.permission_cache and affected_user_ids:
            await self.permission_cache.delete_user_cache_batch(affected_user_ids)
            add_after_commit_callback(
                self.db,
                partial(
                    self.permission_cache.delete_user_cache_batch,
                    affected_user_ids,
                ),
            )
        # 6. 返回更新后的 role（会自动带上新的 permissions）
        return role
