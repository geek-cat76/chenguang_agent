from src.core.base_model import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped
from src.modules.role.model import Role,user_roles
import datetime



class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), unique=True, index=True,comment="用户名")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True,comment="邮箱")
    hashed_password: Mapped[str] = mapped_column(String(255), comment="哈希密码")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")
     
    is_superuser: Mapped[bool] = mapped_column(default=False, comment="是否为超级管理员")
    last_login: Mapped[datetime.datetime | None] = mapped_column(comment="最后登录时间")

    roles: Mapped[list[Role]] = mapped_column(secondary=user_roles,lazy="selectin")


