from src.core.base_repository import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.modules.permission.model import Permission

class PermissionRepository(BaseRepository[Permission]):
    def __init__(self, db: AsyncSession):
        super().__init__(Permission, db)

    async def get_by_code(self, code: str) -> Permission | None:
        # 根据 code 查询权限, code 是唯一的，所以返回值是 Permission 或 None
        stmt = select(Permission).where(Permission.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[int]) -> list[Permission]:
        result = await self.db.scalars(select(Permission).where(Permission.id.in_(ids)))
        return result.all()

    # 分页搜索
    async def search_page(self, offset: int,
                          limit: int,
                          keyword: str | None) -> tuple[list[Permission], int]:
        return await self.get_page(offset, limit, keyword, self.SEARCH_FIELDS)