# 晨光 Agent 平台前端

全部前端代码位于本目录。当前工程根据 `docs/openapi.json` 实现后台管理控制台。

## 技术栈

- React 19 + TypeScript
- Vite
- React Router
- TanStack Query
- Axios
- Ant Design

## 安装与启动

环境要求：Node.js `^20.19.0` 或 `>=22.12.0`。

首次拉取项目后执行：

```bash
cd app
npm ci
npm run dev
```

浏览器访问 `http://localhost:5173`。Vite 默认把 `/api` 和 `/health` 代理到 `http://localhost:8000`，因此还需要在仓库根目录启动 FastAPI：

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

不需要再手动安装基础组件，所有依赖已经写入 `package.json` 和 `package-lock.json`。只有在依赖清单变化时才使用 `npm install <package>`。

## 常用命令

```bash
npm run dev        # 启动开发服务器
npm run typecheck  # TypeScript 类型检查
npm run build      # 类型检查并生成生产构建到 dist/
npm run preview    # 本地预览生产构建
```

如果后端不是 `http://localhost:8000`，复制 `.env.example` 为 `.env.local` 并修改：

```dotenv
VITE_API_PROXY_TARGET=http://你的后端地址
```

生产环境前后端不同域时，可设置 `VITE_API_BASE_URL`；同域反向代理部署时保持为空。

## 页面与路由

| 路由 | 页面 | 主要接口 |
| --- | --- | --- |
| `/login` | 登录 | 验证码、登录 |
| `/dashboard` | 工作台 | 健康检查、用户/角色/权限统计 |
| `/users` | 用户管理 | 列表、创建、分配角色 |
| `/roles` | 角色管理 | 列表、创建、编辑、删除、分配权限 |
| `/permissions` | 权限管理 | 列表、创建、编辑、删除 |
| `/profile` | 个人信息 | 当前用户 |

## 目录结构

```text
src/
├── auth/          # 登录态上下文
├── components/    # 通用组件与路由守卫
├── layouts/       # 后台整体布局
├── pages/         # 页面
├── services/      # API、Axios、Token 存储
├── styles/        # 全局样式
└── types/         # OpenAPI 对应 TypeScript 类型
```

## 接口注意事项

- 后端业务异常可能仍返回 HTTP 200，`services/http.ts` 会继续检查响应 JSON 的 `code`。
- Token 当前保存在 `localStorage`，请求时自动添加 `Authorization: Bearer ...`。
- 登录失败后必须刷新验证码，因为后端会先消费验证码再校验账户。
- 用户分配角色接口请求体是原始数组；角色分配权限接口请求体是对象，两者不能混用。
- 前端的菜单和按钮不是安全边界；后端管理接口仍需接入 `require_permission`。
