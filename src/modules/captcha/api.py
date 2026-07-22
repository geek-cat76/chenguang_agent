import redis.asyncio as redis
from fastapi import APIRouter, Depends
from src.core.base_schema import ResponseSchema
from src.modules.captcha.schema import CaptchaRead, CaptchaVerifyRequest
from src.modules.captcha.service import CaptchaService
from src.infra.redis_cache import get_redis_client



"""
    验证码模块 API 路由
    1. 前端请求验证码
    2. 验证验证码结果
"""
async def get_captcha_service(redis_client: redis.Redis = Depends(get_redis_client)):
    return CaptchaService(redis_client)



router = APIRouter(prefix="/captcha", tags=["验证码"])

@router.get("", response_model=ResponseSchema[CaptchaRead], summary="获取验证码") 
async def get_captcha(captcha_service: CaptchaService = Depends(get_captcha_service)):
    captcha =  await captcha_service.create_captcha()
    return ResponseSchema[CaptchaRead](data=captcha)


@router.post("",response_model=ResponseSchema[bool], summary="验证验证码")
async def verify_captcha(
    data: CaptchaVerifyRequest,
    captcha_service: CaptchaService = Depends(get_captcha_service),
):
    is_valid = await captcha_service.verify_captcha(data)
    return ResponseSchema[bool](data=is_valid)