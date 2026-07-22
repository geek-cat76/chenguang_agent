from pydantic import BaseModel,EmailStr


#  用户注册请求
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool

    # from_attributes 从数据库模型中读取属性
    model_config = {"from_attributes": True}