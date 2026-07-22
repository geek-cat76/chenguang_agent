from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import get_db
from src.core.base_schema import ResponseSchema
from src.modules.user.schema import UserCreate, UserRead
from src.modules.user.service import UserService
from src.core.deps import get_current_user
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


@router.get("", response_model=ResponseSchema[list[UserRead]], summary="获取用户列表")
async def list_users(
    offset: int = 0,
    limit: int = 100,
    svc: UserService = Depends(get_user_service),
):
    users = await svc.list_users(offset, limit)
    return ResponseSchema(data=[UserRead.model_validate(u) for u in users])