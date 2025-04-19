import os
from typing import Any, AsyncGenerator

import dotenv
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from visit_manager.package_utils.logger_conf import logger
from visit_manager.postgres_utils.models import Base


def get_k8s_es_credits(v1: client.CoreV1Api) -> tuple[str, str, str, str]:
    print("K8s...")
    return "", "", "", ""


def get_creds() -> tuple[str, str, str, str]:
    try:
        config.load_kube_config()  # type: ignore[attr-defined]
    except ConfigException:
        dotenv.load_dotenv()
        return (
            os.getenv("POSTGRES_USER") or "",
            os.getenv("POSTGRES_PASSWORD") or "",
            os.getenv("POSTGRES_HOST") or "",
            os.getenv("POSTGRES_PORT") or "",
        )
    v1 = client.CoreV1Api()
    return get_k8s_es_credits(v1)


def get_url() -> str:
    db_user, db_password, db_host, db_port = get_creds()
    return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/visit_manager"


async def create_tables() -> None:
    """Create database tables asynchronously"""
    db_user, db_password, db_host, db_port = get_creds()

    temp_engine = create_async_engine(
        f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/postgres", echo=True
    )

    async with temp_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1 FROM pg_database WHERE datname='visit_manager'"))
        if not result.scalar_one_or_none():
            await conn.execute(text("COMMIT"))  # End transaction
            await conn.execute(text("CREATE DATABASE visit_manager"))
            logger.info("Database created")

    await temp_engine.dispose()

    create_engine = create_async_engine(
        f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/visit_manager", echo=True
    )

    async with create_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tables created")


engine = create_async_engine(get_url(), echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, Any]:
    """Get a database session"""
    async with AsyncSessionLocal() as session:
        yield session
