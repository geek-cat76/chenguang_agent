import redis.asyncio as redis
import random
import string
import base64
import uuid
from captcha.image import ImageCaptcha
from src.modules.captcha.schema import CaptchaRead, CaptchaVerifyRequest
from src.core.exceptions import BizException



"""
验证码服务
1. 生成验证码
2. 验证验证码
"""
def get_random_captcha() -> str:
    """
    生成随机4位验证码
    """
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    # 替换相似的字符
    code = code.replace("O", "0").replace("I", "1").replace("L", "1")
    return code



class CaptchaService:

    CAPTCHA_EXPIRE = 60 * 5  # 验证码过期时间（秒）
    CAPTCHA_KEY_PREFIX = "captcha:"  # 验证码前缀


    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client

    async def create_captcha(self):
        """
        生成验证码
        1. 生成随机4位验证码
        2. 存储验证码到 Redis
        3. 返回验证码图片
        """
        # 生成4位验证码
        code = get_random_captcha()
        # 生成验证码图片
        image_captcha = ImageCaptcha(width=162, height=54)
        image_data = image_captcha.generate(code)
        b64 = base64.b64encode(image_data.read()).decode("utf-8")

        # 存储redis设置失效时间
        key = str(uuid.uuid4())
        await self.redis_client.set(f"{self.CAPTCHA_KEY_PREFIX}{key}", code.lower(), ex=self.CAPTCHA_EXPIRE)
        
        captcha = CaptchaRead(key=key, image=f"data:image/png;base64,{b64}")

        return captcha



    async def verify_captcha(self, data: CaptchaVerifyRequest) -> bool:
        """
        验证验证码
        1. 从 Redis 获取验证码
            如果验证码不存在，返回 False
        2. 对比验证码是否匹配
            如果不匹配，返回 False
            否则，返回 True，同时删除 Redis 中的验证码
        """
        # 从 Redis 获取验证码
        key = f"{self.CAPTCHA_KEY_PREFIX}{data.key}"
        stored_code = await self.redis_client.get(key)
        print(stored_code)
        print(data.code)

        if not stored_code:
            raise BizException(code=10001, message="验证码不存在或已过期")
        # 对比验证码是否匹配
        if stored_code.lower() != data.code.lower():    
            raise BizException(code=10002, message="验证码错误")
        else:
            # 删除 Redis 中的验证码
            await self.redis_client.delete(key)
            return True
