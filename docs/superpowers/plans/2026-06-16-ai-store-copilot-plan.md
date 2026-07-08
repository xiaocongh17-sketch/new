# AI Store Copilot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build production-ready AI Store Copilot — WeChat-integrated AI assistant for real estate stores

**Architecture:** Clean Architecture monolith with Domain/Application/Infrastructure/Interface layers. FastAPI backend, Next.js 15 admin panel, PostgreSQL with pgvector for RAG, DeepSeek AI as default model. Fully Dockerized.

**Tech Stack:** FastAPI, Next.js 15, PostgreSQL 16, Redis 7, pgvector, DeepSeek API, Docker Compose

---

## Phase 1: Project Scaffolding

### Task 1.1: Initialize FastAPI project structure

**Files:**
- Create: `e:\AI客服（\backend\app\__init__.py`
- Create: `e:\AI客服（\backend\app\domain\__init__.py`
- Create: `e:\AI客服（\backend\app\application\__init__.py`
- Create: `e:\AI客服（\backend\app\infrastructure\__init__.py`
- Create: `e:\AI客服（\backend\app\interfaces\__init__.py`
- Create: `e:\AI客服（\backend\app\main.py`
- Create: `e:\AI客服（\backend\requirements.txt`

- [ ] **Step 1: Create Python package init files**

```
backend/app/__init__.py          # empty
backend/app/domain/__init__.py   # empty
backend/app/application/__init__.py
backend/app/infrastructure/__init__.py
backend/app/interfaces/__init__.py
```

- [ ] **Step 2: Create requirements.txt**

```
# Web framework
fastapi==0.115.0
uvicorn[standard]==0.30.6
gunicorn==23.0.0

# Database
sqlalchemy[asyncio]==2.0.35
asyncpg==0.30.0
alembic==1.13.2
psycopg2-binary==2.9.9

# AI / LLM
openai==1.51.0

# Serialization / Validation
pydantic==2.9.2
pydantic-settings==2.5.2

# Auth
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12

# WeCom
wechatpy==2.1.5
xmltodict==0.14.2

# RAG
pgvector==0.3.4
sentence-transformers==3.1.0

# Observability
structlog==24.4.0
opentelemetry-api==1.28.0

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
httpx==0.27.2

# Utils
python-dotenv==1.0.1
uuid7==0.1.0
```

- [ ] **Step 3: Create main.py entry point**

```python
"""AI Store Copilot — FastAPI Application Entry Point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info("app_starting")
    # TODO: Initialize connection pools, AI model, Redis
    yield
    # TODO: Cleanup resources
    logger.info("app_stopped")


app = FastAPI(
    title="AI Store Copilot API",
    description="房地产 AI 门店经营助手 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 4: Create .env.example**

```
# App
APP_NAME=AI Store Copilot
DEBUG=true
SECRET_KEY=change-me-in-production

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/ai_store_copilot
DATABASE_SYNC_URL=postgresql://postgres:postgres@db:5432/ai_store_copilot

# Redis
REDIS_URL=redis://redis:6379/0

# AI Model (DeepSeek)
AI_PROVIDER=deepseek
AI_API_KEY=sk-your-deepseek-api-key
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat
AI_EMBED_MODEL=deepseek-embedding

# WeCom
WECOM_CORP_ID=your-corp-id
WECOM_AGENT_ID=your-agent-id
WECOM_SECRET=your-agent-secret
WECOM_TOKEN=your-callback-token
WECOM_ENCODING_AES_KEY=your-aes-key
WECOM_WEBHOOK_URL=your-bot-webhook-url

# JWT
JWT_SECRET_KEY=change-me-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging
LOG_LEVEL=INFO
```

- [ ] **Step 5: Create infrastructure/config/settings.py**

```python
"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "AI Store Copilot"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/ai_store_copilot"
    database_sync_url: str = "postgresql://postgres:postgres@db:5432/ai_store_copilot"

    redis_url: str = "redis://redis:6379/0"

    ai_provider: str = "deepseek"
    ai_api_key: str = ""
    ai_base_url: str = "https://api.deepseek.com"
    ai_model: str = "deepseek-chat"
    ai_embed_model: str = "deepseek-embedding"

    wecom_corp_id: str = ""
    wecom_agent_id: str = ""
    wecom_secret: str = ""
    wecom_token: str = ""
    wecom_encoding_aes_key: str = ""
    wecom_webhook_url: str = ""

    jwt_secret_key: str = "change-me-in-production"
    jwt_access_token_expire_minutes: int = 120
    jwt_refresh_token_expire_days: int = 7

    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

- [ ] **Step 6: Create Dockerfile**

```dockerfile
FROM python:3.13-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM base AS development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "app.main:app", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

FROM base AS test
CMD ["pytest", "tests/", "-v", "--cov=app"]
```

- [ ] **Step 7: Create docker-compose.yml**

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      target: development
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ai_store_copilot
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/alembic/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      target: development
    ports:
      - "3000:3000"
    env_file:
      - .env
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

- [ ] **Step 8: Create docker-compose.prod.yml**

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      target: production
    environment:
      - DEBUG=false

  frontend:
    build:
      context: ./frontend
      target: production
    environment:
      - NEXT_PUBLIC_API_URL=/api

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
```

- [ ] **Step 9: Create nginx.conf**

```
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name _;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

- [ ] **Step 10: Test the scaffold**

```bash
cd "e:\AI客服（"
docker compose up -d db
docker compose run --rm backend pytest -v -x
```

Expected: FastAPI starts, health endpoint responds, test passes.

---

## Phase 2: Database Schema & Models

### Task 2.1: Create pgvector extension init SQL

**Files:**
- Create: `e:\AI客服（\backend\alembic\init.sql`

- [ ] **Step 1: Create init.sql for pgvector**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

### Task 2.2: Create Alembic migration setup

**Files:**
- Create: `e:\AI客服（\backend\alembic\env.py`
- Create: `e:\AI客服（\backend\alembic\alembic.ini`

- [ ] **Step 1: Create alembic.ini**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://postgres:postgres@db:5432/ai_store_copilot

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create env.py**

```python
"""Alembic migration environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.infrastructure.persistence.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Task 2.3: Create all SQLAlchemy ORM models

**Files:**
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\__init__.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\__init__.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\base.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\store.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\user.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\house.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\conversation.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\message.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\extracted_info.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\knowledge.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\models\audit_log.py`

- [ ] **Step 1: Create base.py with shared columns**

```python
"""Base ORM model with shared columns."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """Mixin for created_at / updated_at timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def uuid_pk() -> Mapped[uuid.UUID]:
    """UUID primary key column helper."""
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
```

- [ ] **Step 2: Create store.py**

```python
"""Store ORM model."""

import uuid
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, uuid_pk


class StoreModel(Base, TimestampMixin):
    __tablename__ = "stores"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
```

- [ ] **Step 3: Create user.py**

```python
"""User ORM model."""

import uuid
from sqlalchemy import Boolean, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
    )
    wecom_userid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # admin|store_manager|agent|landlord
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    store = relationship("StoreModel", backref="users")
```

- [ ] **Step 4: Create house.py**

```python
"""House ORM model."""

import uuid
from decimal import Decimal
from sqlalchemy import String, Text, Numeric, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class HouseModel(Base, TimestampMixin):
    __tablename__ = "houses"

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="SET NULL"), nullable=True
    )
    community: Mapped[str] = mapped_column(String(256), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    area: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    room_type: Mapped[str] = mapped_column(String(64), nullable=False)
    rent_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    decoration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    floor_info: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)

    owner = relationship("UserModel", backref="houses", foreign_keys=[owner_id])

    __table_args__ = (
        Index("idx_houses_store_status", "store_id", "status"),
        Index("idx_houses_community", "community"),
    )
```

- [ ] **Step 5: Create conversation.py**

```python
"""Conversation ORM model."""

import uuid
from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class ConversationModel(Base, TimestampMixin):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = uuid_pk()
    wecom_group_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    participants: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=True)
    context: Mapped[dict | None] = mapped_column(JSON, default=dict, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", nullable=False)
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="SET NULL"), nullable=True
    )
```

- [ ] **Step 6: Create message.py**

```python
"""Message ORM model."""

import uuid
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class MessageModel(Base, TimestampMixin):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    msg_type: Mapped[str] = mapped_column(String(32), default="text", nullable=False)
    wecom_msg_id: Mapped[str | None] = mapped_column(String(128), nullable=True)

    conversation = relationship("ConversationModel", backref="messages")
    sender = relationship("UserModel", backref="messages")

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id", "created_at"),
    )
```

- [ ] **Step 7: Create extracted_info.py**

```python
"""Extracted house info ORM model (AI extraction results)."""

import uuid
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class ExtractedHouseInfoModel(Base, TimestampMixin):
    __tablename__ = "extracted_house_info"

    id: Mapped[uuid.UUID] = uuid_pk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    community: Mapped[str | None] = mapped_column(String(256), nullable=True)
    area: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    room_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rent_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    decoration: Mapped[str | None] = mapped_column(String(32), nullable=True)
    floor_info: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    conversation = relationship("ConversationModel", backref="extracted_info")
```

- [ ] **Step 8: Create knowledge.py (with pgvector)**

```python
"""Knowledge document ORM model with pgvector support."""

import uuid
from sqlalchemy import String, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, uuid_pk


class KnowledgeDocModel(Base, TimestampMixin):
    __tablename__ = "knowledge_docs"

    id: Mapped[uuid.UUID] = uuid_pk()
    store_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)  # SOP|TRAINING|FAQ|MARKET
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata", JSON, default=dict, nullable=True
    )

    store = relationship("StoreModel", backref="knowledge_docs")

    __table_args__ = (
        Index("idx_knowledge_category", "category"),
        Index("idx_knowledge_store", "store_id"),
    )
```

- [ ] **Step 9: Create audit_log.py**

```python
"""Audit log ORM model."""

import uuid
from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin, uuid_pk


class AuditLogModel(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
```

- [ ] **Step 10: Create models/\_\_init\_\_.py**

```python
"""ORM models package."""

from .base import Base
from .store import StoreModel
from .user import UserModel
from .house import HouseModel
from .conversation import ConversationModel
from .message import MessageModel
from .extracted_info import ExtractedHouseInfoModel
from .knowledge import KnowledgeDocModel
from .audit_log import AuditLogModel

__all__ = [
    "Base",
    "StoreModel",
    "UserModel",
    "HouseModel",
    "ConversationModel",
    "MessageModel",
    "ExtractedHouseInfoModel",
    "KnowledgeDocModel",
    "AuditLogModel",
]
```

### Task 2.4: Create initial Alembic migration

**Files:**
- Create: `e:\AI客服（\backend\alembic\versions\0001_initial_schema.py`

- [ ] **Step 1: Generate initial migration**

```bash
cd "e:\AI客服（\backend"
alembic revision --autogenerate -m "initial schema"
```

- [ ] **Step 2: Apply migration**

```bash
docker compose run --rm backend alembic upgrade head
```

- [ ] **Step 3: Verify tables exist**

```bash
docker compose run --rm backend python -c "
from app.infrastructure.persistence.models import Base
from app.infrastructure.config.settings import settings
from sqlalchemy import create_engine
engine = create_engine(settings.database_sync_url)
for table in Base.metadata.sorted_tables:
    print(table.name)
"
```

---

## Phase 3: Domain Layer

### Task 3.1: Define enums and value objects

**Files:**
- Create: `e:\AI客服（\backend\app\domain\__init__.py`
- Create: `e:\AI客服（\backend\app\domain\value_objects\__init__.py`
- Create: `e:\AI客服（\backend\app\domain\value_objects\enums.py`

- [ ] **Step 1: Create all enums**

```python
"""Domain enumerations and value objects."""

from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    STORE_MANAGER = "store_manager"
    AGENT = "agent"
    LANDLORD = "landlord"


class DecorationType(str, Enum):
    ROUGH = "rough"          # 毛坯
    SIMPLE = "simple"        # 简装
    HARDCOVER = "hardcover"  # 精装
    LUXURY = "luxury"        # 豪装


class HouseStatus(str, Enum):
    PENDING = "pending"      # 待审核
    ACTIVE = "active"        # 出租中
    RENTED = "rented"        # 已出租
    OFF = "off"              # 已下架


class ConversationStatus(str, Enum):
    ACTIVE = "active"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    SYSTEM = "system"


class HouseSource(str, Enum):
    WECHAT = "wechat"
    MANUAL = "manual"
    IMPORT = "import"
```

### Task 3.2: Create domain entities

**Files:**
- Create: `e:\AI客服（\backend\app\domain\entities\__init__.py`
- Create: `e:\AI客服（\backend\app\domain\entities\store.py`
- Create: `e:\AI客服（\backend\app\domain\entities\user.py`
- Create: `e:\AI客服（\backend\app\domain\entities\house.py`
- Create: `e:\AI客服（\backend\app\domain\entities\conversation.py`
- Create: `e:\AI客服（\backend\app\domain\entities\message.py`

- [ ] **Step 1: Create Store entity**

```python
"""Store domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Store:
    id: uuid.UUID
    name: str
    code: str
    address: str | None = None
    contact_phone: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, name: str, code: str, address: str | None = None,
               contact_phone: str | None = None) -> "Store":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            name=name,
            code=code,
            address=address,
            contact_phone=contact_phone,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
```

- [ ] **Step 2: Create User entity**

```python
"""User domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from ..value_objects.enums import UserRole


@dataclass
class User:
    id: uuid.UUID
    wecom_userid: str
    name: str
    role: UserRole
    store_id: uuid.UUID | None = None
    phone: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, wecom_userid: str, name: str, role: UserRole,
               store_id: uuid.UUID | None = None, phone: str | None = None) -> "User":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            wecom_userid=wecom_userid,
            name=name,
            role=role,
            store_id=store_id,
            phone=phone,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_landlord(self) -> bool:
        return self.role == UserRole.LANDLORD

    @property
    def is_agent(self) -> bool:
        return self.role == UserRole.AGENT

    @property
    def is_store_manager(self) -> bool:
        return self.role == UserRole.STORE_MANAGER

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
```

- [ ] **Step 3: Create House entity**

```python
"""House domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from ..value_objects.enums import DecorationType, HouseStatus, HouseSource


@dataclass
class House:
    id: uuid.UUID
    community: str
    area: Decimal
    room_type: str
    rent_price: Decimal
    owner_id: uuid.UUID
    store_id: uuid.UUID | None = None
    address: str | None = None
    unit_price: Decimal | None = None
    decoration: str | None = None
    floor_info: str | None = None
    status: HouseStatus = HouseStatus.ACTIVE
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(
        cls,
        community: str,
        area: Decimal,
        room_type: str,
        rent_price: Decimal,
        owner_id: uuid.UUID,
        store_id: uuid.UUID | None = None,
        address: str | None = None,
        decoration: str | None = None,
        floor_info: str | None = None,
    ) -> "House":
        now = datetime.now(timezone.utc)
        unit_price = (rent_price / area).quantize(Decimal("0.01")) if area > 0 else None
        return cls(
            id=uuid.uuid4(),
            community=community,
            area=area,
            room_type=room_type,
            rent_price=rent_price,
            owner_id=owner_id,
            store_id=store_id,
            address=address,
            unit_price=unit_price,
            decoration=decoration,
            floor_info=floor_info,
            status=HouseStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )

    def update_price(self, new_price: Decimal) -> None:
        if new_price <= 0:
            raise ValueError("Price must be positive")
        self.rent_price = new_price
        self.unit_price = (new_price / self.area).quantize(Decimal("0.01"))

    def mark_rented(self) -> None:
        self.status = HouseStatus.RENTED

    def mark_off(self) -> None:
        self.status = HouseStatus.OFF
```

- [ ] **Step 4: Create Conversation entity**

```python
"""Conversation domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ..value_objects.enums import ConversationStatus


@dataclass
class Conversation:
    id: uuid.UUID
    wecom_group_id: str
    participants: list[uuid.UUID] = field(default_factory=list)
    context: dict = field(default_factory=dict)
    status: ConversationStatus = ConversationStatus.ACTIVE
    store_id: uuid.UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, wecom_group_id: str,
               participants: list[uuid.UUID] | None = None,
               store_id: uuid.UUID | None = None) -> "Conversation":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            wecom_group_id=wecom_group_id,
            participants=participants or [],
            context={},
            status=ConversationStatus.ACTIVE,
            store_id=store_id,
            created_at=now,
            updated_at=now,
        )

    def update_context(self, new_info: dict) -> None:
        """Merge new extracted info into conversation context."""
        self.context.update(new_info)
        self.updated_at = datetime.now(timezone.utc)

    def request_review(self) -> None:
        """Mark conversation as pending human review (escalation)."""
        self.status = ConversationStatus.PENDING_REVIEW

    def close(self) -> None:
        self.status = ConversationStatus.CLOSED
```

- [ ] **Step 5: Create Message entity**

```python
"""Message domain entity."""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from ..value_objects.enums import MessageType


@dataclass
class Message:
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: uuid.UUID
    content: str
    msg_type: MessageType = MessageType.TEXT
    wecom_msg_id: str | None = None
    created_at: datetime | None = None

    @classmethod
    def create(cls, conversation_id: uuid.UUID, sender_id: uuid.UUID,
               content: str, msg_type: MessageType = MessageType.TEXT,
               wecom_msg_id: str | None = None) -> "Message":
        return cls(
            id=uuid.uuid4(),
            conversation_id=conversation_id,
            sender_id=sender_id,
            content=content,
            msg_type=msg_type,
            wecom_msg_id=wecom_msg_id,
            created_at=datetime.now(timezone.utc),
        )
```

### Task 3.3: Create Repository interfaces

**Files:**
- Create: `e:\AI客服（\backend\app\domain\repositories\__init__.py`
- Create: `e:\AI客服（\backend\app\domain\repositories\user_repository.py`
- Create: `e:\AI客服（\backend\app\domain\repositories\house_repository.py`
- Create: `e:\AI客服（\backend\app\domain\repositories\store_repository.py`
- Create: `e:\AI客服（\backend\app\domain\repositories\conversation_repository.py`
- Create: `e:\AI客服（\backend\app\domain\repositories\knowledge_repository.py`

- [ ] **Step 1-6: Create repository interfaces**

```python
# user_repository.py
from abc import ABC, abstractmethod
import uuid
from ..entities.user import User

class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> User | None: ...
    @abstractmethod
    async def find_by_wecom_userid(self, wecom_userid: str) -> User | None: ...
    @abstractmethod
    async def find_by_store(self, store_id: uuid.UUID) -> list[User]: ...
    @abstractmethod
    async def save(self, user: User) -> User: ...
```

```python
# house_repository.py
from abc import ABC, abstractmethod
import uuid
from decimal import Decimal
from dataclasses import dataclass
from ..entities.house import House

@dataclass
class HouseFilter:
    community: str | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    room_type: str | None = None
    status: str | None = None
    store_id: uuid.UUID | None = None

@dataclass
class Page[T]:
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

class HouseRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> House | None: ...
    @abstractmethod
    async def find_by_store(self, store_id: uuid.UUID, filter: HouseFilter | None = None,
                            page: int = 1, page_size: int = 20) -> Page[House]: ...
    @abstractmethod
    async def save(self, house: House) -> House: ...
    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool: ...
```

```python
# store_repository.py
from abc import ABC, abstractmethod
import uuid
from ..entities.store import Store

class StoreRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> Store | None: ...
    @abstractmethod
    async def find_by_code(self, code: str) -> Store | None: ...
    @abstractmethod
    async def find_all(self) -> list[Store]: ...
    @abstractmethod
    async def save(self, store: Store) -> Store: ...
```

```python
# conversation_repository.py
from abc import ABC, abstractmethod
import uuid
from ..entities.conversation import Conversation
from ..entities.message import Message

class ConversationRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: uuid.UUID) -> Conversation | None: ...
    @abstractmethod
    async def find_active_by_group(self, wecom_group_id: str) -> Conversation | None: ...
    @abstractmethod
    async def find_by_store(self, store_id: uuid.UUID, page: int = 1,
                            page_size: int = 20) -> tuple[list[Conversation], int]: ...
    @abstractmethod
    async def save(self, conversation: Conversation) -> Conversation: ...
    @abstractmethod
    async def add_message(self, message: Message) -> Message: ...
    @abstractmethod
    async def get_messages(self, conversation_id: uuid.UUID,
                           limit: int = 50) -> list[Message]: ...
```

```python
# knowledge_repository.py
from abc import ABC, abstractmethod
import uuid
from dataclasses import dataclass
from ..entities.knowledge import KnowledgeDocument

@dataclass
class SearchResult:
    document: KnowledgeDocument
    similarity: float

class KnowledgeRepository(ABC):
    @abstractmethod
    async def search_by_vector(self, embedding: list[float], store_id: uuid.UUID | None = None,
                               limit: int = 10) -> list[SearchResult]: ...
    @abstractmethod
    async def search_by_keyword(self, query: str, store_id: uuid.UUID | None = None,
                                limit: int = 10) -> list[KnowledgeDocument]: ...
    @abstractmethod
    async def save(self, doc: KnowledgeDocument) -> KnowledgeDocument: ...
    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool: ...
```

Note: KnowledgeDocument entity needs to be created as well:

```python
# backend/app/domain/entities/knowledge.py
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

@dataclass
class KnowledgeDocument:
    id: uuid.UUID
    title: str
    content: str
    category: str
    store_id: uuid.UUID | None = None
    metadata_: dict = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def create(cls, title: str, content: str, category: str,
               store_id: uuid.UUID | None = None,
               metadata: dict | None = None) -> "KnowledgeDocument":
        now = datetime.now(timezone.utc)
        return cls(
            id=uuid.uuid4(),
            title=title,
            content=content,
            category=category,
            store_id=store_id,
            metadata_=metadata or {},
            created_at=now,
            updated_at=now,
        )
```

### Task 3.4: Create domain services

**Files:**
- Create: `e:\AI客服（\backend\app\domain\services\__init__.py`
- Create: `e:\AI客服（\backend\app\domain\services\house_extraction_service.py`
- Create: `e:\AI客服（\backend\app\domain\services\conversation_manager.py`

- [ ] **Step 1: Create HouseExtractionService**

```python
"""Domain service for extracting house information from natural language."""

import uuid
from decimal import Decimal
from dataclasses import dataclass, field


@dataclass
class ExtractedHouseInfo:
    community: str | None = None
    area: Decimal | None = None
    room_type: str | None = None
    rent_price: Decimal | None = None
    decoration: str | None = None
    floor_info: str | None = None


@dataclass
class ExtractionResult:
    extracted: ExtractedHouseInfo
    missing_fields: list[str]
    is_complete: bool
    suggestion: str | None = None


REQUIRED_FIELDS = ["community", "area", "room_type", "rent_price"]


class HouseExtractionService:
    """Domain service: validate extracted info and determine missing fields."""

    def get_missing_fields(self, info: ExtractedHouseInfo) -> list[str]:
        """Return list of required fields that are still missing."""
        missing = []
        if not info.community:
            missing.append("community")
        if info.area is None or info.area <= 0:
            missing.append("area")
        if not info.room_type:
            missing.append("room_type")
        if info.rent_price is None or info.rent_price <= 0:
            missing.append("rent_price")
        return missing

    def is_complete(self, info: ExtractedHouseInfo) -> bool:
        """Check if enough info has been collected to create a house listing."""
        return len(self.get_missing_fields(info)) == 0

    def merge_with_context(self, new_info: ExtractedHouseInfo,
                           existing: dict | None) -> ExtractedHouseInfo:
        """Merge newly extracted info with existing conversation context."""
        context = existing or {}
        return ExtractedHouseInfo(
            community=new_info.community or context.get("community"),
            area=new_info.area or context.get("area"),
            room_type=new_info.room_type or context.get("room_type"),
            rent_price=new_info.rent_price or context.get("rent_price"),
            decoration=new_info.decoration or context.get("decoration"),
            floor_info=new_info.floor_info or context.get("floor_info"),
        )

    def build_result(self, info: ExtractedHouseInfo) -> ExtractionResult:
        """Build the final extraction result with suggestion text."""
        missing = self.get_missing_fields(info)
        complete = len(missing) == 0

        suggestion = None
        if not complete:
            field_prompts = {
                "community": "请问您的小区名称是什么？",
                "area": "请问房子的面积大概多少平方米？",
                "room_type": "请问是几室几厅的户型？",
                "rent_price": "请问您期望的租金是多少？",
            }
            next_field = missing[0]
            suggestion = field_prompts.get(next_field, "请问还有其他信息可以补充吗？")

        return ExtractionResult(
            extracted=info,
            missing_fields=missing,
            is_complete=complete,
            suggestion=suggestion,
        )
```

- [ ] **Step 2: Create ConversationManager**

```python
"""Domain service: manage conversation context and escalation logic."""

from ..value_objects.enums import ConversationStatus

ESCALATION_KEYWORDS = [
    "投诉", "法律", "律师", "起诉", "法院", "举报",
    "投诉", "赔偿", "违法", "欺诈", "投诉",
]

SPECIAL_REQUIREMENT_KEYWORDS = [
    "特殊", "例外", "帮忙", "急", "马上", "立即",
]


class ConversationManager:
    """Domain service for conversation state management."""

    def should_escalate(self, content: str) -> tuple[bool, str]:
        """Check if a message requires human escalation.

        Returns:
            Tuple of (should_escalate, reason)
        """
        for keyword in ESCALATION_KEYWORDS:
            if keyword in content:
                return True, f"检测到关键词: {keyword}，需要人工处理"
        return False, ""

    def get_next_prompt(self, missing_fields: list[str]) -> str | None:
        """Get the next question to ask based on missing fields."""
        if not missing_fields:
            return None

        prompts = {
            "community": "请问您的小区名称是什么呢？",
            "area": "房子的面积大概是多少平方米呢？",
            "room_type": "请问是几室几厅的户型？",
            "rent_price": "您期望的租金大概是多少？",
            "decoration": "房子的装修情况怎么样？（毛坯/简装/精装/豪装）",
            "floor_info": "房子在几楼？总共多少层？",
        }
        return prompts.get(missing_fields[0])

    def can_proceed_with_partial_info(self, info: dict) -> bool:
        """Check if we have enough info to generate a rough quote/analysis."""
        required = {"community", "area", "room_type"}
        return required.issubset(set(info.keys()))
```

### Task 3.5: Unit tests for Domain Layer

**Files:**
- Create: `e:\AI客服（\backend\tests\__init__.py`
- Create: `e:\AI客服（\backend\tests\unit\__init__.py`
- Create: `e:\AI客服（\backend\tests\unit\domain\__init__.py`
- Create: `e:\AI客服（\backend\tests\unit\domain\test_entities.py`
- Create: `e:\AI客服（\backend\tests\unit\domain\test_value_objects.py`
- Create: `e:\AI客服（\backend\tests\unit\domain\test_domain_services.py`

- [ ] **Step 1: Write entity tests**

```python
# test_entities.py
import uuid
from decimal import Decimal
from app.domain.entities.user import User
from app.domain.entities.house import House
from app.domain.entities.store import Store
from app.domain.entities.conversation import Conversation
from app.domain.value_objects.enums import UserRole, HouseStatus, DecorationType


class TestUserEntity:
    def test_create_landlord(self):
        user = User.create(
            wecom_userid="wx_123",
            name="张三",
            role=UserRole.LANDLORD,
        )
        assert user.wecom_userid == "wx_123"
        assert user.name == "张三"
        assert user.role == UserRole.LANDLORD
        assert user.is_landlord is True
        assert user.is_agent is False

    def test_create_agent(self):
        store_id = uuid.uuid4()
        user = User.create(
            wecom_userid="wx_456",
            name="李四",
            role=UserRole.AGENT,
            store_id=store_id,
            phone="13800138000",
        )
        assert user.store_id == store_id
        assert user.phone == "13800138000"
        assert user.is_agent is True

    def test_user_is_active_by_default(self):
        user = User.create(wecom_userid="wx_test", name="Test", role=UserRole.AGENT)
        assert user.is_active is True


class TestHouseEntity:
    def test_create_house_calculates_unit_price(self):
        house = House.create(
            community="万科城",
            area=Decimal("89.50"),
            room_type="3室2厅2卫",
            rent_price=Decimal("3500"),
            owner_id=uuid.uuid4(),
            decoration="精装",
            floor_info="18/18",
        )
        assert house.community == "万科城"
        assert house.area == Decimal("89.50")
        assert house.room_type == "3室2厅2卫"
        assert house.rent_price == Decimal("3500")
        assert house.unit_price == Decimal("39.11")  # 3500 / 89.5
        assert house.status == HouseStatus.ACTIVE
        assert house.decoration == "精装"
        assert house.floor_info == "18/18"

    def test_update_price_recalculates_unit_price(self):
        house = House.create(
            community="测试小区",
            area=Decimal("100"),
            room_type="3室2厅",
            rent_price=Decimal("3000"),
            owner_id=uuid.uuid4(),
        )
        house.update_price(Decimal("3500"))
        assert house.rent_price == Decimal("3500")
        assert house.unit_price == Decimal("35.00")

    def test_mark_rented(self):
        house = House.create(
            community="测试", area=Decimal("80"), room_type="2室1厅",
            rent_price=Decimal("2000"), owner_id=uuid.uuid4(),
        )
        house.mark_rented()
        assert house.status == HouseStatus.RENTED

    def test_negative_price_raises(self):
        import pytest
        house = House.create(
            community="测试", area=Decimal("80"), room_type="2室1厅",
            rent_price=Decimal("2000"), owner_id=uuid.uuid4(),
        )
        with pytest.raises(ValueError, match="Price must be positive"):
            house.update_price(Decimal("-100"))


class TestStoreEntity:
    def test_create_store(self):
        store = Store.create(
            name="锡上好房旗舰店",
            code="WXHQD",
            address="无锡市梁溪区",
            contact_phone="0510-12345678",
        )
        assert store.name == "锡上好房旗舰店"
        assert store.code == "WXHQD"
        assert store.is_active is True

    def test_deactivate(self):
        store = Store.create(name="测试店", code="TEST")
        store.deactivate()
        assert store.is_active is False


class TestConversationEntity:
    def test_create_conversation(self):
        user_id = uuid.uuid4()
        conv = Conversation.create(
            wecom_group_id="grp_123",
            participants=[user_id],
        )
        assert conv.wecom_group_id == "grp_123"
        assert user_id in conv.participants
        assert conv.context == {}
        assert conv.status.value == "active"

    def test_update_context(self):
        conv = Conversation.create(wecom_group_id="grp_123")
        conv.update_context({"community": "万科城"})
        assert conv.context["community"] == "万科城"

    def test_request_review(self):
        conv = Conversation.create(wecom_group_id="grp_123")
        conv.request_review()
        assert conv.status.value == "pending_review"
```

- [ ] **Step 2: Write value object tests**

```python
# test_value_objects.py
from app.domain.value_objects.enums import (
    UserRole, DecorationType, HouseStatus,
    ConversationStatus, MessageType, HouseSource,
)


class TestEnums:
    def test_user_role_values(self):
        assert UserRole.ADMIN.value == "admin"
        assert UserRole.STORE_MANAGER.value == "store_manager"
        assert UserRole.AGENT.value == "agent"
        assert UserRole.LANDLORD.value == "landlord"

    def test_decoration_type_values(self):
        assert DecorationType.ROUGH.value == "rough"
        assert DecorationType.SIMPLE.value == "simple"
        assert DecorationType.HARDCOVER.value == "hardcover"
        assert DecorationType.LUXURY.value == "luxury"

    def test_house_status_values(self):
        assert HouseStatus.PENDING.value == "pending"
        assert HouseStatus.ACTIVE.value == "active"
        assert HouseStatus.RENTED.value == "rented"
        assert HouseStatus.OFF.value == "off"

    def test_conversation_status(self):
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.PENDING_REVIEW.value == "pending_review"
        assert ConversationStatus.CLOSED.value == "closed"
```

- [ ] **Step 3: Write domain service tests**

```python
# test_domain_services.py
from decimal import Decimal
from app.domain.services.house_extraction_service import (
    HouseExtractionService, ExtractedHouseInfo,
)
from app.domain.services.conversation_manager import ConversationManager


class TestHouseExtractionService:
    def setup_method(self):
        self.service = HouseExtractionService()

    def test_complete_info_returns_no_missing(self):
        info = ExtractedHouseInfo(
            community="万科城",
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        missing = self.service.get_missing_fields(info)
        assert missing == []

    def test_missing_community(self):
        info = ExtractedHouseInfo(
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        missing = self.service.get_missing_fields(info)
        assert "community" in missing

    def test_missing_area_and_price(self):
        info = ExtractedHouseInfo(
            community="万科城",
            room_type="3室2厅",
        )
        missing = self.service.get_missing_fields(info)
        assert "area" in missing
        assert "rent_price" in missing

    def test_is_complete(self):
        info = ExtractedHouseInfo(
            community="万科城",
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        assert self.service.is_complete(info) is True

    def test_is_not_complete(self):
        info = ExtractedHouseInfo(community="万科城")
        assert self.service.is_complete(info) is False

    def test_merge_with_context_keeps_existing(self):
        new_info = ExtractedHouseInfo(community="万科城")
        existing = {"room_type": "3室2厅", "area": Decimal("89.5")}
        merged = self.service.merge_with_context(new_info, existing)
        assert merged.community == "万科城"
        assert merged.room_type == "3室2厅"
        assert merged.area == Decimal("89.5")

    def test_build_result_with_suggestion(self):
        info = ExtractedHouseInfo(community="万科城")
        result = self.service.build_result(info)
        assert result.is_complete is False
        assert "area" in result.missing_fields
        assert result.suggestion is not None

    def test_build_result_complete(self):
        info = ExtractedHouseInfo(
            community="万科城",
            area=Decimal("89.5"),
            room_type="3室2厅",
            rent_price=Decimal("3500"),
        )
        result = self.service.build_result(info)
        assert result.is_complete is True
        assert result.missing_fields == []


class TestConversationManager:
    def setup_method(self):
        self.manager = ConversationManager()

    def test_escalate_on_complaint(self):
        should, reason = self.manager.should_escalate("我要投诉你们的服务")
        assert should is True
        assert "投诉" in reason

    def test_escalate_on_legal(self):
        should, _ = self.manager.should_escalate("我要找律师处理")
        assert should is True

    def test_no_escalate_on_normal(self):
        should, _ = self.manager.should_escalate("请问万科城3室2厅的租金大概多少？")
        assert should is False

    def test_get_next_prompt_community(self):
        prompt = self.manager.get_next_prompt(["community"])
        assert prompt is not None
        assert "小区" in prompt

    def test_get_next_prompt_none(self):
        prompt = self.manager.get_next_prompt([])
        assert prompt is None
```

- [ ] **Step 4: Run domain tests**

```bash
cd "e:\AI客服（"
docker compose run --rm backend pytest tests/unit/ -v
```

Expected: All domain tests pass.

---

## Phase 4: Infrastructure Layer

### Task 4.1: SQLAlchemy Repository implementations

**Files:**
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\repositories\__init__.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\repositories\user_repo.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\repositories\house_repo.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\repositories\store_repo.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\repositories\conversation_repo.py`
- Create: `e:\AI客服（\backend\app\infrastructure\persistence\database.py`

- [ ] **Step 1: Create database session helper**

```python
# database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.infrastructure.config.settings import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:  # type: ignore
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **Step 2-6: Create each repository implementation (converting between domain entities and ORM models)**

Each repository follows the same pattern:

```python
# user_repo.py — example
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.models.user import UserModel


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, id: UUID) -> User | None:
        result = await self.session.execute(select(UserModel).where(UserModel.id == id))
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_wecom_userid(self, wecom_userid: str) -> User | None:
        result = await self.session.execute(
            select(UserModel).where(UserModel.wecom_userid == wecom_userid)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_store(self, store_id: UUID) -> list[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.store_id == store_id)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, user: User) -> User:
        model = self._to_orm(user)
        self.session.add(model)
        await self.session.flush()
        return self._to_domain(model)

    def _to_domain(self, model: UserModel) -> User:
        from app.domain.value_objects.enums import UserRole
        return User(
            id=model.id,
            wecom_userid=model.wecom_userid,
            name=model.name,
            role=UserRole(model.role),
            store_id=model.store_id,
            phone=model.phone,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_orm(self, domain: User) -> UserModel:
        return UserModel(
            id=domain.id,
            wecom_userid=domain.wecom_userid,
            name=domain.name,
            role=domain.role.value,
            store_id=domain.store_id,
            phone=domain.phone,
            is_active=domain.is_active,
        )
```

Full implementations follow the same pattern for each repository.

### Task 4.2: AI Model abstraction and DeepSeek implementation

**Files:**
- Create: `e:\AI客服（\backend\app\infrastructure\ai\__init__.py`
- Create: `e:\AI客服（\backend\app\infrastructure\ai\base.py`
- Create: `e:\AI客服（\backend\app\infrastructure\ai\deepseek.py`
- Create: `e:\AI客服（\backend\app\infrastructure\ai\openai_compat.py`
- Create: `e:\AI客服（\backend\app\infrastructure\ai\factory.py`

- [ ] **Step 1: Create base AI model abstraction**

```python
# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel


@dataclass
class ChatMessage:
    role: str       # "system" | "user" | "assistant"
    content: str


@dataclass
class ChatResponse:
    content: str
    model: str
    usage: dict | None = None


class BaseAIModel(ABC):
    """Abstract base for all AI model providers."""

    @abstractmethod
    async def chat(self, messages: list[ChatMessage],
                   temperature: float = 0.7,
                   max_tokens: int = 2048) -> ChatResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def structured_extract(self, messages: list[ChatMessage],
                                  output_schema: type[BaseModel]) -> BaseModel:
        """Extract structured data from text."""
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for text."""
        ...
```

- [ ] **Step 2: Create DeepSeek implementation**

```python
# deepseek.py
from openai import AsyncOpenAI
from pydantic import BaseModel
from .base import BaseAIModel, ChatMessage, ChatResponse


class DeepSeekModel(BaseAIModel):
    """DeepSeek API implementation."""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com",
                 model: str = "deepseek-chat",
                 embed_model: str = "deepseek-embedding"):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.embed_model = embed_model

    async def chat(self, messages: list[ChatMessage],
                   temperature: float = 0.7,
                   max_tokens: int = 2048) -> ChatResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=self.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
        )

    async def structured_extract(self, messages: list[ChatMessage],
                                  output_schema: type[BaseModel]) -> BaseModel:
        system_msg = (
            f"你是一个数据提取助手。从用户输入中提取结构化信息，"
            f"以JSON格式输出，schema如下：\n{output_schema.model_json_schema()}\n"
            f"只输出JSON，不要包含其他内容。"
        )
        full_messages = [ChatMessage(role="system", content=system_msg)] + messages
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in full_messages],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        return output_schema.model_validate_json(content)

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=self.embed_model,
            input=text,
        )
        return response.data[0].embedding
```

- [ ] **Step 3: Create OpenAI Compatible implementation**

```python
# openai_compat.py
from openai import AsyncOpenAI
from pydantic import BaseModel
from .base import BaseAIModel, ChatMessage, ChatResponse


class OpenAICompatibleModel(BaseAIModel):
    """OpenAI-compatible API implementation (for Qwen/GLM/Ollama etc.)."""

    def __init__(self, api_key: str, base_url: str, model: str,
                 embed_model: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.embed_model = embed_model

    async def chat(self, messages, temperature=0.7, max_tokens=2048) -> ChatResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in messages],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        choice = response.choices[0]
        return ChatResponse(content=choice.message.content or "", model=self.model)

    async def structured_extract(self, messages, output_schema) -> BaseModel:
        system_msg = f"从输入中提取JSON格式数据：\n{output_schema.model_json_schema()}"
        full_messages = [ChatMessage(role="system", content=system_msg)] + messages
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": m.role, "content": m.content} for m in full_messages],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return output_schema.model_validate_json(response.choices[0].message.content or "{}")

    async def embed(self, text: str) -> list[float]:
        if not self.embed_model:
            raise NotImplementedError("Embedding not supported by this provider")
        response = await self.client.embeddings.create(
            model=self.embed_model, input=text,
        )
        return response.data[0].embedding
```

- [ ] **Step 4: Create AI model factory**

```python
# factory.py
from app.infrastructure.config.settings import settings
from .base import BaseAIModel
from .deepseek import DeepSeekModel
from .openai_compat import OpenAICompatibleModel

_model_instance: BaseAIModel | None = None


def get_ai_model() -> BaseAIModel:
    """Get or create the AI model singleton."""
    global _model_instance
    if _model_instance is not None:
        return _model_instance

    if settings.ai_provider == "deepseek":
        _model_instance = DeepSeekModel(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            embed_model=settings.ai_embed_model,
        )
    elif settings.ai_provider == "openai_compatible":
        _model_instance = OpenAICompatibleModel(
            api_key=settings.ai_api_key,
            base_url=settings.ai_base_url,
            model=settings.ai_model,
            embed_model=settings.ai_embed_model,
        )
    else:
        raise ValueError(f"Unknown AI provider: {settings.ai_provider}")

    return _model_instance
```

- [ ] **Step 5: Write unit tests for AI model (mocked)**

```python
# tests/unit/infrastructure/test_ai_model.py
from unittest.mock import AsyncMock, patch
from app.infrastructure.ai.base import BaseAIModel, ChatMessage
from app.infrastructure.ai.factory import get_ai_model
import pytest


class TestAIModelFactory:
    @patch("app.infrastructure.ai.factory.settings")
    def test_returns_deepseek_model(self, mock_settings):
        mock_settings.ai_provider = "deepseek"
        mock_settings.ai_api_key = "test_key"
        mock_settings.ai_base_url = "https://api.deepseek.com"
        mock_settings.ai_model = "deepseek-chat"
        mock_settings.ai_embed_model = "deepseek-embedding"

        model = get_ai_model()
        from app.infrastructure.ai.deepseek import DeepSeekModel
        assert isinstance(model, DeepSeekModel)
```

### Task 4.3: WeCom (企业微信) integration

**Files:**
- Create: `e:\AI客服（\backend\app\infrastructure\wecom\__init__.py`
- Create: `e:\AI客服（\backend\app\infrastructure\wecom\crypto.py`
- Create: `e:\AI客服（\backend\app\infrastructure\wecom\client.py`
- Create: `e:\AI客服（\backend\app\infrastructure\wecom\callback.py`

- [ ] **Step 1: Create WeCom crypto handler**

```python
# crypto.py
"""WeCom message encryption/decryption.

Uses wechatpy's crypto implementation for XML message encryption/decryption.
"""

from wechatpy.crypto import WeChatCrypto
from wechatpy.exceptions import InvalidSignatureException
from app.infrastructure.config.settings import settings

_crypto: WeChatCrypto | None = None


def get_crypto() -> WeChatCrypto:
    global _crypto
    if _crypto is None:
        _crypto = WeChatCrypto(
            token=settings.wecom_token,
            encoding_aes_key=settings.wecom_encoding_aes_key,
            corp_id=settings.wecom_corp_id,
        )
    return _crypto


def verify_url(signature: str, timestamp: str, nonce: str, echostr: str) -> str:
    """Verify URL challenge from WeCom. Returns decrypted echostr."""
    crypto = get_crypto()
    try:
        return crypto.check_signature(signature, timestamp, nonce, echostr)
    except InvalidSignatureException:
        raise ValueError("Invalid WeCom signature")


def decrypt_message(signature: str, timestamp: str, nonce: str, xml_data: str) -> str:
    """Decrypt an encrypted WeCom message XML."""
    crypto = get_crypto()
    return crypto.decrypt_message(xml_data, signature, timestamp, nonce)


def encrypt_message(reply_xml: str, nonce: str, timestamp: str | None = None) -> str:
    """Encrypt a reply message for WeCom."""
    from datetime import datetime
    crypto = get_crypto()
    timestamp = timestamp or str(int(datetime.now().timestamp()))
    return crypto.encrypt_message(reply_xml, nonce, timestamp)
```

- [ ] **Step 2: Create WeCom API client**

```python
# client.py
"""WeCom API client for sending messages and querying user info."""

import httpx
from app.infrastructure.config.settings import settings


class WeComClient:
    """Enterprise WeChat API client."""

    BASE_URL = "https://qyapi.weixin.qq.com/cgi-bin"

    def __init__(self, corp_id: str, agent_id: str, secret: str):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self._access_token: str | None = None
        self._token_expires_at: int = 0

    async def _get_access_token(self) -> str:
        """Get or refresh access token."""
        from datetime import datetime, timezone
        now = int(datetime.now(timezone.utc).timestamp())
        if self._access_token and now < self._token_expires_at:
            return self._access_token

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/gettoken",
                params={"corpid": self.corp_id, "corpsecret": self.secret},
            )
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"Failed to get token: {data.get('errmsg')}")
            self._access_token = data["access_token"]
            self._token_expires_at = now + data.get("expires_in", 7200) - 200
            return self._access_token

    async def send_text_message(self, touser: str, content: str,
                                chat_id: str | None = None) -> dict:
        """Send a text message to a user or group chat."""
        token = await self._get_access_token()
        payload = {
            "touser": touser,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {"content": content},
        }
        if chat_id:
            payload["chatid"] = chat_id

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/message/send",
                params={"access_token": token},
                json=payload,
            )
            return resp.json()

    async def send_webhook_message(self, content: str) -> dict:
        """Send message via group robot webhook (for notifications)."""
        if not settings.wecom_webhook_url:
            raise RuntimeError("WeCom webhook URL not configured")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                settings.wecom_webhook_url,
                json={"msgtype": "text", "text": {"content": content}},
            )
            return resp.json()

    async def get_user_info(self, userid: str) -> dict:
        """Get user details by WeCom user ID."""
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/user/get",
                params={"access_token": token, "userid": userid},
            )
            return resp.json()
```

- [ ] **Step 3: Create callback handler**

```python
# callback.py
"""WeCom callback message handler — parses XML messages into domain objects."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass


@dataclass
class WeComMessage:
    """Parsed WeCom message."""
    msg_id: str
    from_user: str          # 发送者 UserId
    to_user: str            # 接收者（应用ID或群ID）
    content: str
    msg_type: str           # text, image, event
    create_time: int
    agent_id: str | None = None
    chat_id: str | None = None  # 群聊ID


def parse_message_xml(xml_str: str) -> WeComMessage:
    """Parse WeCom message XML into WeComMessage dataclass."""
    root = ET.fromstring(xml_str)

    msg_id = root.findtext("MsgId", "")
    from_user = root.findtext("FromUserName", "")
    to_user = root.findtext("ToUserName", "")
    content = root.findtext("Content", "")
    msg_type = root.findtext("MsgType", "text")
    create_time_text = root.findtext("CreateTime", "0")

    return WeComMessage(
        msg_id=msg_id or root.findtext("MsgId", ""),
        from_user=from_user,
        to_user=to_user,
        content=content or root.findtext("Content", ""),
        msg_type=msg_type or root.findtext("MsgType", "text"),
        create_time=int(create_time_text or "0"),
    )
```

### Task 4.4: RAG Engine (pgvector)

**Files:**
- Create: `e:\AI客服（\backend\app\infrastructure\rag\__init__.py`
- Create: `e:\AI客服（\backend\app\infrastructure\rag\embedding.py`
- Create: `e:\AI客服（\backend\app\infrastructure\rag\retriever.py`

- [ ] **Step 1: Create embedding service**

```python
# embedding.py
from app.infrastructure.ai.factory import get_ai_model


class EmbeddingService:
    """Generate embeddings for RAG using the configured AI model."""

    def __init__(self):
        self.model = get_ai_model()

    async def embed_text(self, text: str) -> list[float]:
        return await self.model.embed(text)

    async def embed_document(self, title: str, content: str) -> list[float]:
        """Generate embedding for a document (title + content combined)."""
        combined = f"{title}\n{content}"
        return await self.model.embed(combined)
```

- [ ] **Step 2: Create retriever**

```python
# retriever.py
"""RAG retriever: multi-strategy retrieval with reranking."""

import uuid
import structlog
from app.infrastructure.config.settings import settings
from app.domain.repositories.knowledge_repository import KnowledgeRepository, SearchResult

logger = structlog.get_logger()


class Retriever:
    """Multi-strategy retriever with result fusion."""

    def __init__(self, knowledge_repo: KnowledgeRepository):
        self.knowledge_repo = knowledge_repo

    async def retrieve(
        self,
        query: str,
        query_embedding: list[float],
        store_id: uuid.UUID | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Retrieve relevant documents using vector + keyword hybrid search."""
        vector_results = await self.knowledge_repo.search_by_vector(
            embedding=query_embedding,
            store_id=store_id,
            limit=top_k,
        )

        keyword_results = await self.knowledge_repo.search_by_keyword(
            query=query,
            store_id=store_id,
            limit=top_k,
        )

        fused = self._fusion_rank(vector_results, keyword_results, top_k)

        logger.info(
            "retrieval_complete",
            query_length=len(query),
            vector_results=len(vector_results),
            keyword_results=len(keyword_results),
            fused_results=len(fused),
        )
        return fused

    def _fusion_rank(
        self,
        vector_results: list[SearchResult],
        keyword_results,
        top_k: int,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion (RRF) for combining two result sets."""
        doc_scores: dict[str, float] = {}

        for rank, result in enumerate(vector_results):
            doc_id = str(result.document.id)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1.0 / (rank + 60)

        for rank, doc in enumerate(keyword_results):
            doc_id = str(doc.id)
            score = 1.0 / (rank + 60)
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + score

        ranked_ids = sorted(doc_scores, key=doc_scores.get, reverse=True)[:top_k]

        doc_map = {str(r.document.id): r for r in vector_results}
        for doc in keyword_results:
            doc_map[str(doc.id)] = SearchResult(document=doc, similarity=0.0)

        return [doc_map[doc_id] for doc_id in ranked_ids if doc_id in doc_map]
```

---

## Phase 5: Application Layer (Use Cases)

### Task 5.1: Create all use cases

**Files:**
- Create: `e:\AI客服（\backend\app\application\dto\__init__.py`
- Create: `e:\AI客服（\backend\app\application\dto\wecom_dto.py`
- Create: `e:\AI客服（\backend\app\application\dto\house_dto.py`
- Create: `e:\AI客服（\backend\app\application\dto\chat_dto.py`
- Create: `e:\AI客服（\backend\app\application\use_cases\__init__.py`
- Create: `e:\AI客服（\backend\app\application\use_cases\handle_landlord_message.py`
- Create: `e:\AI客服（\backend\app\application\use_cases\extract_house_info.py`
- Create: `e:\AI客服（\backend\app\application\use_cases\answer_employee_query.py`
- Create: `e:\AI客服（\backend\app\application\use_cases\house_management.py`
- Create: `e:\AI客服（\backend\app\application\use_cases\user_management.py`
- Create: `e:\AI客服（\backend\app\application\use_cases\wecom_callback.py`

- [ ] **Step 1: Create DTOs**

```python
# dto/house_dto.py
from pydantic import BaseModel, Field
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from typing import Optional


class ExtractedHouseInfoDTO(BaseModel):
    community: Optional[str] = None
    area: Optional[Decimal] = None
    room_type: Optional[str] = None
    rent_price: Optional[Decimal] = None
    decoration: Optional[str] = None
    floor_info: Optional[str] = None


class ExtractHouseInfoInput(BaseModel):
    conversation_id: UUID
    raw_text: str
    existing_context: dict = Field(default_factory=dict)


class ExtractHouseInfoOutput(BaseModel):
    extracted_info: ExtractedHouseInfoDTO
    missing_fields: list[str]
    is_complete: bool
    suggestion: Optional[str] = None


class HouseResponse(BaseModel):
    id: UUID
    community: str
    area: Decimal
    room_type: str
    rent_price: Decimal
    unit_price: Optional[Decimal] = None
    decoration: Optional[str] = None
    floor_info: Optional[str] = None
    status: str
    owner_id: UUID
    created_at: datetime


class HouseCreateInput(BaseModel):
    community: str = Field(..., min_length=1, max_length=256)
    area: Decimal = Field(..., gt=0)
    room_type: str = Field(..., min_length=1)
    rent_price: Decimal = Field(..., gt=0)
    decoration: Optional[str] = None
    floor_info: Optional[str] = None
    owner_id: UUID


class HouseListResponse(BaseModel):
    items: list[HouseResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ChatInput(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    store_id: Optional[UUID] = None


class ChatOutput(BaseModel):
    answer: str
    sources: list[dict] = Field(default_factory=list)
```

- [ ] **Step 2: Create HandleLandlordMessage use case**

```python
# use_cases/handle_landlord_message.py
import structlog
from app.domain.entities.user import User
from app.domain.entities.conversation import Conversation
from app.domain.entities.message import Message
from app.domain.value_objects.enums import UserRole, MessageType
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.conversation_repository import ConversationRepository
from app.domain.services.house_extraction_service import HouseExtractionService
from app.domain.services.conversation_manager import ConversationManager
from app.infrastructure.ai.base import BaseAIModel, ChatMessage
from app.infrastructure.wecom.client import WeComClient

logger = structlog.get_logger()

LANDLORD_SYSTEM_PROMPT = """你是一个专业的房地产AI门店助手，正在帮助房东出租房源。

回答风格：
- 专业、亲切、简洁
- 用中文回答
- 每次最多追问一个信息点

你的职责包括：
1. 回答房东关于佣金、出租流程、材料要求的问题
2. 收集房源信息：小区名称、面积、户型、期望租金、装修情况
3. 当信息不完整时，自然地追问缺失的信息
4. 如果房东有投诉、法律问题或特殊要求，礼貌地告知会转接人工

已收集的信息：{collected_info}
"""


class HandleLandlordMessageUseCase:
    """Process a landlord's message and generate AI response."""

    def __init__(
        self,
        user_repo: UserRepository,
        conversation_repo: ConversationRepository,
        ai_model: BaseAIModel,
        wecom_client: WeComClient,
        extraction_service: HouseExtractionService | None = None,
        conversation_manager: ConversationManager | None = None,
    ):
        self.user_repo = user_repo
        self.conversation_repo = conversation_repo
        self.ai_model = ai_model
        self.wecom_client = wecom_client
        self.extraction_service = extraction_service or HouseExtractionService()
        self.conversation_manager = conversation_manager or ConversationManager()

    async def execute(self, wecom_userid: str, wecom_group_id: str,
                      content: str, wecom_msg_id: str | None = None) -> str:
        """Handle incoming landlord message. Returns AI reply content."""
        # 1. Identify user (register if new)
        user = await self.user_repo.find_by_wecom_userid(wecom_userid)
        if not user:
            user = User.create(
                wecom_userid=wecom_userid,
                name=wecom_userid,  # Will update later from WeCom profile
                role=UserRole.LANDLORD,
            )
            user = await self.user_repo.save(user)
            logger.info("new_landlord_registered", user_id=str(user.id))

        # 2. Get or create conversation
        conv = await self.conversation_repo.find_active_by_group(wecom_group_id)
        if not conv:
            conv = Conversation.create(
                wecom_group_id=wecom_group_id,
                participants=[user.id],
            )
            conv = await self.conversation_repo.save(conv)
        elif user.id not in conv.participants:
            conv.participants.append(user.id)
            conv = await self.conversation_repo.save(conv)

        # 3. Check for escalation
        should_escalate, reason = self.conversation_manager.should_escalate(content)
        if should_escalate:
            conv.request_review()
            await self.conversation_repo.save(conv)
            logger.warning("conversation_escalated", conv_id=str(conv.id), reason=reason)
            reply = "很抱歉，您提到的问题我需要转接给人工客服处理。请您稍等，我们的专业顾问会尽快联系您。"
            return await self._send_reply(user, conv, reply, wecom_msg_id)

        # 4. Build prompt with context
        collected = {k: v for k, v in conv.context.items() if v}
        system_prompt = LANDLORD_SYSTEM_PROMPT.format(
            collected_info=str(collected) if collected else "暂无"
        )

        # 5. Call AI model
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=content),
        ]
        response = await self.ai_model.chat(messages, temperature=0.7)

        # 6. Save message and reply
        msg = Message.create(
            conversation_id=conv.id,
            sender_id=user.id,
            content=content,
            msg_type=MessageType.TEXT,
            wecom_msg_id=wecom_msg_id,
        )
        await self.conversation_repo.add_message(msg)

        return await self._send_reply(user, conv, response.content, wecom_msg_id)

    async def _send_reply(self, user: User, conv: Conversation,
                          reply_content: str, wecom_msg_id: str | None) -> str:
        """Send reply via WeCom and save the message."""
        reply_msg = Message.create(
            conversation_id=conv.id,
            sender_id=user.id,
            content=reply_content,
            msg_type=MessageType.TEXT,
        )
        await self.conversation_repo.add_message(reply_msg)

        # Send via WeCom
        try:
            await self.wecom_client.send_text_message(
                touser=user.wecom_userid,
                content=reply_content,
                chat_id=conv.wecom_group_id,
            )
        except Exception as e:
            logger.error("wecom_send_failed", error=str(e), user_id=str(user.id))

        return reply_content
```

- [ ] **Step 3: Create ExtractHouseInfo use case**

```python
# use_cases/extract_house_info.py
import structlog
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from app.domain.services.house_extraction_service import (
    HouseExtractionService, ExtractedHouseInfo,
)
from app.infrastructure.ai.base import BaseAIModel, ChatMessage

logger = structlog.get_logger()


class HouseExtractionSchema(BaseModel):
    """Schema for AI structured output extraction."""
    community: Optional[str] = Field(None, description="小区名称")
    area: Optional[float] = Field(None, description="面积，单位：平方米")
    room_type: Optional[str] = Field(None, description="户型，如3室2厅2卫")
    rent_price: Optional[float] = Field(None, description="期望租金，单位：元/月")
    decoration: Optional[str] = Field(None, description="装修情况：毛坯/简装/精装/豪装")
    floor_info: Optional[str] = Field(None, description="楼层信息，如18/18")


class ExtractHouseInfoUseCase:
    """Extract structured house info from natural language using AI."""

    def __init__(self, ai_model: BaseAIModel,
                 extraction_service: HouseExtractionService | None = None):
        self.ai_model = ai_model
        self.extraction_service = extraction_service or HouseExtractionService()

    async def execute(self, raw_text: str,
                      existing_context: dict | None = None) -> dict:
        """Extract house info and return structured result."""
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "你是一个房源信息提取助手。从用户的对话中提取房源相关信息，"
                    "以JSON格式输出。如果某个信息没有提到，不要猜测，设为null。"
                ),
            ),
            ChatMessage(role="user", content=raw_text),
        ]

        try:
            extracted = await self.ai_model.structured_extract(
                messages=messages,
                output_schema=HouseExtractionSchema,
            )
        except Exception as e:
            logger.error("ai_extraction_failed", error=str(e), text=raw_text)
            return {
                "extracted_info": {},
                "missing_fields": ["community", "area", "room_type", "rent_price"],
                "is_complete": False,
                "suggestion": "抱歉，我没有理解您的信息，能请您再说一遍吗？",
            }

        domain_info = ExtractedHouseInfo(
            community=extracted.community,
            area=Decimal(str(extracted.area)) if extracted.area else None,
            room_type=extracted.room_type,
            rent_price=Decimal(str(extracted.rent_price)) if extracted.rent_price else None,
            decoration=extracted.decoration,
            floor_info=extracted.floor_info,
        )

        merged = self.extraction_service.merge_with_context(domain_info, existing_context)
        result = self.extraction_service.build_result(merged)

        return {
            "extracted_info": {
                "community": merged.community,
                "area": float(merged.area) if merged.area else None,
                "room_type": merged.room_type,
                "rent_price": float(merged.rent_price) if merged.rent_price else None,
                "decoration": merged.decoration,
                "floor_info": merged.floor_info,
            },
            "missing_fields": result.missing_fields,
            "is_complete": result.is_complete,
            "suggestion": result.suggestion,
        }
```

- [ ] **Step 4: Create AnswerEmployeeQuery use case (RAG)**

```python
# use_cases/answer_employee_query.py
import structlog
from app.domain.repositories.knowledge_repository import KnowledgeRepository
from app.infrastructure.ai.base import BaseAIModel, ChatMessage
from app.infrastructure.rag.embedding import EmbeddingService
from app.infrastructure.rag.retriever import Retriever
from app.infrastructure.config.settings import settings

logger = structlog.get_logger()

RAG_SYSTEM_PROMPT = """你是一个房地产门店AI业务助手。你的知识来自以下参考资料：

{context}

请基于以上资料回答员工的问题。如果资料中找不到答案，请如实说不知道，不要编造。
回答要求：专业、简洁、实用，适合一线业务员阅读。"""


class AnswerEmployeeQueryUseCase:
    """Answer employee business questions using RAG."""

    def __init__(
        self,
        ai_model: BaseAIModel,
        knowledge_repo: KnowledgeRepository,
        embedding_service: EmbeddingService | None = None,
        retriever: Retriever | None = None,
    ):
        self.ai_model = ai_model
        self.embedding_service = embedding_service or EmbeddingService()
        self.retriever = retriever or Retriever(knowledge_repo)

    async def execute(self, query: str, store_id: str | None = None) -> dict:
        """Answer query using RAG pipeline."""
        import uuid
        store_uuid = uuid.UUID(store_id) if store_id else None

        # 1. Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        # 2. Retrieve relevant documents
        search_results = await self.retriever.retrieve(
            query=query,
            query_embedding=query_embedding,
            store_id=store_uuid,
            top_k=5,
        )

        # 3. Build context from retrieved docs
        context_items = []
        sources = []
        for result in search_results:
            doc = result.document
            context_items.append(f"[{doc.category}] {doc.title}\n{doc.content}")
            sources.append({
                "title": doc.title,
                "category": doc.category,
                "similarity": result.similarity,
            })

        context = "\n\n---\n\n".join(context_items) if context_items else "暂无相关资料。"

        # 4. Call AI with context
        messages = [
            ChatMessage(role="system", content=RAG_SYSTEM_PROMPT.format(context=context)),
            ChatMessage(role="user", content=query),
        ]
        response = await self.ai_model.chat(messages, temperature=0.5)

        return {
            "answer": response.content,
            "sources": sources,
        }
```

- [ ] **Step 5: Create House Management use case**

```python
# use_cases/house_management.py
import uuid
from decimal import Decimal
import structlog
from app.domain.entities.house import House
from app.domain.entities.user import User
from app.domain.repositories.house_repository import HouseRepository, HouseFilter, Page
from app.domain.value_objects.enums import HouseStatus

logger = structlog.get_logger()


class CreateHouseUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, community: str, area: Decimal, room_type: str,
                      rent_price: Decimal, owner_id: uuid.UUID,
                      decoration: str | None = None,
                      floor_info: str | None = None,
                      store_id: uuid.UUID | None = None) -> House:
        house = House.create(
            community=community,
            area=area,
            room_type=room_type,
            rent_price=rent_price,
            owner_id=owner_id,
            store_id=store_id,
            decoration=decoration,
            floor_info=floor_info,
        )
        saved = await self.house_repo.save(house)
        logger.info("house_created", house_id=str(saved.id), owner_id=str(owner_id))
        return saved


class UpdateHouseUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, house_id: uuid.UUID, **kwargs) -> House | None:
        house = await self.house_repo.find_by_id(house_id)
        if not house:
            return None

        if "rent_price" in kwargs:
            house.update_price(Decimal(str(kwargs.pop("rent_price"))))
        for key, value in kwargs.items():
            if hasattr(house, key) and value is not None:
                setattr(house, key, value)

        saved = await self.house_repo.save(house)
        logger.info("house_updated", house_id=str(house_id))
        return saved


class DeleteHouseUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, house_id: uuid.UUID) -> bool:
        result = await self.house_repo.delete(house_id)
        if result:
            logger.info("house_deleted", house_id=str(house_id))
        return result


class SearchHousesUseCase:
    def __init__(self, house_repo: HouseRepository):
        self.house_repo = house_repo

    async def execute(self, store_id: uuid.UUID | None = None,
                      community: str | None = None,
                      min_price: Decimal | None = None,
                      max_price: Decimal | None = None,
                      room_type: str | None = None,
                      status: str | None = None,
                      page: int = 1, page_size: int = 20) -> Page[House]:
        filter = HouseFilter(
            community=community,
            min_price=min_price,
            max_price=max_price,
            room_type=room_type,
            status=status,
            store_id=store_id,
        )
        return await self.house_repo.find_by_store(
            store_id=store_id or uuid.UUID(int=0),
            filter=filter,
            page=page,
            page_size=page_size,
        )
```

- [ ] **Step 6: Create User Management use case**

```python
# use_cases/user_management.py
import uuid
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.enums import UserRole
from app.infrastructure.wecom.client import WeComClient


class RegisterUserFromWeComUseCase:
    """Register or lookup a user from WeCom user ID."""

    def __init__(self, user_repo: UserRepository, wecom_client: WeComClient):
        self.user_repo = user_repo
        self.wecom_client = wecom_client

    async def execute(self, wecom_userid: str) -> User:
        existing = await self.user_repo.find_by_wecom_userid(wecom_userid)
        if existing:
            return existing

        # Try to get user info from WeCom
        try:
            wecom_user = await self.wecom_client.get_user_info(wecom_userid)
            name = wecom_user.get("name", wecom_userid)
            role = UserRole.LANDLORD  # External contacts are landlords
        except Exception:
            name = wecom_userid
            role = UserRole.LANDLORD

        user = User.create(wecom_userid=wecom_userid, name=name, role=role)
        return await self.user_repo.save(user)
```

- [ ] **Step 7: Create WeCom Callback use case**

```python
# use_cases/wecom_callback.py
import structlog
from app.infrastructure.wecom.callback import WeComMessage
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.conversation_repository import ConversationRepository
from .handle_landlord_message import HandleLandlordMessageUseCase

logger = structlog.get_logger()


class HandleWecomCallbackUseCase:
    """Route incoming WeCom messages to the appropriate handler."""

    def __init__(
        self,
        landlord_handler: HandleLandlordMessageUseCase,
        user_repo: UserRepository,
    ):
        self.landlord_handler = landlord_handler
        self.user_repo = user_repo

    async def execute(self, wecom_msg: WeComMessage) -> str | None:
        """Route message based on sender role. Returns reply string if applicable."""
        logger.info(
            "wecom_callback_received",
            msg_type=wecom_msg.msg_type,
            from_user=wecom_msg.from_user,
        )

        if wecom_msg.msg_type != "text":
            logger.debug("non_text_message_ignored", msg_type=wecom_msg.msg_type)
            return None

        # Check if sender is known landlord
        sender = await self.user_repo.find_by_wecom_userid(wecom_msg.from_user)
        if sender and sender.role.value in ("landlord",):
            reply = await self.landlord_handler.execute(
                wecom_userid=wecom_msg.from_user,
                wecom_group_id=wecom_msg.to_user,
                content=wecom_msg.content,
                wecom_msg_id=wecom_msg.msg_id,
            )
            return reply

        # Unknown sender: register and treat as landlord
        reply = await self.landlord_handler.execute(
            wecom_userid=wecom_msg.from_user,
            wecom_group_id=wecom_msg.to_user,
            content=wecom_msg.content,
            wecom_msg_id=wecom_msg.msg_id,
        )
        return reply
```

### Task 5.2: Application layer tests

**Files:**
- Create: `e:\AI客服（\backend\tests\unit\application\__init__.py`
- Create: `e:\AI客服（\backend\tests\unit\application\test_use_cases.py`

- [ ] **Step 1: Write use case tests with mocks**

These tests mock all repository and AI dependencies to test use case logic in isolation.

---

## Phase 6: API Layer

### Task 6.1: Create API routes with JWT auth and RBAC

**Files:**
- Create: `e:\AI客服（\backend\app\interfaces\api\__init__.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\deps.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\__init__.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\wecom.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\auth.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\houses.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\conversations.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\employees.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\knowledge.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\ai.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\stores.py`
- Create: `e:\AI客服（\backend\app\interfaces\api\v1\dashboard.py`
- Create: `e:\AI客服（\backend\app\interfaces\middleware\__init__.py`
- Create: `e:\AI客服（\backend\app\interfaces\middleware\logging.py`
- Create: `e:\AI客服（\backend\app\interfaces\errors\__init__.py`
- Create: `e:\AI客服（\backend\app\interfaces\errors\handlers.py`

- [ ] **Step 1: Create auth dependencies**

```python
# deps.py
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.config.settings import settings
from app.infrastructure.persistence.database import async_session_factory
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository
from app.domain.entities.user import User
from app.domain.value_objects.enums import UserRole
from typing import Callable

security = HTTPBearer()


async def get_session():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_user_repo(session: AsyncSession = Depends(get_session)):
    return SQLAlchemyUserRepository(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: SQLAlchemyUserRepository = Depends(get_user_repo),
) -> User:
    """Validate JWT and return current user."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await user_repo.find_by_id(uuid.UUID(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_roles(allowed_roles: list[UserRole]) -> Callable:
    """RBAC decorator: check user has one of the allowed roles."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user.role.value}' not allowed for this endpoint",
            )
        return user
    return role_checker
```

- [ ] **Step 2: Create WeCom callback route**

```python
# v1/wecom.py
from fastapi import APIRouter, Request, Query, HTTPException
from app.infrastructure.wecom.crypto import verify_url, decrypt_message, encrypt_message
from app.infrastructure.wecom.callback import parse_message_xml
import structlog

router = APIRouter(prefix="/wecom", tags=["企业微信"])
logger = structlog.get_logger()


@router.get("/callback")
async def verify_callback(
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
    echostr: str = Query(...),
):
    """Verify WeCom callback URL (GET)."""
    try:
        decrypted = verify_url(msg_signature, timestamp, nonce, echostr)
        return int(decrypted)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/callback")
async def handle_callback(
    request: Request,
    msg_signature: str = Query(..., alias="msg_signature"),
    timestamp: str = Query(...),
    nonce: str = Query(...),
):
    """Handle WeCom callback message (POST)."""
    body = await request.body()
    xml_data = body.decode("utf-8")

    try:
        decrypted_xml = decrypt_message(msg_signature, timestamp, nonce, xml_data)
        wecom_msg = parse_message_xml(decrypted_xml)

        # TODO: inject use case and process message
        # reply = await handle_wecom_callback_uc.execute(wecom_msg)
        # if reply:
        #     reply_xml = build_reply_xml(wecom_msg.from_user, wecom_msg.to_user, reply)
        #     encrypted = encrypt_message(reply_xml, nonce)
        #     return Response(content=encrypted, media_type="application/xml")

        return {"errcode": 0, "errmsg": "ok"}
    except Exception as e:
        logger.error("wecom_callback_error", error=str(e))
        return {"errcode": 0, "errmsg": "ok"}  # Always return ok to WeCom
```

- [ ] **Step 3: Create auth routes**

```python
# v1/auth.py
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.config.settings import settings
from app.infrastructure.persistence.database import async_session_factory
from app.infrastructure.persistence.repositories.user_repo import SQLAlchemyUserRepository

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginInput(BaseModel):
    wecom_userid: str = Field(..., description="企业微信用户ID")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/login", response_model=TokenResponse)
async def login(input: LoginInput):
    """Login with WeCom user ID (simplified — production would use OAuth)."""
    async with async_session_factory() as session:
        repo = SQLAlchemyUserRepository(session)
        user = await repo.find_by_wecom_userid(input.wecom_userid)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        now = datetime.now(timezone.utc)
        access_payload = {
            "sub": str(user.id),
            "role": user.role.value,
            "store_id": str(user.store_id) if user.store_id else None,
            "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
            "type": "access",
        }
        refresh_payload = {
            "sub": str(user.id),
            "exp": now + timedelta(days=settings.jwt_refresh_token_expire_days),
            "type": "refresh",
        }

        return TokenResponse(
            access_token=jwt.encode(access_payload, settings.jwt_secret_key, algorithm="HS256"),
            refresh_token=jwt.encode(refresh_payload, settings.jwt_secret_key, algorithm="HS256"),
            expires_in=settings.jwt_access_token_expire_minutes * 60,
        )
```

- [ ] **Step 4-10: Create remaining API routes**

Each route follows the same pattern: inject dependencies via `Depends()`, call use cases, return Pydantic response models.

### Task 6.2: Wire up main.py with all routes

- [ ] **Step 1: Update main.py to include all routers**

```python
from app.interfaces.api.v1 import wecom, auth, houses, conversations, employees, knowledge, ai, stores, dashboard

app.include_router(wecom.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(houses.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(employees.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(stores.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
```

### Task 6.3: Add error handlers

- [ ] **Step 1: Create global error handlers**

```python
# errors/handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import structlog

logger = structlog.get_logger()


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
    )


async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("unhandled_error", path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )


def register_error_handlers(app):
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
```

---

## Phase 7: Frontend (Next.js 15)

### Task 7.1: Initialize Next.js project

**Files:**
- Create: `e:\AI客服（\frontend\package.json`
- Create: `e:\AI客服（\frontend\next.config.ts`
- Create: `e:\AI客服（\frontend\tsconfig.json`
- Create: `e:\AI客服（\frontend\tailwind.config.ts`
- Create: `e:\AI客服（\frontend\postcss.config.js`
- Create: `e:\AI客服（\frontend\Dockerfile`
- Create: `e:\AI客服（\frontend\.eslintrc.json`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "ai-store-copilot-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.59.0",
    "zustand": "^5.0.0",
    "lucide-react": "^0.449.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.5.3",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.6.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^9.0.0",
    "eslint-config-next": "15.0.0"
  }
}
```

### Task 7.2: Create shared UI components and layouts

**Files:**
- Create: `e:\AI客服（\frontend\src\lib\utils.ts`
- Create: `e:\AI客服（\frontend\src\lib\api.ts`
- Create: `e:\AI客服（\frontend\src\stores\auth.ts`
- Create: `e:\AI客服（\frontend\src\types\index.ts`
- Create: `e:\AI客服（\frontend\src\app\layout.tsx`
- Create: `e:\AI客服（\frontend\src\app\globals.css`

### Task 7.3: Create application pages

**Files:**
- Create: `e:\AI客服（\frontend\src\app\page.tsx` — Dashboard
- Create: `e:\AI客服（\frontend\src\app\houses\page.tsx` — House List
- Create: `e:\AI客服（\frontend\src\app\houses\[id]\page.tsx` — House Detail
- Create: `e:\AI客服（\frontend\src\app\employees\page.tsx` — Employee List
- Create: `e:\AI客服（\frontend\src\app\knowledge\page.tsx` — Knowledge Base
- Create: `e:\AI客服（\frontend\src\app\ai-chat\page.tsx` — AI Chat page
- Create: `e:\AI客服（\frontend\src\app\login\page.tsx` — Login page

---

## Phase 8: Testing

### Task 8.1: Integration tests

**Files:**
- Create: `e:\AI客服（\backend\tests\integration\__init__.py`
- Create: `e:\AI客服（\backend\tests\integration\conftest.py`
- Create: `e:\AI客服（\backend\tests\integration\test_repositories.py`
- Create: `e:\AI客服（\backend\tests\integration\test_api.py`

### Task 8.2: E2E tests

**Files:**
- Create: `e:\AI客服（\backend\tests\e2e\__init__.py`
- Create: `e:\AI客服（\backend\tests\e2e\test_full_flow.py`

---

## Phase 9: Deployment Documentation

### Task 9.1: Deployment docs and scripts

**Files:**
- Create: `e:\AI客服（\docs\deployment.md`
- Create: `e:\AI客服（\docker\nginx\nginx.conf`
- Create: `e:\AI客服（\.env.example`

---

## Summary

| Phase | Tasks | Files Created |
|-------|-------|---------------|
| 1: Scaffolding | 10 | 12 |
| 2: Database | 10 | 15 |
| 3: Domain Layer | 4 | 20 |
| 4: Infrastructure | 5 | 18 |
| 5: Application | 7 | 20 |
| 6: API Layer | 12 | 20 |
| 7: Frontend | 3 | 18 |
| 8: Testing | 2 | 6 |
| 9: Deployment | 1 | 3 |
| **Total** | **54** | **~132** |
