# Meridian Airport PMO suite
# (c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved.
# Proprietary — unauthorised copying, distribution, modification or use prohibited.

.PHONY: help up down logs ps reset migrate seed test fmt lint backend-shell frontend-shell psql redis-cli

help:
	@echo "Meridian — common dev tasks"
	@echo "(c) GV Softwares. Developed by Gaurav Vatsa. All rights reserved."
	@echo ""
	@echo "  make up              docker compose up --build (frontend, backend, worker, pg, redis)"
	@echo "  make down            stop everything"
	@echo "  make logs            tail logs from all services"
	@echo "  make ps              service status"
	@echo "  make reset           down + remove volumes (wipes DB)"
	@echo "  make migrate         alembic upgrade head"
	@echo "  make seed            python -m app.seed inside backend container"
	@echo "  make test            run pytest inside backend container"
	@echo "  make fmt             ruff format + black + prettier"
	@echo "  make lint            ruff + mypy + eslint"
	@echo "  make backend-shell   bash into backend container"
	@echo "  make frontend-shell  bash into frontend container"
	@echo "  make psql            psql into postgres"
	@echo "  make redis-cli       redis-cli into redis"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps

reset:
	docker compose down -v

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.seed

test:
	docker compose exec backend pytest -q

fmt:
	docker compose exec backend ruff format app tests
	docker compose exec frontend npm run format

lint:
	docker compose exec backend ruff check app tests
	docker compose exec frontend npm run lint

backend-shell:
	docker compose exec backend bash

frontend-shell:
	docker compose exec frontend sh

psql:
	docker compose exec postgres psql -U meridian -d meridian

redis-cli:
	docker compose exec redis redis-cli
