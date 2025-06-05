import os
import threading
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from visit_manager.app.routers import auth, payment, visit_manage
from visit_manager.kafka_utils.common import enable_listen_to_kafka
from visit_manager.package_utils.logger_conf import logger
from visit_manager.package_utils.settings import VisitManagerSettings
from visit_manager.postgres_utils.utils import create_tables


@asynccontextmanager
async def lifespan(turbo_app: FastAPI) -> AsyncGenerator[None, Any]:
    logger.info("Initializing database connection...")
    await create_tables()
    logger.info("Starting Kafka consumer thread...")
    thread = threading.Thread(target=enable_listen_to_kafka, daemon=True)
    thread.start()
    yield  # App runs while this context is active
    logger.info("App is shutting down.")


app = FastAPI(
    lifespan=lifespan,
    root_path=VisitManagerSettings().ROOT_PATH,
)


# OAuth Setup
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("FASTAPI_SECRET_KEY"),
    https_only=False,  # Allow HTTP for development
    same_site="lax",  # Better compatibility for OAuth redirects
)

app.include_router(visit_manage.router)
app.include_router(payment.router)
app.include_router(auth.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
