import os
from typing import Any, Generator

import dotenv
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy_utils import create_database, database_exists

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


def get_pg_client_url() -> URL:
    username, pg_pass, pg_host, pg_port = get_creds()
    return URL.create(
        "postgresql+pg8000",
        username=username,
        password=pg_pass,  # plain (unescaped) text
        host=pg_host,
        port=int(pg_port),
        database="visit_manager",
    )


# Singleton class to create a connection to the database
class SqlEngine(object):
    def __init__(self) -> None:
        url = get_pg_client_url()
        self.engine = create_engine(url)
        if not database_exists(self.engine.url):
            create_database(self.engine.url)
            print(f"Database {self.engine.url.database} created")  # TODO add logger
        Base.metadata.create_all(self.engine)

    def __new__(cls) -> "SqlEngine":
        if not hasattr(cls, "instance"):
            cls.instance = super(SqlEngine, cls).__new__(cls)
            print("Create instance of SqlEngine")  # TODO add logger
        return cls.instance


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=SqlEngine().engine)


def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
