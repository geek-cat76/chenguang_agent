from fastapi import APIRouter,Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from src.modules.auth.schema import LoginRequest, TokenResponse
from src.modules.auth.service import AuthService
from src.infra.database import get_db
from src.infra.redis_cache import get_redis_client
from src.core.base_schema import ResponseSchema


router = APIRouter(prefix="/auth", tags=["auth"])

def get_auth_service(
    db: AsyncSession = Depends(get_db),
    redis:Redis = Depends(get_redis_client)) -> AuthService:
    return AuthService(db,redis)

# 
@router.post("/login", response_model=ResponseSchema[TokenResponse])
async def login(login_request: LoginRequest,auth_service: AuthService = Depends(get_auth_service)) -> ResponseSchema[TokenResponse]:
    """
        登陆接口
    """
    resp = await auth_service.login(login_request)
    return ResponseSchema(data=resp)
