import asyncio
import json

import confluent_kafka  # type: ignore[import-untyped]

from visit_manager.kafka_utils.oauth import KafkaTokenProvider
from visit_manager.package_utils.logger_conf import logger
from visit_manager.package_utils.settings import KafkaSettings, kafka_authentication_scheme_t
from visit_manager.services.visit_service import create_visit


def _get_kafka_consumer_config(
    bootstrap_url: str, group_id: str, auth_scheme: kafka_authentication_scheme_t
) -> dict[str, (str | int | bool | object | None)]:
    config = {
        "bootstrap.servers": bootstrap_url,
        "group.id": group_id,
        "enable.auto.commit": True,
        "auto.offset.reset": "earliest",
    }

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


def _handle_message(topic: str, message: str) -> None:
    logger.info(f"Processing message: {message}")
    if topic == "visits.scheduled":
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            logger.error(f"Cannot decode JSON from visits.scheduled: {message}")
            return
        asyncio.create_task(create_visit(payload))
    else:
        logger.debug(f"Ignoring topic '{topic}' (no handler implemented).")


def listen_to_kafka() -> None:
    settings = KafkaSettings()

    auth_scheme: kafka_authentication_scheme_t = settings.AUTHENTICATION_SCHEME

    config = _get_kafka_consumer_config(
        bootstrap_url=settings.BOOTSTRAP_URL, group_id=settings.GROUP_ID, auth_scheme=auth_scheme
    )

    consumer = confluent_kafka.Consumer(config)
    topics = [t.strip() for t in settings.TOPIC.split(",")]
    consumer.subscribe(topics)
    logger.info(f"Listening for messages on Kafka topic '{settings.TOPIC}'...")

    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            logger.error(f"Kafka error: {msg.error()}")
            continue
        topic = msg.topic()
        payload = msg.value().decode("utf-8")
        _handle_message(topic, payload)


def enable_listen_to_kafka() -> None:
    """
    Enable the Kafka consumer to listen for messages.
    """
    logger.info("Starting Kafka consumer...")
    listen_to_kafka()
