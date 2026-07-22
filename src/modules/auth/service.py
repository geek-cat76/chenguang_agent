from datetime import datetime
from src.core.exceptions import BizException
from src.modules.user.repository import UserRepository
from src.modules.captcha.schema import CaptchaVerifyRequest
from src.modules.captcha.service import CaptchaService
from src.modules.auth.schema import LoginRequest, TokenResponse
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from src.utils.jwt_utils import encode_jwt, verify_jwt
from src.utils.password_utils import verify_password


"""
    登陆服务
    1. 验证码校验   :  注入redis
    2. 用户查找     :  注入db
    3. 密码校验
    4. 用户状态校验
    5. 生成 JWT 令牌
"""

class AuthService:
    def __init__(self, db: AsyncSession,redis:Redis):
        self.db = db
        self.redis = redis
        self.captcha_service = CaptchaService(redis)
        self.user_repo = UserRepository(db)


    async def login(self,login_request: LoginRequest) -> TokenResponse|None:
        """
            登陆接口
        """
        # 验证码校验
        captcha = CaptchaVerifyRequest(
            key=login_request.captcha_key,
            code=login_request.captcha_code,
        )
        if not await self.captcha_service.verify_captcha(captcha):
            raise BizException(code=10002, message="验证码错误")
        
        # 用户查找
        user = await self.user_repo.get_by_username(login_request.username)
        
        if not user:
            raise BizException(code=10002, message="用户名不存在")
        
        # 密码校验
        if not verify_password(login_request.password, user.hashed_password):
            raise BizException(code=10003, message="密码错误")

        # 用户状态校验
        if not user.is_active:
            raise BizException(code=10004, message="用户已被禁用")

        # 生成 JWT 令牌
        access_token = encode_jwt({
                "id": user.id,
                "username": user.username,
                "is_superuser": user.is_superuser,
            })
        # 更新登陆时间
        user.last_login = datetime.now()
        await self.db.flush()
        
        return TokenResponse(access_token=access_token)
        
        
