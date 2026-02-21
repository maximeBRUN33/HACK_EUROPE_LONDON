.PHONY: api-install api-run api-test web-install web-run

api-install:
	cd apps/api && pip install -e .[dev]

api-run:
	cd apps/api && uvicorn app.main:app --reload --port 8000

api-test:
	cd apps/api && python3 -m pytest -q

web-install:
	cd apps/web && npm install

web-run:
	cd apps/web && npm run dev
