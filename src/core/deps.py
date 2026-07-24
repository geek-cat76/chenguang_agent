from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.infra.database import get_db
from src.core.exceptions import BizException
from src.utils.jwt_utils import verify_jwt, oauth2_scheme
from src.modules.user.model import User


class PageParams:
    """通用分页参数，通过 Depends 注入到接口中。"""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码，从1开始"),
        page_size: int = Query(10, ge=1, le=100, description="每页条数"),
        keyword: str | None = Query(None, description="搜索关键词"),
    ):
        self.page = page
        self.page_size = page_size
        self.keyword = keyword

    @property
    def offset(self) -> int:
        """计算 SQL OFFSET。"""
        return (self.page - 1) * self.page_size

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """从 JWT token 中解析当前登录用户，用于保护接口"""
    try:
        payload = verify_jwt(token)
        user_id = int(payload.get("id"))
    except Exception:
        raise BizException(code=401, message="未登录或 token 已过期")

    user = await db.get(User, user_id)
    if not user:
        raise BizException(code=401, message="用户不存在")
    if not user.is_active:
        raise BizException(code=401, message="账号已被禁用")

    return user


def require_permission(permission_code: str):
    """
    返回一个 FastAPI 依赖函数，用于校验当前用户是否拥有指定权限。

    使用方式：Depends(require_permission("user:list"))
    """
    async def _check(
        current_user: User = Depends(get_current_user),
    ) -> User:
        # 1. 超级管理员直接放行
        if current_user.is_superuser:
            return current_user

        # 2. 收集用户所有权限 code
        #    遍历 current_user.roles，再遍历每个 role.permissions
        #    收集所有 permission.code 到一个 set 中
        user_permissions = set()
        for role in current_user.roles:
            for perm in role.permissions:
                user_permissions.add(perm.code)

        # 3. 检查目标权限是否在集合中
        if permission_code not in user_permissions:
            raise BizException(code=403, message=f"无权限: {permission_code}")

        return current_user

    return _check
