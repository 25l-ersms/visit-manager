import logging

from visit_manager.package_utils.settings import VisitManagerSettings

settings = VisitManagerSettings()

level = settings.LOG_LEVEL
# create logger
logger = logging.getLogger("visit_manager")
logger.setLevel(level)

ch = logging.StreamHandler()
ch.setLevel(level)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

ch.setFormatter(formatter)

logger.addHandler(ch)
