from kafka import KafkaConsumer

from visit_manager.package_utils.logger_conf import logger

TOPIC = "test_topic"
BOOTSTRAP_SERVERS = ["broker:9092"]
GROUP_ID = "my-consumer-group"


def handle_message(message: str) -> None:
    logger.info(f"Processing message: {message}")


def listen_to_kafka() -> None:
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id=GROUP_ID,
        value_deserializer=lambda x: x.decode("utf-8"),
    )

    logger.info(f"Listening for messages on topic '{TOPIC}'...")
    for msg in consumer:
        handle_message(msg.value)


def enable_listen_to_kafka() -> None:
    """
    Enable the Kafka consumer to listen for messages.
    """
    logger.info("Starting Kafka consumer...")
    listen_to_kafka()
