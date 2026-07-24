# chenguang_agent


## 本地测试

### 启动容器
    `docker compose -f docker-compose.yaml up -d`
### 数据库维护
4. 常用命令
命令	说明

| 命令 | 说明 |
| --- | --- |
| `alembic revision --autogenerate -m "描述"` | 根据模型变更自动生成迁移脚本 |
| `alembic upgrade head` | 升级到最新版本 |
| `alembic downgrade -1` | 回退一个版本 |
| `alembic current` | 查看当前数据库版本 |
| `alembic history` | 查看迁移历史 |
