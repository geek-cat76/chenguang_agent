from src.core.base_model import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped



class User(BaseModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(255), unique=True, index=True,comment="用户名")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True,comment="邮箱")
    hashed_password: Mapped[str] = mapped_column(String(255), comment="哈希密码")
    is_active: Mapped[bool] = mapped_column(default=True, comment="是否启用")


