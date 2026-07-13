.PHONY: dev dev-backend dev-frontend dev-docker test lint clean

# ─── Development ──────────────────────────────────────────

dev: dev-docker dev-backend dev-frontend
	@echo "All services started!"

dev-backend:
	cd backend && python run.py

dev-frontend:
	cd frontend && npx next dev --port 3000

dev-docker:
	cd docker && docker compose -p ai-store-copilot up -d db redis

# ─── Docker (full stack) ─────────────────────────────────

docker-up:
	cd docker && docker compose -p ai-store-copilot up -d

docker-down:
	cd docker && docker compose -p ai-store-copilot down

docker-logs:
	cd docker && docker compose -p ai-store-copilot logs -f

# ─── Testing ──────────────────────────────────────────────

test:
	cd backend && pytest tests/ -v

test-cov:
	cd backend && pytest tests/ -v --cov=app --cov-report=term-missing

test-unit:
	cd backend && pytest tests/unit/ -v

test-integration:
	cd backend && pytest tests/integration/ -v

# ─── Lint ────────────────────────────────────────────────

lint:
	cd backend && ruff check app/ --fix
	cd frontend && npx next lint

# ─── Database ────────────────────────────────────────────

db-init:
	cd backend && python scripts/init_dev_db.py

db-seed:
	cd backend && python scripts/seed.py

db-reset:
	cd docker && docker compose -p ai-store-copilot down db
	docker volume rm ai-store-copilot_postgres_data || true
	cd docker && docker compose -p ai-store-copilot up -d db
	@sleep 3
	cd backend && python scripts/init_dev_db.py

db-migrate:
	cd backend && alembic revision --autogenerate -m "$(message)"

db-rollback:
	cd backend && alembic downgrade -1

# ─── Clean ────────────────────────────────────────────────

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ .coverage htmlcov/
	rm -f backend/dev.db backend/test.db
	rm -rf frontend/.next/
