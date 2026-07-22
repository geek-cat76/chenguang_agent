from pydantic import BaseModel


class CaptchaRead(BaseModel):
    key: str
    image: str  # data:image/png;base64,...

class CaptchaVerifyRequest(BaseModel):
    key: str
    code: str
