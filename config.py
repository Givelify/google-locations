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
    api_key = os.getenv("google_api_key")
    topmost_name_matching_threshold = 90
    autocomplete_address_matching_threshold = 80
