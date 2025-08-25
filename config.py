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

    DB_HOST = os.getenv("PLATFORM_DB_HOST_WRITE")
    DB_PORT = os.getenv("PLATFORM_DB_PORT")
    DB_USER = os.getenv("PLATFORM_DB_USERNAME")
    DB_PASSWORD = os.getenv("PLATFORM_DB_PASSWORD")
    DB_NAME = os.getenv("PLATFORM_DB_NAME")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    TEXT_SEARCH_MATCHING_THRESHOLD = 90
    AUTOCOMPLETE_MATCHING_THRESHOLD = 90
    GP_IDS = os.getenv("GP_IDS", None)
    LOG_LEVEL= os.getenv("LOG_LEVEL", "DEBUG")
    BUILDING_OUTLINES_ONLY= os.getenv("BUILDING_OUTLINES_ONLY", "false").lower() in ('true', '1', 't')
    stdout_handler = logging.StreamHandler(sys.stdout)
    logger = slogger.StructuredLogger.getLogger(
        "google-locations", LOG_LEVEL, stdout_handler
    )
