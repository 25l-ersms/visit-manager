import base64
import datetime
import json
import time
from typing import Any

import google.auth
import urllib3
from google.auth.compute_engine.credentials import Credentials
from google.auth.transport.urllib3 import Request

from visit_manager.package_utils.logger_conf import logger

# from https://cloud.google.com/managed-service-for-apache-kafka/docs/quickstart-python


def _encode(source: str) -> str:
    """Safe base64 encoding."""
    return base64.urlsafe_b64encode(source.encode("utf-8")).decode("utf-8").rstrip("=")


class KafkaTokenProvider(object):
    """
    Provides OAuth tokens from Google Cloud Application Default credentials.
    """

    def __init__(self, **config: dict[Any, Any]):
        self.credentials, _ = google.auth.default()
        self.http_client = urllib3.PoolManager()
        self.HEADER = json.dumps(dict(typ="JWT", alg="GOOG_OAUTH2_TOKEN"))

    def get_credentials(self) -> Credentials | None:
        if not self.credentials.valid:
            logger.debug("Application default credentials not valid, refreshing")
            self.credentials.refresh(Request(self.http_client))
        logger.debug("Application default credentials not valid")

        return self.credentials  # type: ignore[no-any-return]

    def get_jwt(self, creds: Credentials) -> str:
        token_data = dict(
            exp=creds.expiry.timestamp(),  # type: ignore[union-attr]
            iat=datetime.datetime.now(datetime.timezone.utc).timestamp(),
            iss="Google",
            scope="kafka",
            sub=creds.service_account_email,
        )
        return json.dumps(token_data)

    def get_token(self, config_str: str | None) -> tuple[str, float]:
        # Note: kafka client required that the function accepts a `config_str` parameter, which
        # is the value of `sasl.oauthbearer.config` in the Kafka client configuration
        # We're not using it, but without it, the client will silently fail the OAuth2 authentication (this behavior is not documented!)
        # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#kafka-client-configuration
        if config_str is not None:
            logger.warn("config_str was passed to get_token, but it will not be used")

        logger.debug("Requesting Kafka credentials")
        creds = self.get_credentials()
        if creds is None:
            raise RuntimeError("Could not find application default credentials")
        token = ".".join([_encode(self.HEADER), _encode(self.get_jwt(creds)), _encode(creds.token)])  # type: ignore[arg-type]
        logger.debug("Got Kafka credentials")

        utc_expiry = creds.expiry.replace(tzinfo=datetime.timezone.utc)  # type: ignore[union-attr]
        expiry_seconds = (utc_expiry - datetime.datetime.now(datetime.timezone.utc)).total_seconds()

        return token, time.time() + expiry_seconds
