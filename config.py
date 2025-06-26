# pylint: disable=too-few-public-methods
"""os module for getting env variables"""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """config file"""

    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_USER = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    TOPMOST_NAME_MATCHING_THRESHOLD = 90
    AUTOCOMPLETE_ADDRESS_MATCHING_THRESHOLD = 80
