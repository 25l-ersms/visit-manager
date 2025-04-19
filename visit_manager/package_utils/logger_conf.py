import logging
import os

level = os.getenv("VISIT_MANAGER_LOG_LEVEL", "INFO").upper()
# create logger
logger = logging.getLogger("visit_manager")
logger.setLevel("INFO")

ch = logging.StreamHandler()
ch.setLevel("INFO")

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

ch.setFormatter(formatter)

logger.addHandler(ch)
