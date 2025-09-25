# pylint: disable=too-few-public-methods
"""os module for getting env variables"""

import logging
import os
import sys

from dotenv import load_dotenv
from givelifylogging import StructuredLogger as slogger

load_dotenv()


class Config:
    """config file"""

    PLATFORM_DB_HOST_WRITE = os.getenv("PLATFORM_DB_HOST_WRITE")
    PLATFORM_DB_PORT = os.getenv("PLATFORM_DB_PORT")
    PLATFORM_DB_USERNAME = os.getenv("PLATFORM_DB_USERNAME")
    PLATFORM_DB_PASSWORD = os.getenv("PLATFORM_DB_PASSWORD")
    PLATFORM_DB_DATABASE = os.getenv("PLATFORM_DB_DATABASE")

    MONO_DB_DATABASE = os.getenv("MONO_DB_DATABASE")

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    GP_IDS = os.getenv("GP_IDS") or ""

    DAILY_ITERATION_LIMIT = int(os.getenv("DAILY_ITERATION_LIMIT", "1"))

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    stdout_handler = logging.StreamHandler(sys.stdout)
    logger = slogger.StructuredLogger.getLogger(
        "google-locations", LOG_LEVEL, stdout_handler
    )
