import threading
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from visit_manager.app.routers import visit_manage
from visit_manager.kafka_utils.common import enable_listen_to_kafka
from visit_manager.package_utils.logger_conf import logger

# from fastapi.security import OAuth2PasswordBearer


# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # TODO setup OAuth and uncomment this line


@asynccontextmanager
async def lifespan(turboApp: FastAPI) -> AsyncGenerator[None, Any]:
    logger.info("Starting Kafka consumer thread...")
    thread = threading.Thread(target=enable_listen_to_kafka, daemon=True)
    thread.start()
    yield  # App runs while this context is active
    logger.info("App is shutting down.")


app = FastAPI(lifespan=lifespan)

app.include_router(visit_manage.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
