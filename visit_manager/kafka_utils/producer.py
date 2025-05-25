import functools

import confluent_kafka  # type: ignore[import-untyped]

from visit_manager.kafka_utils.common import KafkaTopics
from visit_manager.kafka_utils.oauth import KafkaTokenProvider
from visit_manager.package_utils.logger_conf import logger
from visit_manager.package_utils.settings import KafkaSettings, kafka_authentication_scheme_t


def _get_kafka_config(
    bootstrap_url: str, auth_scheme: kafka_authentication_scheme_t
) -> dict[str, (str | int | bool | object | None)]:
    config: dict[str, (str | int | bool | object | None)] = {"bootstrap.servers": bootstrap_url}

    if auth_scheme == "oauth":
        logger.debug("Using OAuth for Kafka authentication")
        token_provider = KafkaTokenProvider()

        config = config | {
            "security.protocol": "SASL_SSL",
            "sasl.mechanisms": "OAUTHBEARER",
            "oauth_cb": token_provider.get_token,
        }
    else:
        logger.debug("Assuming Kafka authentication is not required")

    return config


def _callback(error: str, message: str) -> None:
    if error is not None:
        logger.error(f"Message delivery failed: {error}")
    else:
        logger.info(f"Delivered message {message}")


@functools.lru_cache(maxsize=1)
def _get_producer() -> confluent_kafka.Producer:  # type: ignore[no-any-unimported]
    settings = KafkaSettings()
    logger.info("Initializing Kafka producer")

    auth_scheme: kafka_authentication_scheme_t = settings.AUTHENTICATION_SCHEME

    config = _get_kafka_config(bootstrap_url=settings.BOOTSTRAP_URL, auth_scheme=auth_scheme)

    producer = confluent_kafka.Producer(config)
    logger.info("Initialized Kafka producer")
    return producer


def send_message(message: str, topic: KafkaTopics) -> None:
    """
    Send a message to the Kafka topic.
    """

    producer = _get_producer()
    producer.poll(timeout=0.0)
    producer.produce(topic.topic_name, value=message.encode("utf-8"), key="message", callback=_callback)
    producer.flush()
