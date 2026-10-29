.PHONY: dev test lint typecheck check sync
sync:
	uv sync --extra dev
dev:
	uv run uvicorn resume_pipeline.main:app --host 127.0.0.1 --port 8000 --reload
test:
	uv run pytest -q
lint:
	uv run ruff check .
typecheck:
	uv run mypy resume_pipeline
check: lint typecheck test
