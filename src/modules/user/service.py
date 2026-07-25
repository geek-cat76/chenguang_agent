from functools import partial

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import BizException
from src.modules.user.model import User
from src.modules.user.schema import UserCreate
from src.modules.user.repository import UserRepository
from src.utils.password_utils import hash_password
from src.modules.role.repository import RoleRepository
from src.core.base_schema import PageResult
from src.core.deps import PageParams
from src.utils.permission_cache import PermissionCache
from src.infra.database import add_after_commit_callback


class UserService:
    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.permission_cache = PermissionCache(redis) if redis else None

    async def create_user(self, data: UserCreate) -> User:
        if await self.repo.get_by_username(data.username):
            raise BizException(code=400, message="用户名已存在")
        if await self.repo.get_by_email(data.email):
            raise BizException(code=400, message="邮箱已存在")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),  # 项目开发时用 bcrypt 等加密
        )
        return await self.repo.create(user)

    async def get_user(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise BizException(code=404, message="用户不存在")
        return user

    async def list_users(self, params: PageParams) -> PageResult:
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

    async def assign_roles(self, user_id: int, role_ids: list[int]) -> User:
        
        # 1. 查找用户，不存在抛异常
        user = await self.get_user(user_id)
        if not user:
            raise BizException(code=400, message="用户不存在")
        
        # 2. 通过 RoleRepository.get_by_ids(role_ids) 批量查询角色
        role_list = await self.role_repo.get_by_ids(role_ids)

        # 3. 校验数量是否匹配
        if len(role_list) != len(role_ids):
            raise BizException(code=400, message="角色不存在")

        # 4. user.roles = role_list（整体替换）
        user.roles = role_list
        
        # 5. flush + refresh
        user = await self.repo.update(user)

        if self.permission_cache:
            # Delete before commit so a Redis failure rolls back the DB change,
            # then delete again after commit to remove any concurrent stale fill.
            await self.permission_cache.delete_user_cache(user_id)
            add_after_commit_callback(
                self.db,
                partial(self.permission_cache.delete_user_cache, user_id),
            )
        
        # 6. 返回 user
        return user

    async def get_user_with_roles(self, user_id: int) -> User:
        # 和 get_user 一样，但返回的 User 对象会自动带上 roles
        user = await self.get_user(user_id)
        return user
