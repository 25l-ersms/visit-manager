# import base64
# import datetime
# import json
# import time

# import google.auth
# import urllib3
# from google.auth.transport.urllib3 import Request

# import logging
# logger = logging.getLogger(__name__)
# logger.setLevel("INFO")
# ch = logging.StreamHandler()
# ch.setLevel("INFO")
# formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
# ch.setFormatter(formatter)
# logger.addHandler(ch)

# def encode(source):
#   """Safe base64 encoding."""
#   return base64.urlsafe_b64encode(source.encode('utf-8')).decode('utf-8').rstrip('=')

# class TokenProvider(object):
#   """
#   Provides OAuth tokens from Google Cloud Application Default credentials.
#   """

#   def __init__(self, **config):
#     logger.info("Init token provider")
#     self.credentials, _project = google.auth.default()
#     self.http_client = urllib3.PoolManager()
#     self.HEADER = json.dumps(dict(typ='JWT', alg='GOOG_OAUTH2_TOKEN'))
#     logger.info("Initialized token provider")

#   def get_credentials(self):
#     if not self.credentials.valid:
#       logger.info("Creds not valid, refreshing")
#       self.credentials.refresh(Request(self.http_client))
#     logger.info("Credentials valid")
#     return self.credentials

#   def get_jwt(self, creds):
#     token_data = dict(
#             exp=creds.expiry.timestamp(),
#             iat=datetime.datetime.now(datetime.timezone.utc).timestamp(),
#             iss='Google',
#             scope='kafka',
#             sub=creds.service_account_email,
#     )
#     return json.dumps(token_data)

#   def get_token(self):
#     logger.info("get_token called")
#     creds = self.get_credentials()
#     token = '.'.join([
#       encode(self.HEADER),
#       encode(self.get_jwt(creds)),
#       encode(creds.token)
#     ])

#     # compute expiry time explicitly
#     utc_expiry = creds.expiry.replace(tzinfo=datetime.timezone.utc)
#     expiry_seconds = (utc_expiry - datetime.datetime.now(datetime.timezone.utc)).total_seconds()

#     logger.info(repr(vars(creds)))

#     return token, time.time() + expiry_seconds

# import os

# import confluent_kafka

# TOPIC = "test_topic"
# BOOTSTRAP_SERVERS = os.environ["BOOTSTRAP"]
# GROUP_ID = os.getenv("KAFKA_GROUP_ID", "my-consumer-group")


# def handle_message(message: str) -> None:
#     logger.info(f"Processing message: {message}")


# def listen_to_kafka() -> None:
#     def get_token(*args, **kwargs):
#         logger.info(f"Args: {args}")
#         logger.info(f"Kwargs: {kwargs}")
#         token_provider = TokenProvider()
#         token = token_provider.get_token()
#         return token

#     logger.info("Using OAuth for authentication")
#     config = {
#         'bootstrap.servers': BOOTSTRAP_SERVERS,
#         'security.protocol': 'SASL_SSL',
#         'sasl.mechanisms': 'OAUTHBEARER',
#         #'sasl.oauthbearer.config': 'oauth_cb',
#         'oauth_cb': get_token,
#         'group.id': GROUP_ID,
#         'enable.auto.commit': True,
#         'auto.offset.reset': 'earliest',
#         #'log_level': 7,
#         #'logger': logger,
#         #'debug': 'all',
#     }
#     print(config)
#     logger.info("Creating consumer")
#     consumer = confluent_kafka.Consumer(config)

#     # trigger the oauth callback
#     consumer.poll(1.0)

#     logger.info("Created consumer, attempting to list topics")
#     topics = consumer.list_topics().topics
#     logger.info(f"Got topics: {topics}")
#     assert topics
#     consumer.subscribe([TOPIC])
#     logger.info(f"Listening for messages on topic '{TOPIC}'...")
#     while True:
#         msg = consumer.poll(1.0)
#         if msg is None:
#             logger.info("No messages")
#             continue
#         if msg.error():
#             logger.info(f"Error: {msg.error()}")
#             continue
#         handle_message(msg.value().decode("utf-8"))

# def enable_listen_to_kafka() -> None:
#     """
#     Enable the Kafka consumer to listen for messages.
#     """
#     logger.info("Starting Kafka consumer...")
#     listen_to_kafka()

# if __name__ == "__main__":
#     enable_listen_to_kafka()
