# AI Store Copilot — 房地产 AI 门店经营助手（标杆合作版）

## 设计文档

| 项目     | 内容                                     |
| -------- | ---------------------------------------- |
| 版本     | v1.0                                     |
| 日期     | 2026-06-16                               |
| 状态     | Draft → Approved                         |
| 技术栈   | Next.js 15 + FastAPI + PostgreSQL + Redis + Docker |

---

## 1. 项目目标

帮助房地产门店实现：

1. 自动接待房东（企业微信群消息）
2. 自动收集房东信息（结构化抽取）
3. 自动生成房源
4. 辅助业务员沟通（AI 对话）
5. 为员工提供业务问答（RAG）
6. 构建房源数据库

**MVP 定位**：AI 助手先行。「锡上好房」全链路业务系统（定价、推广、服务团队、买家管理、交易管理）作为 V2，架构预留扩展点。

---

## 2. 用户角色与权限

| 角色           | 标识             | 核心权限                                                     |
| -------------- | ---------------- | ------------------------------------------------------------ |
| 系统管理员     | `admin`          | 管理门店、员工，查看所有数据                                 |
| 店长           | `store_manager`  | 管理本门店员工，查看房源和客户                               |
| 业务员         | `agent`          | 查看自己的客户，使用 AI 助手                                 |
| 房东           | `landlord`       | 企业微信群交流（不登录后台）                                 |

---

## 3. 系统架构

### 3.1 整体架构模式

**方案**：Clean Architecture Monolith（推荐）

```
Interface Layer  →  Application Layer  →  Domain Layer
（API 路由）       （用例编排）            （纯业务逻辑）
      │
      ▼
Infrastructure Layer
（技术实现：DB/AI/WeCom/Redis）
```

### 3.2 分层职责

| 层              | 职责                                               | 外部依赖         |
| --------------- | -------------------------------------------------- | ---------------- |
| **Domain**      | 实体、值对象、聚合根、领域服务、Repository 接口    | 无（纯 Python）  |
| **Application** | 用例编排、DTO、接口定义                            | Domain           |
| **Infrastructure** | SQLAlchemy 实现、AI 模型适配（DeepSeek）、企业微信集成、RAG 引擎 | Domain + 外部SDK |
| **Interfaces**  | FastAPI 路由、Middlewares、错误处理、OpenAPI        | Application      |

### 3.3 项目目录结构

```
e:\AI客服（
├── backend/
│   ├── app/
│   │   ├── domain/
│   │   │   ├── entities/               # 实体
│   │   │   ├── value_objects/          # 值对象
│   │   │   ├── repositories/           # Repository 接口
│   │   │   └── services/               # 领域服务
│   │   ├── application/
│   │   │   ├── use_cases/              # 用例
│   │   │   ├── dto/                    # 数据传输对象
│   │   │   └── interfaces/             # 应用层接口
│   │   ├── infrastructure/
│   │   │   ├── persistence/            # SQLAlchemy
│   │   │   │   ├── models/            # ORM 模型
│   │   │   │   └── repositories/      # Repository 实现
│   │   │   ├── ai/                    # AI 模型适配
│   │   │   │   ├── base.py           # BaseAIModel 抽象
│   │   │   │   ├── deepseek.py       # DeepSeek 实现
│   │   │   │   └── openai_compat.py  # OpenAI Compatible 实现
│   │   │   ├── wecom/                # 企业微信集成
│   │   │   │   ├── crypto.py         # 加解密
│   │   │   │   ├── client.py         # API 客户端
│   │   │   │   └── callback.py       # 回调处理
│   │   │   ├── rag/                  # RAG 引擎
│   │   │   │   ├── embedding.py      # 向量化
│   │   │   │   └── retriever.py      # 检索器
│   │   │   └── config/               # 配置
│   │   ├── interfaces/
│   │   │   ├── api/                  # FastAPI 路由
│   │   │   │   ├── v1/              # API v1
│   │   │   │   └── deps.py          # 依赖注入
│   │   │   ├── middleware/           # 中间件
│   │   │   └── errors/              # 异常处理
│   │   └── main.py                  # 应用入口
│   ├── alembic/                     # 数据库迁移
│   ├── tests/                       # 测试
│   │   ├── unit/
│   │   ├── integration/
│   │   ├── e2e/
│   │   └── conftest.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/                     # App Router
│   │   ├── components/              # UI 组件（shadcn/ui）
│   │   ├── lib/                     # 工具库
│   │   ├── hooks/                   # 自定义 Hooks
│   │   ├── stores/                  # Zustand stores
│   │   ├── services/                # API 客户端
│   │   └── types/                   # TypeScript 类型
│   ├── Dockerfile
│   └── package.json
│
├── docker/
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   └── nginx/
│
├── docs/
│   ├── superpowers/specs/
│   ├── api/
│   └── deployment.md
│
└── .env.example
```

---

## 4. 数据库设计

### 4.1 ER 图

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│    stores    │       │      users       │       │    houses    │
│──────────────│       │──────────────────│       │──────────────│
│ id (PK)      │──1:N──│ id (PK)          │       │ id (PK)      │
│ name         │       │ store_id (FK)    │──1:N──│ owner_id (FK)│
│ code         │       │ wecom_userid     │       │ community    │
│ address      │       │ name             │       │ area         │
│ contact_phone│       │ role             │       │ room_type    │
│ is_active    │       │ phone            │       │ rent_price   │
│ created_at   │       │ is_active        │       │ decoration   │
│ updated_at   │       │ created_at       │       │ floor_info   │
└──────────────┘       │ updated_at       │       │ status       │
                       └──────────────────┘       │ unit_price   │
                                                   │ store_id     │
┌──────────────────┐    ┌──────────────────┐       │ created_at   │
│  conversations   │    │    messages      │       │ updated_at   │
│──────────────────│    │──────────────────│       └──────────────┘
│ id (PK)          │──1:N│ id (PK)          │
│ wecom_group_id   │    │ conversation_id  │
│ participants[]   │    │ sender_id (FK)   │
│ context (jsonb)  │    │ content          │
│ status           │    │ msg_type         │
│ store_id         │    │ wecom_msg_id     │
│ created_at       │    │ created_at       │
│ updated_at       │    └──────────────────┘
└──────────────────┘
        │
        │ 1:N
┌──────────────────────────────┐
│     extracted_house_info     │
│──────────────────────────────│
│ id (PK)                      │
│ conversation_id (FK)         │
│ community  │ area            │
│ room_type  │ rent_price      │
│ decoration │ floor_info      │
│ is_confirmed                 │
│ created_at │ updated_at      │
└──────────────────────────────┘

┌──────────────────┐
│ knowledge_docs   │
│──────────────────│
│ id (PK)          │
│ store_id (FK)    │
│ title            │
│ content          │
│ category         │
│ embedding(vector)│
│ metadata (jsonb) │
│ created_at       │
│ updated_at       │
└──────────────────┘

┌──────────────────┐
│   audit_logs     │
│──────────────────│
│ id (PK)          │
│ user_id (FK)     │
│ action           │
│ resource_type    │
│ resource_id      │
│ details (jsonb)  │
│ ip_address       │
│ created_at       │
└──────────────────┘
```

### 4.2 核心表定义

**stores** — 门店表
| 字段         | 类型         | 约束                     |
| ------------ | ------------ | ------------------------ |
| id           | UUID         | PK, DEFAULT gen_random_uuid() |
| name         | VARCHAR(128) | NOT NULL                 |
| code         | VARCHAR(64)  | NOT NULL, UNIQUE         |
| address      | TEXT         |                          |
| contact_phone| VARCHAR(32)  |                          |
| is_active    | BOOLEAN      | DEFAULT true             |
| created_at   | TIMESTAMPTZ  | DEFAULT NOW()            |
| updated_at   | TIMESTAMPTZ  | DEFAULT NOW()            |

**users** — 用户表
| 字段          | 类型         | 约束                     |
| ------------- | ------------ | ------------------------ |
| id            | UUID         | PK                       |
| store_id      | UUID         | FK → stores.id           |
| wecom_userid  | VARCHAR(128) | NOT NULL, UNIQUE, INDEX  |
| name          | VARCHAR(128) | NOT NULL                 |
| role          | VARCHAR(32)  | NOT NULL                 |
| phone         | VARCHAR(32)  |                          |
| is_active     | BOOLEAN      | DEFAULT true             |
| created_at    | TIMESTAMPTZ  | DEFAULT NOW()            |
| updated_at    | TIMESTAMPTZ  | DEFAULT NOW()            |

**houses** — 房源表
| 字段         | 类型          | 约束                     |
| ------------ | ------------- | ------------------------ |
| id           | UUID          | PK                       |
| owner_id     | UUID          | FK → users.id            |
| store_id     | UUID          | FK → stores.id           |
| community    | VARCHAR(256)  | NOT NULL                 |
| address      | TEXT          |                          |
| area         | NUMERIC(10,2) | NOT NULL                 |
| room_type    | VARCHAR(64)   | NOT NULL                 |
| rent_price   | NUMERIC(12,2) | NOT NULL                 |
| unit_price   | NUMERIC(10,2) |                          |
| decoration   | VARCHAR(32)   |                          |
| floor_info   | VARCHAR(64)   |                          |
| status       | VARCHAR(32)   | DEFAULT 'active'         |
| created_at   | TIMESTAMPTZ   | DEFAULT NOW()            |
| updated_at   | TIMESTAMPTZ   | DEFAULT NOW()            |

**conversations** — 对话表
| 字段            | 类型         | 约束                     |
| --------------- | ------------ | ------------------------ |
| id              | UUID         | PK                       |
| wecom_group_id  | VARCHAR(128) | NOT NULL, INDEX          |
| participants    | UUID[]       |                          |
| context         | JSONB        | DEFAULT '{}'             |
| status          | VARCHAR(32)  | DEFAULT 'active'         |
| store_id        | UUID         | FK → stores.id           |
| created_at      | TIMESTAMPTZ  | DEFAULT NOW()            |
| updated_at      | TIMESTAMPTZ  | DEFAULT NOW()            |

**messages** — 消息表
| 字段             | 类型         | 约束                     |
| ---------------- | ------------ | ------------------------ |
| id               | UUID         | PK                       |
| conversation_id  | UUID         | FK → conversations.id    |
| sender_id        | UUID         | FK → users.id            |
| content          | TEXT         | NOT NULL                 |
| msg_type         | VARCHAR(32)  | DEFAULT 'text'           |
| wecom_msg_id     | VARCHAR(128) |                          |
| created_at       | TIMESTAMPTZ  | DEFAULT NOW()            |

**extracted_house_info** — AI 抽取房源信息（临时表）
| 字段            | 类型          | 约束                     |
| --------------- | ------------- | ------------------------ |
| id              | UUID          | PK                       |
| conversation_id | UUID          | FK → conversations.id    |
| community       | VARCHAR(256)  |                          |
| area            | NUMERIC(10,2) |                          |
| room_type       | VARCHAR(64)   |                          |
| rent_price      | NUMERIC(12,2) |                          |
| decoration      | VARCHAR(32)   |                          |
| floor_info      | VARCHAR(64)   |                          |
| is_confirmed    | BOOLEAN       | DEFAULT false            |
| created_at      | TIMESTAMPTZ   | DEFAULT NOW()            |
| updated_at      | TIMESTAMPTZ   | DEFAULT NOW()            |

**knowledge_docs** — 知识库文档（支持 pgvector）
| 字段         | 类型         | 约束                     |
| ------------ | ------------ | ------------------------ |
| id           | UUID         | PK                       |
| store_id     | UUID         | FK → stores.id           |
| title        | VARCHAR(256) | NOT NULL                 |
| content      | TEXT         | NOT NULL                 |
| category     | VARCHAR(32)  | NOT NULL                 |
| embedding    | vector(1536) |                          |
| metadata     | JSONB        | DEFAULT '{}'             |
| created_at   | TIMESTAMPTZ  | DEFAULT NOW()            |
| updated_at   | TIMESTAMPTZ  | DEFAULT NOW()            |

**audit_logs** — 审计日志表
| 字段          | 类型         | 约束                     |
| ------------- | ------------ | ------------------------ |
| id            | UUID         | PK                       |
| user_id       | UUID         | FK → users.id            |
| action        | VARCHAR(64)  | NOT NULL                 |
| resource_type | VARCHAR(64)  | NOT NULL                 |
| resource_id   | VARCHAR(128) |                          |
| details       | JSONB        |                          |
| ip_address    | VARCHAR(64)  |                          |
| created_at    | TIMESTAMPTZ  | DEFAULT NOW()            |

---

## 5. Domain 层设计

### 5.1 实体

- **User** — 用户聚合根（角色：admin/store_manager/agent/landlord）
- **Store** — 门店聚合根
- **House** — 房源聚合根
- **Conversation** — 对话聚合根
- **Message** — 消息值对象

### 5.2 值对象

- **UserRole** — 用户角色枚举
- **DecorationType** — 装修类型枚举（rough/simple/hardcover/luxury）
- **HouseStatus** — 房源状态枚举（pending/active/rented/off）
- **MessageType** — 消息类型枚举
- **ConversationStatus** — 对话状态枚举

### 5.3 领域服务

| 服务                            | 职责                                         |
| ------------------------------- | -------------------------------------------- |
| **HouseExtractionService**      | 从自然语言中提取房源结构化信息                |
| **ConversationManager**         | 管理对话上下文、判断转人工、追踪缺失字段      |
| **RentCalculationService**      | 计算佣金（预留门店策略维度）                  |

### 5.4 Repository 接口

| 接口                     | 核心方法                                                     |
| ------------------------ | ------------------------------------------------------------ |
| **UserRepository**       | find_by_id, find_by_wecom_userid, find_by_store, save        |
| **HouseRepository**      | find_by_id, find_by_store (paginated), save, delete          |
| **StoreRepository**      | find_by_id, save                                              |
| **ConversationRepository** | find_active_by_group, save, add_message                    |
| **KnowledgeRepository**  | search_by_vector, search_by_keyword, save, delete            |

---

## 6. Application 层设计

### 6.1 用例清单

| 用例                                     | 描述                               |
| ---------------------------------------- | ---------------------------------- |
| **HandleLandlordMessageUseCase**         | 处理房东消息 → AI 回复或转人工    |
| **ExtractHouseInfoUseCase**              | 自然语言 → 结构化房源信息          |
| **SubmitHouseUseCase**                   | 创建新房源（AI 确认后自动创建）     |
| **UpdateHouseUseCase**                   | 更新房源信息                       |
| **SearchHousesUseCase**                  | 多条件搜索房源                     |
| **GetHouseDetailUseCase**                | 房源详情                           |
| **AnswerEmployeeQueryUseCase**            | 员工业务问答（RAG）                |
| **RegisterUserUseCase**                  | 从企业微信消息注册用户/房东         |
| **AuthenticateUserUseCase**              | JWT 认证                           |
| **HandleWecomCallbackUseCase**            | 企业微信回调分发                    |

### 6.2 DTO 设计（示例）

```python
class ExtractHouseInfoInput(BaseModel):
    conversation_id: UUID
    raw_text: str
    existing_context: dict | None = None

class ExtractedHouseInfo(BaseModel):
    community: str | None = None
    area: float | None = None
    room_type: str | None = None
    rent_price: Decimal | None = None
    decoration: str | None = None
    floor_info: str | None = None

class ExtractHouseInfoOutput(BaseModel):
    extracted_info: ExtractedHouseInfo
    missing_fields: list[str]
    is_complete: bool
    suggestion: str | None = None
```

---

## 7. Infrastructure 层设计

### 7.1 AI 模型抽象

```python
class BaseAIModel(ABC):
    async def chat(self, messages, temperature, max_tokens) -> ChatResponse
    async def structured_extract(self, messages, output_schema) -> BaseModel
    async def embed(self, text) -> list[float]
```

实现：
- **DeepSeekModel** — 基于 DeepSeek API（MVP 默认）
- **OpenAICompatibleModel** — 通用 OpenAI 兼容协议（扩展备选）

工厂：`AIModelFactory.create(config)` 根据配置返回对应实例。

### 7.2 RAG 引擎

- 向量维度：1536（DeepSeek Embedding）
- 存储：pgvector
- 检索策略：向量相似度检索 + 全文关键词检索 → 融合重排序

### 7.3 企业微信集成

- 回调验证：signature + timestamp + nonce + AES 解密
- 消息类型：文本消息、@消息、群消息
- 身份识别：从回调中提取 sender UserId → 查用户表确认角色
- 被动回复：通过企业微信 API 发送消息

---

## 8. API 设计

### 8.1 路由结构

```
POST   /api/v1/wecom/callback          # 企业微信回调入口
POST   /api/v1/auth/login              # 后台登录（用户名密码→JWT）
POST   /api/v1/auth/refresh            # Token 刷新

GET    /api/v1/houses                   # 房源列表（分页+搜索+过滤）
POST   /api/v1/houses                   # 创建房源
GET    /api/v1/houses/{id}             # 房源详情
PUT    /api/v1/houses/{id}             # 更新房源
DELETE /api/v1/houses/{id}             # 删除房源
GET    /api/v1/houses/{id}/report      # 房源分析报告

GET    /api/v1/conversations            # 对话列表
GET    /api/v1/conversations/{id}      # 对话详情

GET    /api/v1/employees                # 员工管理列表
PUT    /api/v1/employees/{id}          # 更新员工信息

GET    /api/v1/stores                   # 门店列表
POST   /api/v1/stores                   # 创建门店
GET    /api/v1/stores/{id}             # 门店详情
PUT    /api/v1/stores/{id}             # 更新门店

GET    /api/v1/knowledge                # 知识库文档列表
POST   /api/v1/knowledge                # 上传知识文档
DELETE /api/v1/knowledge/{id}          # 删除知识文档

POST   /api/v1/ai/chat                 # AI 业务助手对话
GET    /api/v1/dashboard/stats          # Dashboard 统计概览
```

### 8.2 认证

- JWT（access token 2h, refresh token 7d）
- RBAC 权限校验（依赖注入层）
- OpenAPI 3.0 Bearer Auth

---

## 9. 错误处理

- **DomainError** — 领域异常基类（code + status_code + message）
- **全局异常处理器**：DomainError → 400/403/404, ValidationError → 422, 未预期异常 → 500
- 响应格式统一：`{ "error": { "code": "...", "message": "...", "details": ... } }`

---

## 10. 日志体系

- 库：`structlog`
- 格式：JSON（生产环境），开发环境可读格式
- 级别：INFO 业务事件，ERROR 异常
- 关键日志点：AI 调用耗时、企业微信回调、用户操作、异常堆栈

---

## 11. 测试策略

| 层级         | 覆盖范围               | 外部依赖     |
| ------------ | ---------------------- | ------------ |
| Unit         | 实体、值对象、领域服务 | 无（Mock）   |
| Integration  | Repository、AI 抽取    | 测试 DB      |
| E2E          | 完整 API 流程          | 测试 DB + Mock AI |

---

## 12. 部署架构

```
Nginx（反向代理 + SSL）
├── /api/* → FastAPI（Gunicorn + Uvicorn workers）
├── /     → Next.js（standalone）
└── /docs → OpenAPI Swagger UI

PostgreSQL（pgvector）← FastAPI
Redis（缓存 + Session）← FastAPI
```

---

## 13. V2 扩展预留

当前架构已预留以下扩展点：

| 扩展点           | 预留方式                                    |
| ---------------- | ------------------------------------------- |
| AI 供应商替换    | BaseAIModel 抽象 + AIModelFactory           |
| SaaS 多租户      | store_id 隔离 + RBAC                        |
| 消息队列（异步） | UseCase 接口不变，只加 Worker 进程         |
| 全链路业务系统   | Domain 层可新增实体，不影响现有模块         |
| 第三方平台接入   | 现有 UseCase 不变，新增 PlatformAdapter     |
| 数据分析/BI      | audit_logs 提供基础数据，可扩展分析 Pipeline |

---

## 14. 开发顺序

1. 项目脚手架（项目结构、Docker Compose、配置体系）
2. Database Schema + Alembic 迁移
3. Domain 层（实体、值对象、Repository 接口、领域服务）
4. Infrastructure 层（SQLAlchemy 实现、AI 模型适配、企业微信集成）
5. Application 层（所有 UseCase）
6. API 层（路由 + OpenAPI + Auth）
7. 前端（后台管理页面）
8. 测试覆盖
9. 部署文档

---

*文档结束*
