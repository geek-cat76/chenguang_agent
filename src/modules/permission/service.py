from src.core.exceptions import BizException
from src.infra.database import AsyncSession
from src.modules.permission.model import Permission
from src.modules.permission.repository import PermissionRepository
from src.modules.permission.schema import PermissionCreate, PermissionUpdate

class PermissionService:
    def __init__(self, db: AsyncSession):
        self.repo = PermissionRepository(db)

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

    async def list_permissions(self) -> list[Permission]:
        # 调用 repo.get_all()
        return await self.repo.get_all()

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
        # 2. 调用 repo.delete()
        await self.repo.delete(permission)
        return None
