# GreenThumb Makefile
# Shortcuts for common Docker operations

.PHONY: help prod dev dev-nc reset-db update update-% sync logs logs-api logs-ctrl db-shell clean restart-% mock test

help:
	@echo "GreenThumb Docker Commands:"
	@echo ""
	@echo "  Production:"
	@echo "    make prod        - Pull latest pre-built images and start"
	@echo "    make up          - Start all services (no build)"
	@echo "    make down        - Stop all services"
	@echo ""
	@echo "  Development:"
	@echo "    make dev         - Quick build (api + controller) and start"
	@echo "    make dev-nc      - Build without cache (force reinstall libs) and start"
	@echo "    make reset-db    - Wipe database volume and restart (applies new sql scripts)"
	@echo "    make update      - Update all git submodules"
	@echo "    make sync        - Commit and push all submodule changes"
	@echo ""
	@echo "  Utilities:"
	@echo "    make logs        - Follow logs from all services"
	@echo "    make logs-api    - Follow API logs only"
	@echo "    make logs-ctrl   - Follow controller logs only"
	@echo "    make db-shell    - Open psql shell to database"
	@echo "    make clean       - Remove all containers, volumes, images (DANGER!)"
	@echo ""
	@echo "  Testing:"
	@echo "    make mock        - Run standalone mock API locally for Postman testing"
	@echo "    make test        - Run automated tests locally"

# ============================================
# PRODUCTION
# ============================================

prod:
	docker compose pull
	docker compose up -d

up:
	docker compose up -d

down:
	docker compose down --remove-orphans

# ============================================
# DEVELOPMENT
# ============================================

dev:
	docker compose build
	docker compose up -d

dev-nc:
	docker compose build --no-cache
	docker compose up -d

reset-db:
	docker compose stop db
	docker compose rm -f -v db
	docker volume rm greenthumb_postgres_data || true
	docker compose up -d db

reset-all:
	docker compose stop
	docker compose rm -f -v
	docker volume rm greenthumb_postgres_data || true
	docker compose up -d

# ============================================
# SUBMODULE MANAGEMENT
# ============================================

update:
	git submodule update --remote --merge
	git add .
	git commit -m "chore: update all submodules"

# Specific submodule updates (optional but good to keep)
update-%:
	git submodule update --remote $*
	git add $*
	git commit -m "chore: update $* submodule"

# Commit and push all submodule changes
sync:
	@for mod in microcontroller-api greenthumb-models greenthumb-rpi5 local-dashboard; do \
	  if [ -n "$$(git -C $$mod status --porcelain)" ]; then \
	    echo "Committing $$mod..."; \
	    git -C $$mod add -A && git -C $$mod commit -m "wip: sync"; \
	    git -C $$mod push; \
	  fi; \
	done
	git add microcontroller-api greenthumb-models greenthumb-rpi5 local-dashboard
	git commit -m "chore: sync submodules" || true
	git push

# ============================================
# UTILITIES
# ============================================

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-ctrl:
	docker compose logs -f controller

db-shell:
	docker compose exec db psql -U root -d greenthumb

clean:
	@echo "Removing all docker containers..."
	-if [ -n "$$(docker ps -aq)" ]; then docker rm -f $$(docker ps -aq); fi
	docker compose down --remove-orphans --volumes
	docker image prune -af

restart-%:
	docker compose restart $*

# ============================================
# TESTING
# ============================================

mock:
	cd microcontroller-api && .venv\Scripts\python.exe run_mock.py

test:
	cd microcontroller-api && .venv\Scripts\python.exe -m pytest tests/ -v