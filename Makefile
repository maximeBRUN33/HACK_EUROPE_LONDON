.PHONY: api-install api-run api-run-debug api-test api-test-logs api-smoke web-install web-run

API_PORT ?= 8000
LOG_LEVEL ?= INFO
AST_PROGRESS_EVERY ?= 100

api-install:
	cd apps/api && pip install -e .[dev]

api-run:
	cd apps/api && LEGACY_ATLAS_LOG_LEVEL=$(LOG_LEVEL) LEGACY_ATLAS_AST_PROGRESS_EVERY=$(AST_PROGRESS_EVERY) uvicorn app.main:app --reload --port $(API_PORT)

api-run-debug:
	$(MAKE) api-run LOG_LEVEL=DEBUG AST_PROGRESS_EVERY=25

api-test:
	cd apps/api && python3 -m pytest -q

api-test-logs:
	cd apps/api && pytest -s -o log_cli=true -o log_cli_level=INFO

api-smoke:
	cd apps/api && pytest -s -k test_manual_cli_flow_sequence -o log_cli=true -o log_cli_level=INFO

web-install:
	cd apps/web && npm install

web-run:
	cd apps/web && npm run dev
