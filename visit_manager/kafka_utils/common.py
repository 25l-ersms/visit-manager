import confluent_kafka  # type: ignore[import-untyped]

from visit_manager.kafka_utils.oauth import KafkaTokenProvider
from visit_manager.package_utils.logger_conf import logger
from visit_manager.package_utils.settings import KafkaSettings, kafka_authentication_scheme_t


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


def _handle_message(message: str) -> None:
    logger.info(f"Processing message: {message}")


def listen_to_kafka() -> None:
    settings = KafkaSettings()

    auth_scheme: kafka_authentication_scheme_t = settings.AUTHENTICATION_SCHEME

    config = _get_kafka_consumer_config(
        bootstrap_url=settings.BOOTSTRAP_URL, group_id=settings.GROUP_ID, auth_scheme=auth_scheme
    )

    consumer = confluent_kafka.Consumer(config)
    consumer.subscribe([settings.TOPIC])
    logger.info(f"Listening for messages on Kafka topic '{settings.TOPIC}'...")

    while True:
        msg = consumer.poll(timeout=1.0)
        if msg is None:
            continue
        if msg.error():
            logger.error(f"Kafka error: {msg.error()}")
            continue
        _handle_message(msg.value().decode("utf-8"))


def enable_listen_to_kafka() -> None:
    """
    Enable the Kafka consumer to listen for messages.
    """
    logger.info("Starting Kafka consumer...")
    listen_to_kafka()
