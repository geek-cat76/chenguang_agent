# 晨光 Agent 平台：项目上下文与 AI 接手说明

> 本文档用于让后续 AI 或开发者快速理解并修改本项目。内容基于 **2026-07-26** 工作区的实际源码、迁移、配置、测试和 Git 状态整理，而不只是 README。
>
> 重要边界：用户已明确约定 **`app/` 目录承载全部前端代码**。2026-07-26 已在该目录建立 React 19 + TypeScript + Vite 管理控制台；后续前端修改必须继续留在 `app/`，不能散落到后端 `src/`。

---

## 1. 一分钟了解项目

- 仓库名：`chenguang_agent`
- 本地应用名：`晨光Agent平台`（来自被 `.gitignore` 忽略的 `.env`）
- 当前分支/基线：`main`，文档更新时 HEAD 为 `bc31bc0`（提交说明：`redis 缓存`）
- 许可证：Apache License 2.0
- 当前产品形态：异步 FastAPI 后端 + React 管理控制台。后端已实现用户、图形验证码、登录、JWT、角色、权限和 RBAC 权限缓存；前端已实现对应的登录、工作台、用户、角色、权限和个人信息页面。
- 当前没有任何 AI/Agent、模型调用、知识库、对话或工作流实现；项目名称中的 “Agent” 还没有对应业务代码。
- 前端使用 React 19、TypeScript、Vite、React Router、TanStack Query、Axios 和 Ant Design，依赖由 npm lockfile 固定。
- 数据层：MySQL 8.4 + SQLAlchemy 2 异步 ORM + Alembic。
- 缓存层：Redis，存验证码以及用户的角色/权限快照。
- MinIO 已在 Docker Compose 中声明，但代码尚未使用，也没有 MinIO Python SDK。
- API 总前缀为 `/api/v1`，健康检查为 `/health`，FastAPI 默认文档通常位于 `/docs`、`/redoc` 和 `/openapi.json`。
- 业务响应统一设计为 `{code, message, data}`，但 FastAPI 自身的 401/404/422 等响应目前不一定遵循该格式。

当前最重要的接手事实：

1. **绝大多数业务接口目前没有鉴权。** 只有 `GET /api/v1/users/me` 使用了 `get_current_user`；`require_permission(...)` 虽已实现，但没有挂到任何 API 上。
2. **权限缓存已进入当前基线。** 修改鉴权、事务或 RBAC 关系前仍需理解双删与提交后回调，不要破坏缓存一致性。
3. **依赖清单不完整。** 源码直接依赖 `redis`、`bcrypt`、`captcha`、`PyJWT`，但它们不在 `requirements.txt` 中。
4. **完整测试目前不能通过。** 测试收集会因当前环境缺少 `bcrypt` 中断；单独运行 JWT 测试时，一个写死的 token 已过期。
5. **JWT 密钥硬编码在源码。** 在继续做鉴权功能前，应优先迁移到环境变量并轮换密钥。

---

## 2. 项目目录与职责

```text
chenguang_agent/
├── app/                         # 全部前端代码的唯一目录；React 19 + TypeScript + Vite
│   ├── src/
│   │   ├── auth/                # 登录态上下文和当前用户查询
│   │   ├── components/          # 品牌、页面标题、受保护路由
│   │   ├── layouts/             # 后台侧栏和顶栏布局
│   │   ├── pages/               # 登录、工作台、用户、角色、权限、个人信息
│   │   ├── services/            # Axios、统一响应解析、API、Token 存储
│   │   ├── styles/              # 响应式全局样式
│   │   └── types/               # OpenAPI 对应的 TypeScript 类型
│   ├── package.json             # 前端命令与直接依赖
│   ├── package-lock.json        # npm 锁文件
│   └── vite.config.ts           # React 插件及后端开发代理
├── src/                         # FastAPI 后端源码
│   ├── main.py                  # 应用工厂、生命周期、中间件/异常/路由注册、健康检查
│   ├── core/                    # 配置、基类、通用依赖、异常、日志
│   │   ├── config.py            # Pydantic Settings 和 DATABASE_URL
│   │   ├── base_model.py        # SQLAlchemy Base、时间戳、统一主键
│   │   ├── base_schema.py       # ResponseSchema、PageResult
│   │   ├── base_repository.py   # 通用异步 CRUD、分页、模糊搜索
│   │   ├── deps.py              # 分页参数、当前用户、权限依赖
│   │   ├── exceptions.py        # BizException 与全局异常处理
│   │   └── logger.py            # Loguru 控制台/文件日志
│   ├── infra/
│   │   ├── database.py          # 异步引擎、会话依赖、提交后回调
│   │   └── redis_cache.py       # Redis 连接池和共享客户端
│   ├── middlewares/logging.py   # 请求方法、路径、状态码、耗时日志
│   ├── modules/                 # 按业务模块拆分
│   │   ├── auth/                # 验证码 + 用户名密码登录、JWT 签发
│   │   ├── captcha/             # 验证码生成、Redis 存取与校验
│   │   ├── user/                # 用户 CRUD 子集、用户-角色分配
│   │   ├── role/                # 角色 CRUD、角色-权限分配
│   │   └── permission/          # 权限 CRUD
│   └── utils/
│       ├── jwt_utils.py         # JWT 编解码与 OAuth2 Bearer 定义
│       ├── password_utils.py    # bcrypt 哈希/校验
│       └── permission_cache.py  # RBAC Redis 缓存实现
├── alembic/                     # 数据库迁移环境及版本脚本
├── docker/docker-compose.yaml   # MySQL、Redis、MinIO；不包含后端服务
├── test/                        # pytest 测试
├── logs/                        # Loguru 运行日志；仓库中已有一个历史压缩日志
├── .env                         # 本地配置，已忽略，不应提交
├── requirements.txt             # Python 固定版本依赖，但当前缺少若干直接依赖
├── pytest.ini                   # pytest 配置
├── alembic.ini                  # Alembic 配置；URL 由项目 Settings 动态注入
├── README.md                    # 目前只有极简的容器/迁移说明
└── PROJECT_CONTEXT.md           # 本文档
```

模块内部基本遵循以下分层：

```text
api.py -> service.py -> repository.py -> model.py / AsyncSession -> MySQL
                └----> PermissionCache / CaptchaService ---------> Redis
schema.py 用于 API 输入输出；main.py 负责注册各模块 router。
```

职责约定：

- `api.py`：路由、依赖注入、将 ORM 对象转为 Pydantic 输出。
- `service.py`：业务校验、跨仓储编排、缓存失效。
- `repository.py`：SQL 查询与持久化，不应塞入 HTTP 细节。
- `model.py`：SQLAlchemy 表结构及关系。
- `schema.py`：Pydantic 请求/响应模型。
- `src/core`：所有模块共享的基础设施和约定。
- `src/infra`：外部基础设施连接与事务生命周期。

---

## 3. 技术栈和依赖现状

### 3.1 核心技术

| 类别 | 当前实现 |
| --- | --- |
| 前端 | React `19.2.8`、TypeScript `7.0.2`、Vite `8.1.5`、React Router `7.18.1` |
| 前端数据/UI | TanStack Query `5.101.4`、Axios `1.18.1`、Ant Design `6.5.2` |
| Web | FastAPI `0.135.1`、Starlette `1.3.1`、Uvicorn `0.51.0` |
| 数据校验/配置 | Pydantic `2.13.4`、pydantic-settings `2.14.2`、email-validator |
| ORM/迁移 | SQLAlchemy `2.0.48`、Alembic `1.18.5`、asyncmy `0.2.11` |
| 数据库 | MySQL 8.4（Docker Compose） |
| 缓存 | Redis async client；Compose 当前使用 `redis:latest` |
| 鉴权 | OAuth2 Bearer + HS256 JWT，固定 30 分钟过期 |
| 密码 | bcrypt |
| 验证码 | `captcha.image.ImageCaptcha`，Redis TTL 5 分钟 |
| 日志 | Loguru `0.7.3` |
| 测试 | pytest、pytest-asyncio、AnyIO |
| 本地基础设施 | Docker Compose：MySQL、Redis、MinIO |

项目没有声明 Python 版本（没有 `.python-version`、`pyproject.toml` 等）。本次检查环境是 Python `3.13.2`，这只是当前机器事实，不等于项目正式兼容性承诺。

### 3.2 `requirements.txt` 的已知缺口

以下包被源码直接导入，但没有写入 `requirements.txt`：

- `redis`
- `bcrypt`
- `captcha`
- `PyJWT`（导入名为 `jwt`）

当前全局 Python 环境碰巧已有 `redis` 和 `PyJWT`，但没有 `bcrypt`；不能依赖这种机器偶然状态。新环境只执行 `pip install -r requirements.txt` 后，应用和测试大概率无法启动。

另外，`requirements.txt` 包含 Playwright、playwright-stealth 等目前未被项目源码使用的重型依赖。后续整理依赖时，应区分直接运行依赖、开发/测试依赖和暂未使用依赖，并增加锁文件或标准项目配置。

---

## 4. 配置与本地基础设施

### 4.1 Settings

`src/core/config.py` 使用 `BaseSettings` 读取根目录 `.env`，并通过 `@lru_cache` 作为进程内单例。支持的变量：

| 变量 | 用途 | 代码默认值/说明 |
| --- | --- | --- |
| `APP_NAME` | FastAPI 标题、启停日志 | `MyApp`；本地 `.env` 为“晨光Agent平台” |
| `APP_ENV` | 环境标识 | `development` |
| `APP_DEBUG` | SQLAlchemy `echo` | `True`，会打印 SQL |
| `APP_VERSION` | OpenAPI 应用版本 | `1.0.0` |
| `DB_HOST` | MySQL 主机 | `127.0.0.1` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | MySQL 用户 | `root` |
| `DB_PASSWORD` | MySQL 密码 | 代码默认空字符串 |
| `DB_NAME` | MySQL 数据库 | 代码默认 `myapp`；本地为 `chenguang` |
| `REDIS_HOST` | Redis 主机 | `localhost` |
| `REDIS_PORT` | Redis 端口 | `6379` |
| `REDIS_PASSWORD` | Redis 密码 | 代码含开发默认值 |
| `REDIS_DB` | Redis DB 编号 | `0` |
| `LOG_LEVEL` | 日志级别 | `DEBUG` |
| `LOG_DIR` | 日志目录 | `logs` |

异步数据库 URL 在运行时拼成：

```text
mysql+asyncmy://<user>:<password>@<host>:<port>/<db>?charset=utf8mb4
```

`.env` 已被 `.gitignore` 忽略。不要把真实密钥复制到文档、源码或 Git；建议补一个只含占位符的 `.env.example`。

### 4.2 Docker Compose

`docker/docker-compose.yaml` 声明：

- MySQL 8.4：主机端口 `3306`，初始化数据库名为 `chenguang`。
- Redis：主机端口 `6379`，开启密码和 AOF。
- MinIO：API `9000`，控制台 `9001`。
- 三者位于 `app-network` bridge 网络。
- Compose 中包含硬编码开发凭据，只适合本地开发。
- 没有后端容器、Dockerfile、反向代理或前端容器；FastAPI 仍需在主机单独启动。
- 数据卷相对 Compose 文件解析到 `docker/docker/...`；该数据目录已被 Git 忽略。

从仓库根目录使用的可靠命令是：

```bash
docker compose -f docker/docker-compose.yaml up -d
docker compose -f docker/docker-compose.yaml ps
docker compose -f docker/docker-compose.yaml down
```

README 中写的是 `docker compose -f docker-compose.yaml up -d`，只有先进入 `docker/` 目录才找得到该文件。

---

## 5. 应用启动、生命周期和请求事务

### 5.1 应用入口

入口是 `src/main.py`：

1. `create_app()` 从 Settings 设置应用标题和版本。
2. 注册 `LoggingMiddleware`。
3. 注册 `BizException` 和全局 `Exception` 处理器。
4. 把 user、captcha、auth、permission、role 五个 router 统一挂到 `/api/v1`。
5. lifespan 启动时初始化 Loguru，退出时 `engine.dispose()`。
6. 模块级 `app = create_app()` 供 ASGI Server 导入。
7. `/health` 定义在模块级应用上。

仓库没有明确写出后端启动命令。基于入口结构，推荐从仓库根目录使用：

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

这是根据代码推导出的标准命令，不是当前 README 已验证的完整启动流程。

### 5.2 数据库会话

`src/infra/database.py` 在模块导入时创建异步 Engine 和 `AsyncSessionLocal`：

- 连接池：`pool_size=10`、`max_overflow=20`、`pool_recycle=3600`、`pool_pre_ping=True`。
- `expire_on_commit=False`。
- `get_db()` 是 yield 依赖：路由正常结束后 commit；异常时清理提交后回调、rollback 并重新抛出。
- Repository 的 create/update/delete 只 `flush`，不自行 commit；请求级依赖统一提交。
- 当前权限缓存改动引入 `session.info["after_commit_callbacks"]`，用于数据库提交成功后再次清除缓存。

### 5.3 Redis 客户端

`src/infra/redis_cache.py` 在模块导入时创建连接池和共享客户端：

- `decode_responses=True`，正常返回字符串。
- 所有依赖注入得到同一个客户端实例，由 Redis 连接池管理连接。
- 应用 lifespan 当前没有显式关闭 Redis client/pool。

### 5.4 日志和异常

- 请求中间件记录请求方法、路径、响应状态码和毫秒耗时，不记录请求体。
- Loguru 同时输出控制台和 `logs/{日期}.log`。
- 日志每天零点轮转、保留 30 天、旧文件 gzip 压缩。
- `BizException` 被转换为 **HTTP 200**，业务错误码放在响应 JSON 的 `code` 中。
- 未处理异常返回 HTTP 500 和 `{code: 500, message: "服务器内部错误", data: null}`，完整异常写日志。
- FastAPI/Pydantic 的请求校验错误、路由错误和 OAuth2 自身错误没有自定义处理器，通常仍使用框架原生响应格式。

---

## 6. 数据模型与迁移

### 6.1 通用字段

所有继承 `BaseModel` 的表都拥有：

- `id`: `BIGINT` 自增主键
- `created_at`: 数据库 `now()` 默认值
- `updated_at`: 数据库 `now()` 默认值，ORM 更新时使用 `onupdate=func.now()`

### 6.2 表关系

```mermaid
erDiagram
    USERS ||--o{ USER_ROLES : has
    ROLES ||--o{ USER_ROLES : assigned
    ROLES ||--o{ ROLE_PERMISSIONS : has
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : assigned

    USERS {
        bigint id PK
        varchar username UK
        varchar email UK
        varchar hashed_password
        boolean is_active
        boolean is_superuser
        datetime last_login
        datetime created_at
        datetime updated_at
    }
    ROLES {
        bigint id PK
        varchar code UK
        varchar name
        varchar description NULL
        datetime created_at
        datetime updated_at
    }
    PERMISSIONS {
        bigint id PK
        varchar code UK
        varchar name
        varchar description NULL
        datetime created_at
        datetime updated_at
    }
    USER_ROLES {
        bigint user_id PK,FK
        bigint role_id PK,FK
    }
    ROLE_PERMISSIONS {
        bigint role_id PK,FK
        bigint permission_id PK,FK
    }
```

具体模型：

- `User`
  - `username`、`email` 唯一并建索引。
  - `hashed_password` 存 bcrypt 哈希。
  - `is_active` 默认 `True`。
  - `is_superuser` 默认 `False`。
  - `last_login` 可空。
  - `roles` 经 `user_roles` 多对多，`lazy="selectin"`。
- `Role`
  - `code` 唯一，作为稳定业务标识。
  - `name`、可空 `description`。
  - `permissions` 经 `role_permissions` 多对多，`lazy="selectin"`。
- `Permission`
  - `code` 唯一，例如 `user:list`。
  - `name`、可空 `description`。
- 两张中间表的外键都使用 `ON DELETE CASCADE`。

模型关系没有配置 `back_populates`，主要由 User -> Role -> Permission 单向读取。

### 6.3 Alembic 迁移链

```text
e386f16a4a4b_init
  -> c57720e069fd_users
  -> c2babde07b4e_user变更
  -> 9841da79fdd6_ubac权限系统
```

- 初始迁移为空操作。
- 第二个迁移创建 `users`。
- 第三个迁移增加 `is_superuser`、`last_login`。
- 第四个迁移创建 `roles`、`permissions`、`user_roles`、`role_permissions`。
- `alembic/env.py` 会导入三个 model 模块，并把 `Base.metadata` 交给 autogenerate。
- `alembic.ini` 中 `sqlalchemy.url` 故意为空，运行时从 Settings 注入。
- 当前没有种子数据迁移，没有默认管理员、角色或权限初始化脚本。

常用命令：

```bash
alembic current
alembic history
alembic upgrade head
alembic revision --autogenerate -m "描述"
alembic downgrade -1
```

修改模型后必须生成并人工检查迁移，不能只改 ORM。新增 model 模块时还要确保它在 `alembic/env.py` 被导入，否则 autogenerate 看不到它。

---

## 7. API 统一约定

### 7.1 成功响应

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

`data` 允许为 `null`。分页数据形状：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

通用分页查询参数：

- `page`: 默认 1，最小 1。
- `page_size`: 默认 10，范围 1 到 100。
- `keyword`: 可选模糊搜索词。
- offset 计算方式：`(page - 1) * page_size`。
- 默认按 `id DESC` 排序。

### 7.2 业务错误

业务异常示例：

```json
{
  "code": 403,
  "message": "无权限: user:list",
  "data": null
}
```

注意它的 HTTP status 仍是 200，前端必须同时检查 JSON `code`。如果后续改成标准 HTTP 状态码，需要同步修改前端拦截器、自动化测试和现有调用方。

### 7.3 鉴权头

受保护接口使用：

```http
Authorization: Bearer <access_token>
```

OAuth2 schema 的 `tokenUrl` 是 `/api/v1/auth/login`。登录接口实际接收 JSON，而不是标准 OAuth2 password form。

---

## 8. 完整 API 清单

“鉴权”列描述的是 **当前代码真实状态**，不是期望状态。

### 8.1 系统与验证码

| 方法 | 路径 | 鉴权 | 输入 | `data` 输出/说明 |
| --- | --- | --- | --- | --- |
| GET | `/health` | 无 | 无 | 原始 `{"status":"ok"}`，不使用统一响应包装 |
| GET | `/api/v1/captcha` | 无 | 无 | `{key, image}`；image 是 PNG 的 data URL |
| POST | `/api/v1/captcha` | 无 | `{key, code}` | `true`；成功后删除 Redis 中的验证码 |

验证码行为：

- 随机生成 4 位大写字母/数字，并将 O/I/L 替换为 0/1/1。
- Redis key：`captcha:<uuid>`，TTL 300 秒，值按小写存储。
- 比较时不区分大小写。
- 验证码不存在/过期为业务码 `10001`，错误为 `10002`。
- 错误验证码不会被删除；成功验证码只可使用一次。
- 当前 service 中残留 `print(stored_code)` 和 `print(data.code)`，会把验证码输出到控制台，应删除。

### 8.2 登录

| 方法 | 路径 | 鉴权 | 输入 | `data` 输出 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | 无 | `{username, password, captcha_key, captcha_code}` | `{access_token, token_type:"bearer"}` |

登录顺序：

1. 校验并消费验证码。
2. 按 username 查询用户。
3. bcrypt 校验密码。
4. 检查 `is_active`。
5. 签发 30 分钟 JWT。
6. 更新 `last_login`，由请求结束时统一 commit。

因此，即使用户名或密码错误，验证码也已经消费，下一次登录需要重新获取验证码。

JWT payload 当前包含 `id`、`username`、`is_superuser`、`exp`、`iat`。后续鉴权实际只信任 token 中的 `id` 来重新查询用户状态和数据库中的 `is_superuser`。

### 8.3 用户

| 方法 | 路径 | 鉴权 | 输入 | `data` 输出/说明 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/users` | **无** | `{username, email, password}` | `UserRead` |
| GET | `/api/v1/users/me` | Bearer | 无 | 当前用户 `UserRead` |
| GET | `/api/v1/users/{user_id}` | **无** | 路径 ID | `UserRead` |
| GET | `/api/v1/users` | **无** | `page,page_size,keyword` | `PageResult<UserRead>`，搜索 username/email |
| PUT | `/api/v1/users/{user_id}/roles` | **无** | **原始 JSON 数组**，如 `[1,2]` | `UserRead`；整体替换用户角色 |
| GET | `/api/v1/users/{user_id}/roles` | **无** | 路径 ID | 当前实现返回一个元素的数组 `[UserWithRolesRead]` |

`UserRead` 字段：`id, username, email, is_active`。不会输出密码、超级管理员标记、最后登录时间和时间戳。

特别注意：

- `UserAssignRoles {role_ids: [...]}` schema 已定义但未使用；实际 PUT 请求体必须是数组，不是 `{role_ids:[...]}`。
- `GET .../roles` 的 response model 是列表，但语义上只查一个用户；返回形状不自然。
- 用户创建和所有用户/角色管理接口目前公开，存在严重越权风险。
- 没有用户更新、禁用、删除、改密、忘记密码等 API。

### 8.4 权限

| 方法 | 路径 | 鉴权 | 输入 | `data` 输出/说明 |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/permissions/{permission_id}` | **无** | 路径 ID | `PermissionRead` |
| GET | `/api/v1/permissions/` | **无** | `page,page_size,keyword` | 分页；搜索 code/name |
| POST | `/api/v1/permissions/` | **无** | `{code,name,description?}` | `PermissionRead` |
| PUT | `/api/v1/permissions/{permission_id}` | **无** | `{name?,description?}` | `PermissionRead`；code 不可修改 |
| DELETE | `/api/v1/permissions/{permission_id}` | **无** | 路径 ID | `null` |

权限的列表和创建路由显式带尾斜杠。调用无尾斜杠路径时可能触发 FastAPI/Starlette 自动重定向。

### 8.5 角色

| 方法 | 路径 | 鉴权 | 输入 | `data` 输出/说明 |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/roles` | **无** | `{code,name,description?}` | `RoleRead` |
| GET | `/api/v1/roles/{role_id}` | **无** | 路径 ID | `RoleRead`，含 permissions |
| GET | `/api/v1/roles` | **无** | `page,page_size,keyword` | 分页；搜索 code/name |
| PUT | `/api/v1/roles/{role_id}` | **无** | `{name?,description?}` | `RoleRead`；code 不可修改 |
| DELETE | `/api/v1/roles/{role_id}` | **无** | 路径 ID | `null` |
| PUT | `/api/v1/roles/{role_id}/permissions` | **无** | `{permission_ids:[1,2]}` | `RoleRead`；整体替换角色权限 |

`RoleRead` 内嵌 `permissions: PermissionRead[]`。

---

## 9. 用户认证与 RBAC 权限链路

### 9.1 当前用户解析

`get_current_user` 位于 `src/core/deps.py`：

1. 从 OAuth2 Bearer 读取 token。
2. `verify_jwt` 解码，并把 payload `id` 转为整数。
3. 查询 Redis 权限缓存。
4. 无论缓存是否命中，都从 MySQL 读取用户行，用于确认用户存在且启用。
5. 缓存命中时对 `User.roles` 使用 `raiseload`，避免默认 `selectin` 加载整张 RBAC 关系图。
6. 缓存未命中时读取 `user.roles -> role.permissions`，构建角色和权限 code 集合并写入 Redis。
7. 把本次请求的权限快照暂挂到 User 对象 `_rbac_permission_codes`，供后续权限依赖复用。

异常映射：token 错误/过期、用户不存在、用户被禁用均抛业务码 401。

### 9.2 权限检查

预期用法：

```python
@router.get("/example")
async def example(
    current_user: User = Depends(require_permission("example:read")),
):
    ...
```

`require_permission(code)` 行为：

1. `is_superuser=True` 直接放行。
2. 优先复用本请求 User 对象上的权限快照。
3. 若无快照，查 Redis；仍未命中则从 ORM 关系重建权限与角色缓存。
4. code 不在集合中时抛业务码 403。

**当前没有任何路由实际调用 `require_permission`。** RBAC 数据结构和检查器已存在，但 API 授权层尚未接线。

### 9.3 Redis 权限缓存

`src/utils/permission_cache.py` 是当前工作区新增、尚未提交的实现：

| 内容 | Redis key | 值 | TTL |
| --- | --- | --- | --- |
| 用户权限 codes | `user:perms:<user_id>` | 排序后的 JSON 字符串数组 | 1800 秒 |
| 用户角色 codes | `user:roles:<user_id>` | 排序后的 JSON 字符串数组 | 1800 秒 |

关键语义：

- `None` 表示缓存未命中或数据损坏。
- 空集合会存为 `[]`，是有效命中；不能用 truthy/falsy 判断命中。
- 权限和角色通过 Redis transaction pipeline 原子写入，并使用相同 TTL。
- 角色 codes 当前只写入缓存，尚无业务逻辑读取它们做授权。

### 9.4 缓存失效

以下变更会清除受影响用户的两个 key：

- 给用户整体替换角色。
- 给角色整体替换权限。
- 删除角色。
- 删除权限。

为缩小数据库提交与缓存并发回填之间的竞态，当前实现采取“双删”：

1. ORM `flush` 后、数据库 commit 前先删一次缓存；此时 Redis 失败会让请求异常并导致数据库回滚。
2. 在 session 上注册提交后回调。
3. 数据库成功 commit 后再删一次，以清除提交窗口中可能被并发请求回填的旧快照。

删除角色/权限前必须先查受影响的 user IDs，因为中间表行会随删除级联消失。

维护这一机制时必须保持的约束：

- 所有改变 User-Role 或 Role-Permission 关系的代码路径都要失效缓存。
- 权限 code 当前不可更新；若将来允许修改 code，也必须批量失效受影响用户。
- commit 失败时必须清除 session 中待执行回调，不能误删并假装变更已提交。
- 提交后 Redis 删除失败发生在数据库已提交之后，无法再回滚数据库；未来应考虑日志、重试、outbox 或版本化缓存。

---

## 10. 各业务模块实现细节

### 10.1 User

- 创建用户前分别检查 username、email 唯一性。
- 密码使用 bcrypt 哈希后存储。
- 用户列表使用通用 `get_page`，username/email 做 `%keyword%` 模糊查询。
- 分配角色时先批量查询所有 role IDs，数量不一致即报“角色不存在”，随后整体替换 `user.roles`。
- `User.roles` 为 `selectin`，普通用户列表即使输出不需要 roles，也可能额外加载关系，后续可按查询场景优化。

### 10.2 Role

- code 创建后不可更新。
- 创建时检查 code 唯一。
- 角色详情/列表输出嵌套 permissions。
- 分配权限为整体替换，不是增量追加。
- 删除角色通过 Core Repository 的 SQL DELETE；当前不会先验证角色是否存在，不存在也会返回成功。

### 10.3 Permission

- code 创建后不可更新，缓存因此能把 code 作为稳定授权标识。
- 创建时检查 code 唯一。
- name/description 可更新。
- 删除前加载实体并查找经角色关联的所有用户，用于缓存失效。

### 10.4 Repository

`BaseRepository` 提供：

- `get_by_id`
- `get_all`
- `get_page`
- `create`
- `update`
- `delete`
- `delete_by_id`

`get_page`：

- 对声明的搜索字段拼 `OR column LIKE '%keyword%'`。
- 使用子查询 count 获取总数。
- 结果按 `id DESC`。
- 没有通用过滤、排序字段、游标分页、软删除或租户隔离。

---

## 11. 前端 `app/` 的真实状态与接入约束

### 11.1 当前状态

- `app/` 已建立独立 npm 工程，要求 Node.js `^20.19.0` 或 `>=22.12.0`。
- 页面：`/login`、`/dashboard`、`/users`、`/roles`、`/permissions`、`/profile`，以及 404 页面。
- `AuthProvider` 管理 access token 与当前用户；受保护路由无 token 时跳转登录页。
- token 当前写入 `localStorage` 的 `chenguang_access_token`，Axios 请求拦截器自动添加 Bearer 头。该方案适配现有纯 Header 后端，但需承担 XSS 读取风险；若后端以后支持 HttpOnly Cookie，应重新评估。
- TanStack Query 管理分页列表、详情、选项和 mutation 后缓存失效。
- `services/http.ts` 同时处理 HTTP 错误和 `{code,message,data}` 业务错误；业务 code 401 会清除本地 token。
- 登录失败后刷新验证码，因为后端会先消费验证码再校验用户名和密码。
- Vite 开发服务器运行于 `5173`，把 `/api` 和 `/health` 代理到 `VITE_API_PROXY_TARGET`（默认 `http://localhost:8000`），开发阶段不依赖 CORS。
- 生产构建输出到 `app/dist/`，当前仓库尚未提供 Nginx、静态文件托管或前端容器配置。

### 11.2 API 映射中的特殊约束

1. 用户分配角色必须发送原始数组 `[1,2]`，不能包装为对象。
2. 角色分配权限必须发送 `{permission_ids:[1,2]}`。
3. 权限列表/创建使用 `/api/v1/permissions/` 尾斜杠，避免重定向。
4. `/health` 是原始 JSON，不使用统一响应包装，因此由 `requestRaw` 处理。
5. Dashboard 为展示统计会分别请求用户、角色、权限列表的第一页并读取 `total`。
6. 页面上的管理入口不等于授权；后端仍必须把管理接口接入 `require_permission`。

### 11.3 前端目录职责

- `src/pages`：路由级页面与页面内业务交互。
- `src/services/api.ts`：按 OpenAPI 声明接口调用，不在页面重复拼 URL。
- `src/services/http.ts`：统一响应、错误和认证头处理。
- `src/types/api.ts`：与 OpenAPI schema 对应的明确类型。
- `src/auth`：登录态、当前用户查询和退出。
- `src/layouts` / `src/components`：后台壳、路由守卫和可复用展示组件。
- `src/styles/global.css`：当前视觉系统和响应式规则。

---

## 12. 本地开发建议流程

当前仓库缺少一键启动脚本。以下是根据源码整理的建议流程：

```bash
# 1. 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate

# 2. 安装仓库声明依赖
python -m pip install -r requirements.txt

# 3. 在 requirements 修复前，还需补直接依赖
python -m pip install redis bcrypt captcha PyJWT

# 4. 准备根目录 .env，数据库/Redis凭据需和 Compose 对齐

# 5. 启动基础设施
docker compose -f docker/docker-compose.yaml up -d

# 6. 执行迁移
alembic upgrade head

# 7. 启动 API
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

然后可访问：

- 健康检查：`http://localhost:8000/health`
- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`
- 前端：`http://localhost:5173`

前端在另一个终端启动：

```bash
cd app
npm ci
npm run dev
```

`npm ci` 只需在首次拉取或 lockfile 变化后执行。当前基础组件已经全部记录在 `package.json` / `package-lock.json`，日常启动不需要重复安装。

项目当前没有创建首个超级管理员、角色、权限的命令。需要通过公开 API 或直接数据库操作初始化；这本身也是应补齐的安全/运维能力。

---

## 13. 测试与本次验证结果

pytest 配置：

- 测试目录：`test/`
- `pythonpath = .`
- verbose、short traceback、strict markers、CLI INFO 日志。
- 声明 `slow` 和 `integration` marker。

测试文件：

- `test/test_sample.py`：两个简单加法测试；名为 `test_add_fail` 的测试实际断言正确，会通过。
- `test/test_jwt.py`：动态 token 往返测试，以及一个写死 token 的测试。
- `test/test_permission_cache.py`：12 个异步测试，覆盖双 key 写入、空集合命中、批量失效、请求快照、cache hit/miss、提交后回调，以及用户/角色/权限变更时的双删顺序。

2026-07-26 实际验证：

1. `python -m compileall -q src test alembic`：**通过**，说明 Python 语法可编译。
2. `python -m pytest -q`：**测试收集失败**，`src/utils/password_utils.py` 导入 `bcrypt` 时环境报 `ModuleNotFoundError`。
3. 单独运行 `test_sample.py` 与 `test_jwt.py`：**3 passed, 1 failed**。
4. 失败项是 `test_token`，原因是写死 JWT 已过期，不是动态签发逻辑失败。

在修复依赖清单后，应重新执行完整测试。不要通过关闭 token 过期校验来让硬编码测试通过；应改为测试内动态生成 token，或使用可控时钟。

2026-07-26 新增前端后的验证：

1. `cd app && npm run typecheck`：**通过**。
2. `cd app && npm run build`：**通过**，Vite 生成可部署的 `dist/`。
3. 本地浏览器检查登录页：桌面布局、表单和后端不可用异常态正常，浏览器控制台无前端错误。
4. 构建提示主 JS chunk 大于 500 kB；这是 Ant Design 与页面当前同步打包造成的性能提示，不影响正确性，后续可用路由懒加载和更细粒度拆包优化。

---

## 14. 当前 Git 工作区：不要覆盖的未提交改动

2026-07-26 本次前端交付结束前观察到：

- 分支 `main`，HEAD `bc31bc0`（`redis 缓存`）。权限缓存与相关测试已经进入当前 Git 基线。
- `app/` 是本次新增、尚未提交的完整前端工程。
- `docs/openapi.json` 是用户提供、尚未提交的 API 契约，本次没有修改。
- `PROJECT_CONTEXT.md` 因本次前端状态更新而有修改。
- 本次没有修改后端业务源码。

后续 AI 必须重新执行 `git status --short`，以当时工作区为准；不要覆盖 `app/` 或用户后续产生的其他未提交改动。

---

## 15. 已知问题与技术债（按优先级）

### P0：安全与可运行性

1. **管理接口未鉴权**：用户列表/详情/分配角色、角色和权限 CRUD 全部公开；RBAC 检查器没有接到路由。
2. **JWT `SECRET_KEY` 硬编码并已提交**：应改为必填环境变量，轮换现有密钥，必要时让旧 token 失效。
3. **依赖清单缺包**：`redis`、`bcrypt`、`captcha`、`PyJWT` 未声明，新环境不可复现。
4. **完整测试不可运行**：缺 bcrypt 导致收集失败；固定 JWT 测试必然随时间过期。
5. **开发凭据硬编码在 Compose/配置默认值中**：不得沿用到生产。
6. **没有初始化管理员的安全流程**：首次部署无法以受控方式引导 RBAC 数据。

### P1：API 契约和业务正确性

1. `RoleService` 多处错误地调用 `BizException(f"...")`。构造函数第一个位置参数是 `code`，结果会把字符串放入 code，message 仍是“业务异常”；应改成具名参数。
2. 只有 `/users/me` 鉴权，权限缓存的主要能力在真实 API 流量中几乎没有生效。
3. `GET /users/{id}/roles` 返回一个元素的用户数组，不是角色数组或单个用户对象。
4. `PUT /users/{id}/roles` 接受原始数组，而已定义的 `UserAssignRoles` schema 没有使用。
5. BizException 总是 HTTP 200，而校验错误等又使用框架原生状态/格式，客户端错误处理不统一。
6. `RoleUpdate` 使用 `data.name or old`、`data.description or old`，无法把 description 主动清空。
7. 角色/权限 ID 批量校验用“查询数量 == 输入数量”；输入含重复 ID 时会被误判为无效。
8. 删除不存在的角色当前静默成功；其他资源多会返回 404，语义不一致。
9. 验证码 service 会 `print` 正确码和用户输入，存在日志泄漏。
10. 没有登录限流、验证码错误次数限制、账号锁定、refresh token、logout/revocation。
11. 用户注册没有密码强度/长度限制，也没有 username 规则。

### P2：架构、性能与运维

1. `User.roles` 和 `Role.permissions` 默认 `selectin`，某些列表接口会加载输出并不需要的关系。
2. Redis 角色 key 已写入但当前没有读取用途。
3. lifespan 没有显式关闭 Redis pool。
4. 提交后缓存删除失败时数据库已经提交，当前没有重试或恢复机制。
5. Pydantic list 字段使用 `=[]`，建议改为 `Field(default_factory=list)` 明确避免共享可变默认值。
6. 没有 CORS、生产配置、后端 Dockerfile、CI、格式化/lint/type-check 配置或覆盖率门槛。
7. 没有 `.env.example`、依赖锁文件和明确 Python 版本。
8. MinIO、Playwright 相关能力已配置/安装但没有业务使用，增加维护成本。
9. README 太短，且 Compose 命令路径容易误用。
10. `src/main.py` 有未使用的 `asyncio` 导入，代码中还存在重复 import、格式不统一和教学式注释。
11. 没有审计日志、操作人记录、软删除、租户隔离。
12. 没有 API 集成测试；当前权限缓存测试主要依靠 fake DB/Redis。
13. 前端 access token 当前位于 `localStorage`，存在 XSS 读取风险；迁移到 HttpOnly Cookie 需要后端同步设计 CSRF 防护。
14. 前端生产构建主 chunk 当前较大，应在页面继续扩展前引入路由级懒加载和拆包策略。
15. 前端尚无单元测试、端到端测试、lint 和 CI；当前只验证了 TypeScript、生产构建与登录页浏览器冒烟。

---

## 16. 后续修改指南

### 16.1 新增一个后端业务模块

建议按现有约定新增：

```text
src/modules/<module>/
├── __init__.py
├── model.py
├── schema.py
├── repository.py
├── service.py
└── api.py
```

然后：

1. 在 `src/main.py` import 并 `include_router(..., prefix="/api/v1")`。
2. 若有新 ORM model，在 `alembic/env.py` 导入对应模块。
3. 生成并检查 Alembic migration。
4. 增加 service/repository 单测和 API 集成测试。
5. 明确接口是否需要 `get_current_user` 或 `require_permission(code)`。
6. 若变更影响用户最终权限集合，接入缓存失效逻辑。

### 16.2 新增或修改数据库字段

1. 修改 SQLAlchemy model 的类型、nullable、default、index 等。
2. 同步修改输入/输出 schema。
3. 检查 repository 查询和 service 业务。
4. `alembic revision --autogenerate -m "..."`。
5. 人工审查 upgrade/downgrade，尤其是非空列、唯一索引和现有数据回填。
6. 本地 `alembic upgrade head` 后跑测试。

不要用 `Base.metadata.create_all()` 代替迁移；当前项目明确以 Alembic 管理结构。

### 16.3 给接口接入 RBAC

1. 先定义稳定、可读的 permission code，例如 `user:list`、`user:assign-role`。
2. 通过初始化脚本或管理流程创建权限并分配给角色。
3. 在路由使用 `Depends(require_permission("..."))`。
4. 超级管理员会自动放行。
5. 为允许、拒绝、超级管理员、用户禁用、缓存 hit/miss 写 API 或依赖测试。
6. 不要只在前端做菜单/按钮隐藏；后端依赖才是安全边界。

### 16.4 修改 RBAC 关系或缓存

以下不变量必须保留：

- 空权限集是有效缓存命中。
- 角色和权限两个 key 要一起写、一起删。
- 删除角色/权限前收集受影响用户。
- 数据库关系变更成功后必须失效受影响用户缓存。
- 并发一致性策略变更要配套扩充 `test_permission_cache.py`。
- 不要在 Repository 内偷偷 commit，否则会破坏请求级事务和提交后回调时序。

### 16.5 修改前端

1. 所有前端文件继续保留在 `app/`，先阅读 `app/README.md` 和相关 page/service。
2. 新接口先在 `src/types/api.ts` 定义类型，再集中加入 `src/services/api.ts`；不要在页面散落 Axios 调用。
3. 所有统一包装接口使用 `request<T>`，只有 `/health` 这类原始响应才使用 `requestRaw<T>`。
4. mutation 成功后按资源前缀失效 TanStack Query 缓存，确保列表、统计和关联选择同步更新。
5. 新页面需要放到受保护路由和 `AppLayout` 导航中，并同时检查窄屏布局。
6. 后端 OpenAPI 变化时同步更新类型、表单、请求形状和本文档；不能只修 UI。
7. 不要在前端复制后端 JWT secret、数据库/Redis 凭据或真实用户密码。

### 16.6 修改配置或依赖

- 新配置加到 `Settings`，同步补 `.env.example`，不要提交真实 `.env`。
- JWT secret 等安全配置应在非开发环境缺失时直接拒绝启动，而不是静默使用弱默认值。
- 直接 import 的第三方包必须进入依赖清单。
- 优先补正式项目元数据和锁文件，再清理未使用依赖。

---

## 17. AI 接手检查清单

每次开始修改前：

1. 阅读本文档，但以当前源码和 `git diff` 为最终事实。
2. 运行 `git status --short`，保护用户未提交改动。
3. 牢记 `app/` 是全部前端范围；当前已有 React/Vite 工程，不要重复初始化或换技术栈。
4. 判断任务属于 API、service、repository、model/schema、基础设施还是前端，不要跨层堆逻辑。
5. 若涉及鉴权，先核对接口当前是否真的挂了依赖。
6. 若涉及 User-Role-Permission 关系，检查 Redis 双 key 失效和事务时序。
7. 若涉及表结构，必须有 Alembic migration。
8. 若涉及 API 契约，核对统一业务 code 与实际 HTTP status 的双重语义。
9. 完成代码后至少执行相关 pytest；依赖问题解决后再运行全套 `python -m pytest -q`。
10. 对高风险改动补跨模块验证，尤其是登录、权限绕过、缓存一致性和迁移回滚。

每次交付时应说明：

- 修改了哪些文件和行为。
- 是否改变 API 请求/响应、数据表或环境变量。
- 是否新增/改变 permission code。
- 跑了哪些测试，结果如何。
- 是否仍有环境依赖或未解决风险。

---

## 18. 推荐的近期治理顺序

如果后续任务没有另行指定，建议按以下顺序收敛项目：

1. 修复 `requirements.txt`，补齐直接依赖和 Python 版本，恢复可复现安装。
2. 修复测试：删除固定过期 token，确保权限缓存测试完整运行。
3. 把 JWT secret 移到环境变量并轮换；删除验证码调试输出。
4. 设计权限 code 清单，把所有管理接口接入 `require_permission`。
5. 增加安全的首个管理员/RBAC 初始化流程。
6. 统一错误状态和响应契约，修复角色异常构造、用户角色 API 形状。
7. 增加 API 集成测试，覆盖 MySQL/Redis 事务与权限绕过。
8. 让现有 `app/` 与加固后的鉴权接口完成真实联调，并增加前端单测、端到端测试、路由懒加载和生产部署配置。
9. 最后清理未使用的 MinIO/Playwright 依赖，或在真实业务出现时正式接入。

这份顺序不是业务需求；它是基于当前代码安全性、可运行性和后续修改成本给出的工程建议。
