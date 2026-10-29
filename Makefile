# Root convenience targets. Per-app commands live in each app.
SHELL := /bin/zsh

.PHONY: bootstrap up down reset db-migrate pipeline-check ascend-check check doctor

bootstrap:
	pnpm install
	cd apps/resume-pipeline && uv sync --extra dev
	$(MAKE) up
	$(MAKE) db-migrate

# pg_isready alone is not enough on a first boot: initdb runs a temporary server
# that answers, then stops so the real one can start. Polling it races, and the
# loser sees "the database system is shutting down" partway through a migration.
# Require three consecutive real queries a second apart instead.
up:
	docker compose -f docker-compose.dev.yml up -d --wait postgres
	@ok=0; tries=0; \
	while [ $$ok -lt 3 ]; do \
		if docker compose -f docker-compose.dev.yml exec -T postgres psql -U ascend -d ascend -tAc 'select 1' >/dev/null 2>&1; then \
			ok=$$((ok+1)); \
		else \
			ok=0; \
		fi; \
		tries=$$((tries+1)); \
		if [ $$tries -gt 60 ]; then echo "postgres did not stabilise" >&2; exit 1; fi; \
		sleep 1; \
	done
	@echo "postgres ready on 127.0.0.1:55432"

down:
	docker compose -f docker-compose.dev.yml down

reset:
	docker compose -f docker-compose.dev.yml down -v
	$(MAKE) up
	$(MAKE) db-migrate

db-migrate:
	@for f in apps/ascend/supabase/migrations/*.sql; do \
		echo "applying $$f"; \
		docker compose -f docker-compose.dev.yml exec -T postgres psql -v ON_ERROR_STOP=1 -U ascend -d ascend < "$$f" >/dev/null || exit 1; \
	done
	@echo "migrations applied"

pipeline-check:
	cd apps/resume-pipeline && $(MAKE) check

ascend-check:
	pnpm --filter @labs/ascend check

check: pipeline-check ascend-check

doctor:
	@echo "node   $$(node --version 2>/dev/null || echo MISSING)"
	@echo "pnpm   $$(pnpm --version 2>/dev/null || echo MISSING)"
	@echo "uv     $$(uv --version 2>/dev/null || echo MISSING)"
	@echo "docker $$(docker --version 2>/dev/null || echo MISSING)"
	@docker compose -f docker-compose.dev.yml ps
