# AI Store Copilot — 部署文档

## 目录

1. [环境要求](#环境要求)
2. [快速启动（开发环境）](#快速启动开发环境)
3. [生产部署](#生产部署)
4. [环境变量配置](#环境变量配置)
5. [数据库迁移](#数据库迁移)
6. [企业微信配置](#企业微信配置)
7. [AI 模型配置](#ai-模型配置)
8. [故障排查](#故障排查)

---

## 环境要求

| 组件       | 版本要求    | 说明                     |
| ---------- | ----------- | ------------------------ |
| Docker     | 24.0+       | 容器运行时               |
| Docker Compose | 2.20+   | 容器编排                 |
| PostgreSQL | 16+ (自带)  | 主数据库（含 pgvector）  |
| Redis      | 7+ (自带)   | 缓存                     |
| Node.js    | 22+         | 前端构建（生产环境需要） |

---

## 快速启动（开发环境）

### 1. 克隆项目

```bash
git clone <repo-url> "e:\AI客服（"
cd "e:\AI客服（"
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入必要的配置（详见 [环境变量配置](#环境变量配置)）。

### 3. 启动所有服务

```bash
docker compose -f docker/docker-compose.yml up -d
```

此命令将启动：

| 服务       | 端口 | 说明                |
| ---------- | ---- | ------------------- |
| backend    | 8000 | FastAPI 后端        |
| db         | 5432 | PostgreSQL + pgvector |
| redis      | 6379 | Redis 缓存          |
| frontend   | 3000 | Next.js 前端        |

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8000/api/health
# 预期输出: {"status":"ok","version":"0.1.0"}

# API 文档
# 浏览器访问: http://localhost:8000/api/docs

# 前端
# 浏览器访问: http://localhost:3000
```

### 5. 查看日志

```bash
docker compose -f docker/docker-compose.yml logs -f backend
```

---

## 生产部署

### 1. 构建生产镜像

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml build
```

### 2. 启动生产环境

```bash
docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

### 3. Nginx 配置

生产环境使用 Nginx 作为反向代理，配置位于 `docker/nginx/nginx.conf`。

默认配置：

```nginx
server {
    listen 80;
    server_name _;

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
    }
}
```

### 4. SSL 配置（推荐）

将 SSL 证书放置在 `docker/nginx/ssl/` 目录：

```
docker/nginx/ssl/
├── fullchain.pem
└── privkey.pem
```

修改 `docker/nginx/nginx.conf` 添加 SSL：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    location /api/ {
        proxy_pass http://backend:8000;
    }

    location / {
        proxy_pass http://frontend:3000;
    }
}
```

### 5. 数据库备份

```bash
# 备份
docker compose exec db pg_dump -U postgres ai_store_copilot > backup_$(date +%Y%m%d).sql

# 恢复
cat backup.sql | docker compose exec -T db psql -U postgres ai_store_copilot
```

---

## 环境变量配置

### 核心配置

| 变量名                 | 必需 | 默认值            | 说明                         |
| ---------------------- | ---- | ----------------- | ---------------------------- |
| `DEBUG`                | 否   | `true`            | 调试模式（生产环境设为 false）|
| `SECRET_KEY`           | 是   | —                 | 应用密钥（生产环境必须修改） |
| `LOG_LEVEL`            | 否   | `INFO`            | 日志级别                     |

### 数据库

| 变量名                     | 必需 | 默认值                                              |
| -------------------------- | ---- | --------------------------------------------------- |
| `DATABASE_URL`             | 是   | `postgresql+asyncpg://postgres:postgres@db:5432/ai_store_copilot` |
| `DATABASE_SYNC_URL`        | 是   | `postgresql://postgres:postgres@db:5432/ai_store_copilot` |

### Redis

| 变量名      | 必需 | 默认值                     |
| ----------- | ---- | -------------------------- |
| `REDIS_URL` | 否   | `redis://redis:6379/0`     |

### AI 模型（DeepSeek）

| 变量名              | 必需 | 默认值                    | 说明                    |
| ------------------- | ---- | ------------------------- | ----------------------- |
| `AI_PROVIDER`       | 是   | `deepseek`                | 供应商：deepseek 或 openai_compatible |
| `AI_API_KEY`        | 是   | —                         | API 密钥                |
| `AI_BASE_URL`       | 是   | `https://api.deepseek.com` | API 地址               |
| `AI_MODEL`          | 否   | `deepseek-chat`           | 对话模型名称            |
| `AI_EMBED_MODEL`    | 否   | `deepseek-embedding`      | Embedding 模型名称      |

### 企业微信

| 变量名                     | 必需 | 说明                          |
| -------------------------- | ---- | ----------------------------- |
| `WECOM_CORP_ID`            | 是   | 企业微信企业 ID               |
| `WECOM_AGENT_ID`           | 是   | 应用 Agent ID                 |
| `WECOM_SECRET`             | 是   | 应用 Secret                   |
| `WECOM_TOKEN`              | 是   | 回调 URL 验证 Token           |
| `WECOM_ENCODING_AES_KEY`   | 是   | 回调消息 AES 密钥             |
| `WECOM_WEBHOOK_URL`        | 否   | 群机器人 Webhook URL（通知用）|

### JWT

| 变量名                           | 必需 | 默认值 | 说明                  |
| -------------------------------- | ---- | ------ | --------------------- |
| `JWT_SECRET_KEY`                 | 是   | —      | JWT 签名密钥（生产必须修改）|
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`| 否   | 120    | Access Token 过期时间  |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS`  | 否   | 7      | Refresh Token 过期时间 |

### 完整示例

```bash
# App
APP_NAME=AI Store Copilot
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ai_store_copilot
DATABASE_SYNC_URL=postgresql://postgres:postgres@db:5432/ai_store_copilot

# Redis
REDIS_URL=redis://redis:6379/0

# AI - DeepSeek
AI_PROVIDER=deepseek
AI_API_KEY=sk-your-deepseek-api-key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat
AI_EMBED_MODEL=deepseek-embedding

# WeCom
WECOM_CORP_ID=ww123456789
WECOM_AGENT_ID=1000001
WECOM_SECRET=your-agent-secret
WECOM_TOKEN=your-callback-token
WECOM_ENCODING_AES_KEY=your-aes-key
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging
LOG_LEVEL=INFO
```

---

## 数据库迁移

### 首次初始化

数据库表和扩展会在容器首次启动时自动创建：

1. **pgvector 扩展** — 通过 `backend/alembic/init.sql` 自动执行
2. **自动迁移** — 通过 Docker entrypoint 执行 Alembic

### 手动执行迁移

```bash
# 进入 backend 容器
docker compose exec backend bash

# 生成新迁移文件
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 查看迁移状态

```bash
docker compose exec backend alembic current
docker compose exec backend alembic history
```

---

## 企业微信配置

### 自建应用配置

1. 登录[企业微信管理后台](https://work.weixin.qq.com/)
2. **应用管理 → 自建 → 创建应用**
3. 填写应用信息，获取：
   - AgentId
   - Secret
4. **功能 → 接收消息 → 设置回调 URL**
   - URL: `http://your-domain/api/v1/wecom/callback`
   - Token: 与 `WECOM_TOKEN` 一致
   - EncodingAESKey: 随机生成，与 `WECOM_ENCODING_AES_KEY` 一致
5. 将以上信息填入 `.env` 文件

### 群机器人配置（可选，用于通知推送）

1. 在目标企业微信群添加机器人
2. 复制 Webhook URL
3. 填入 `WECOM_WEBHOOK_URL`

---

## AI 模型配置

### DeepSeek（默认）

1. 注册 [DeepSeek 平台](https://platform.deepseek.com/)
2. 创建 API Key
3. 填入 `.env`：
   ```
   AI_PROVIDER=deepseek
   AI_API_KEY=sk-your-key
   AI_BASE_URL=https://api.deepseek.com
   AI_MODEL=deepseek-chat
   AI_EMBED_MODEL=deepseek-embedding
   ```

### OpenAI Compatible（替代方案）

支持兼容 OpenAI API 协议的供应商（如智谱 GLM、通义千问 Qwen、Ollama 本地模型）：

```
AI_PROVIDER=openai_compatible
AI_API_KEY=your-api-key
AI_BASE_URL=https://your-provider-api-endpoint
AI_MODEL=model-name
AI_EMBED_MODEL=embedding-model-name  # 如果不支持 embedding，留空
```

---

## 故障排查

### 后端无法启动

```bash
# 查看日志
docker compose logs backend

# 测试数据库连接
docker compose exec backend python -c "
from app.infrastructure.config.settings import settings
from sqlalchemy import create_engine
engine = create_engine(settings.database_sync_url)
engine.connect()
print('✅ Database connected')
"
```

### 数据库连接失败

```bash
# 检查数据库是否就绪
docker compose exec db pg_isready -U postgres

# 重启数据库
docker compose restart db
```

### pgvector 扩展未安装

```bash
# 手动安装扩展
docker compose exec db psql -U postgres -d ai_store_copilot -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 前端无法访问后端

```bash
# 检查前端环境变量
docker compose exec frontend env | grep NEXT_PUBLIC

# 确保 API 代理配置正确
# next.config.ts 中的 rewrites 配置会代理 /api/* 到后端
```

### 常见问题

| 问题                  | 原因                         | 解决方案                        |
| --------------------- | ---------------------------- | ------------------------------- |
| `port already allocated` | 端口被占用                 | `docker compose down` 后重试    |
| `init.sql not found`  | docker-compose 找不到文件    | 确保 `backend/alembic/init.sql` 存在 |
| ModuleNotFoundError   | 缺少 Python 依赖             | `docker compose build --no-cache backend` |
| JWT 认证失败          | JWT_SECRET_KEY 不匹配        | 检查 `.env` 中的密钥配置        |
| AI 调用失败           | API Key 无效或网络不通       | 检查 `AI_API_KEY` 和网络代理    |
| 企业微信回调验证失败  | Token/AES Key 不匹配         | 确认后台配置与 `.env` 一致      |

---

## 架构总览

```
┌─────────┐     ┌──────────┐     ┌────────────┐
│ Nginx   │────▶│ Frontend │────▶│  Backend   │
│ :80/443 │     │ :3000    │     │  :8000     │
└─────────┘     └──────────┘     └─────┬──────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
             ┌──────────┐      ┌──────────┐      ┌──────────────┐
             │PostgreSQL│      │  Redis   │      │  DeepSeek    │
             │ pgvector │      │  Cache   │      │  AI API      │
             └──────────┘      └──────────┘      └──────────────┘
```

---

## 附录

### 项目目录结构

```
e:\AI客服（
├── backend/           # FastAPI 后端
│   ├── app/           # 应用代码
│   │   ├── domain/           # 领域层（纯 Python）
│   │   ├── application/      # 应用层（Use Case）
│   │   ├── infrastructure/   # 基础设施层
│   │   └── interfaces/       # 接口层（API 路由）
│   ├── alembic/       # 数据库迁移
│   └── tests/         # 测试
├── frontend/          # Next.js 前端
│   └── src/           # 源码
├── docker/            # Docker 编排
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── nginx/
├── docs/              # 文档
│   ├── deployment.md
│   ├── superpowers/
│   └── api/
└── .env.example       # 环境变量模板
```

### 关键技术决策

| 决策           | 选型       | 理由                           |
| -------------- | ---------- | ------------------------------ |
| 架构模式       | Clean Architecture | 业务逻辑与基础设施解耦，易于测试和替换 |
| API 风格       | RESTful + OpenAPI 3.0 | 标准化接口文档，自动生成 Swagger |
| ORM            | SQLAlchemy 2.0 (async) | 成熟的异步 ORM，支持复杂查询    |
| AI 模型抽象    | BaseAIModel 接口 | 供应商可替换，不影响业务逻辑    |
| RAG 检索策略   | 向量 + 关键词混合 + RRF | 兼顾语义和关键词匹配       |
| 认证方式       | JWT + RBAC    | 无状态认证，便于扩展            |
