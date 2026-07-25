from src.modules.role.schema import RoleAssignPermissions
from src.modules.permission.schema import PermissionRead
from src.core.base_schema import PageResult, ResponseSchema
from src.core.deps import PageParams
from src.modules.role.schema import RoleRead
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.role.schema import RoleCreate, RoleUpdate, RoleAssignPermissions

from src.modules.role.service import RoleService
from src.infra.database import get_db
from src.infra.redis_cache import get_redis_client

router = APIRouter(prefix="/roles", tags=["Role"])

def get_role_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> RoleService:
    return RoleService(db, redis)

# POST  /api/v1/roles   创建角色
@router.post("", response_model=ResponseSchema[RoleRead])
async def create_role(role: RoleCreate, service: RoleService = Depends(get_role_service)):
    data = await service.create_role(role)
    return ResponseSchema[RoleRead](data=RoleRead.model_validate(data))

# GET   /api/v1/roles/{role_id} 角色详情（含权限列表）
@router.get("/{role_id}", response_model=ResponseSchema[RoleRead])
async def get_role(role_id: int, service: RoleService = Depends(get_role_service)):
    data = await service.get_role(role_id)
    permissions = [PermissionRead.model_validate(p) for p in data.permissions]

    rd = RoleRead.model_validate(data)
    rd.permissions = permissions
    return ResponseSchema[RoleRead](data=rd)

# GET   /api/v1/roles   角色列表
@router.get("", response_model=ResponseSchema[PageResult[RoleRead]], summary="获取角色列表")
async def get_roles(
    params: PageParams = Depends(),
    service: RoleService = Depends(get_role_service),
):
    page_result = await service.list_roles(params)
    page_result.items = [RoleRead.model_validate(role) for role in page_result.items]
    return ResponseSchema(data=page_result)

# PUT   /api/v1/roles/{role_id} 更新角色
@router.put("/{role_id}", response_model=ResponseSchema[RoleRead])
async def update_role(role_id: int, role: RoleUpdate, service: RoleService = Depends(get_role_service)):
    data = await service.update_role(role_id, role)
    return ResponseSchema[RoleRead](data=RoleRead.model_validate(data))

# DELETE    /api/v1/roles/{role_id} 删除角色
@router.delete("/{role_id}", response_model=ResponseSchema[None])
async def delete_role(role_id: int, service: RoleService = Depends(get_role_service)):
    await service.delete_role(role_id)
    return ResponseSchema[None](data=None)

# PUT   /api/v1/roles/{role_id}/permissions 给角色分配权限
@router.put("/{role_id}/permissions", response_model=ResponseSchema[RoleRead])
async def update_role_permissions(role_id: int, role_permissions: RoleAssignPermissions, 
        service: RoleService = Depends(get_role_service)):
    data = await service.assign_permissions(role_id, role_permissions.permission_ids)
    return ResponseSchema[RoleRead](data=RoleRead.model_validate(data))
