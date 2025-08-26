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

    DB_HOST = os.getenv("PLATFORM_DB_HOST")
    DB_PORT = os.getenv("PLATFORM_DB_PORT")
    DB_USER = os.getenv("PLATFORM_DB_USERNAME")
    DB_PASSWORD = os.getenv("PLATFORM_DB_PASSWORD")
    DB_NAME = os.getenv("PLATFORM_DB_NAME")

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    GP_IDS = os.getenv("GP_IDS") or ""

    BUILDING_OUTLINES_ONLY = os.getenv("BUILDING_OUTLINES_ONLY", "true").lower() in (
        "true",
        "1",
        "t",
    )
    ENABLE_AUTOCOMPLETE = os.getenv("ENABLE_AUTOCOMPLETE", "true").lower() in (
        "true",
        "1",
        "t",
    )

    TEXT_SEARCH_MATCHING_THRESHOLD = 85
    AUTOCOMPLETE_MATCHING_THRESHOLD = 85

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    stdout_handler = logging.StreamHandler(sys.stdout)
    logger = slogger.StructuredLogger.getLogger(
        "google-locations", LOG_LEVEL, stdout_handler
    )
