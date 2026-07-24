from src.modules.role.schema import RoleRead
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


class UserWithRolesRead(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    roles: list[RoleRead] = []     # 从 role 模块导入 RoleRead
    model_config = {"from_attributes": True}

class UserAssignRoles(BaseModel):
    role_ids: list[int]