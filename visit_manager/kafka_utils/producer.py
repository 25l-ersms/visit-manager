import json
from confluent_kafka import Producer # type: ignore[import-untyped]
from visit_manager.package_utils.settings import KafkaSettings


class KafkaProducerClient:
    """
    Client for sending events to Kafka using configuration from KafkaSettings.
    """

    def __init__(self) -> None:
        cfg = KafkaSettings()
        self._producer = Producer(
            {
                "bootstrap.servers": cfg.BOOTSTRAP_URL,
                "enable.idempotence": True, # ensures exactly-once delivery
                "acks": "all",
                "retries": 5,
            }
        )

    def send_user_registered(self, user_id: str, email: str, role: str) -> None:
        """
        Send a 'users.registered' event containing basic information about a new user.
        :param user_id: UUID of the user as a string
        :param email: Email address of the registered user
        :param role: Role of the user, e.g., "client" or "vendor"
        """
        topic = "users.registered"
        payload = {"user_id": user_id, "email": email, "role": role}
        self._producer.produce(topic, key=user_id, value=json.dumps(payload))
        self._producer.flush()

    def send_visit_registered(self, visit_id: str, payload: dict) -> None:
        """
        Send a 'visits.registered' event containing details of a newly created visit.
        :param visit_id: UUID of the visit as a string
        :param payload: Dictionary of visit details (same structure as the request body)
        """
        topic = "visits.registered"
        self._producer.produce(topic, key=visit_id, value=json.dumps(payload))
        self._producer.flush()

    def send_vendor_rating_updated(self, vendor_id: str, new_avg: float) -> None:
        """
        Send a 'vendors.rating_updated' event with the vendor's updated average rating.
        :param vendor_id: UUID of the vendor as a string
        :param new_avg: New average rating of the vendor (float)
        """
        topic = "vendors.rating_updated"
        payload = {"vendor_id": vendor_id, "new_avg": new_avg}
        self._producer.produce(topic, key=vendor_id, value=json.dumps(payload))
        self._producer.flush()
