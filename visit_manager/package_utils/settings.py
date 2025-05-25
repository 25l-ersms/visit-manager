from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class VisitManagerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VISIT_MANAGER_", env_file=".env", env_file_encoding="utf-8")

    LOG_LEVEL: str = "INFO"


kafka_authentication_scheme_t = Literal["oauth", "none"]


class KafkaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KAFKA_", env_file=".env", env_file_encoding="utf-8")

    TOPIC: str
    BOOTSTRAP_URL: str
    GROUP_ID: str = "handymen"
    AUTHENTICATION_SCHEME: kafka_authentication_scheme_t = "none"


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", env_file=".env", env_file_encoding="utf-8")

    USER: str
    PASSWORD: str
    HOST: str
    PORT: int = 5432
