import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.env_loader import load_env_file
from app.logging_config import setup_logging

ENV_FILE_LOADED = load_env_file()
setup_logging()
logger = logging.getLogger(__name__)

from app.routers.copilot import router as copilot_router
from app.routers.graphs import router as graphs_router
from app.routers.health import router as health_router
from app.routers.integrations import router as integrations_router
from app.routers.repos import router as repos_router

app = FastAPI(title="Legacy Atlas API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(repos_router)
app.include_router(graphs_router)
app.include_router(copilot_router)
app.include_router(integrations_router)

logger.info("Legacy Atlas API initialized env_file_loaded=%s", ENV_FILE_LOADED)
