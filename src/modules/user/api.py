from src.modules.user.schema import UserWithRolesRead
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import get_db
from src.core.base_schema import PageResult, ResponseSchema
from src.modules.user.schema import UserCreate, UserRead
from src.modules.user.service import UserService
from src.core.deps import PageParams, get_current_user
from src.modules.user.model import User


router = APIRouter(prefix="/users", tags=["用户API"])


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


@router.post("", response_model=ResponseSchema[UserRead], summary="创建用户")
async def create_user(
    data: UserCreate,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.create_user(data)
    return ResponseSchema(data=UserRead.model_validate(user))


@router.get("/me", response_model=ResponseSchema[UserRead])
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息（需要 token）"""
    return ResponseSchema(data=UserRead.model_validate(current_user))


@router.get("/{user_id}", response_model=ResponseSchema[UserRead], summary="获取用户详情")
async def get_user(
    user_id: int,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.get_user(user_id)
    return ResponseSchema(data=UserRead.model_validate(user))


@router.get("", response_model=ResponseSchema[PageResult[UserRead]], summary="获取用户列表")
async def list_users(
    params: PageParams = Depends(),
    svc: UserService = Depends(get_user_service),
):
    page_result = await svc.list_users(params)
    page_result.items = [UserRead.model_validate(user) for user in page_result.items]
    return ResponseSchema(data=page_result)


# PUT   /api/v1/users/{user_id}/roles   给用户分配角色
@router.put("/{user_id}/roles", response_model=ResponseSchema[UserRead], summary="给用户分配角色")
async def assign_roles_to_user(
    user_id: int,
    role_ids: list[int],
    svc: UserService = Depends(get_user_service),
):
    user = await svc.assign_roles(user_id, role_ids)
    return ResponseSchema(data=UserRead.model_validate(user))

# GET   /api/v1/users/{user_id}/roles   查看用户的角色列表
@router.get("/{user_id}/roles", response_model=ResponseSchema[list[UserWithRolesRead]], summary="查看用户的角色列表")
async def get_user_roles(
    user_id: int,
    svc: UserService = Depends(get_user_service),
):
    user = await svc.get_user_with_roles(user_id)
    return ResponseSchema(data=[UserWithRolesRead.model_validate(user)])
