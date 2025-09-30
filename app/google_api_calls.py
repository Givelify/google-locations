"""json module for parsing the google API responses"""

import requests
from requests.exceptions import RequestException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Config

logger = Config.logger


def is_retryable(exception):
    """function that returns whether the google api call error is a 429 error
    so that the call could be retried"""
    return (
        isinstance(exception, RequestException)
        and getattr(exception, "response", None) is not None
        and exception.response.status_code == 429
    )


def geocoding_api_address(address, city, state, zipcode, country):
    """Function calling text search API"""
    data = {
        "addressQuery": {
            "addressQuery": f"{address}, {city}, {state} {zipcode}, {country}"
        }
    }
    return _call_geocoding_api(data)


@retry(
    wait=wait_exponential(multiplier=1, min=5, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(is_retryable),
)
def _call_geocoding_api(data):
    """Internal function to call the Google Geocoding API with given params."""
    base_url = "https://geocode.googleapis.com/v4alpha/geocode/destinations"
    headers = {
        "X-Goog-Api-Key": Config.GOOGLE_API_KEY,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": "destinations.primary.place,destinations.primary.location,destinations.primary.structureType,destinations.primary.displayPolygon,destinations.containingPlaces",
    }
    try:
        response = requests.post(base_url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        params = {k: v for k, v in data.items() if k != "key"}

        if isinstance(e, requests.HTTPError) and e.response is not None:
            status = e.response.status_code

            if status == 429:
                logger.error(
                    "429 Error while calling Google geocoding API",
                    value={"params": params},
                    exc_info=True,
                )
                raise

            if status == 400:
                # Sometimes Google API returns 400 when the request body lacks info
                logger.warn(
                    "400 Error while calling Google geocoding API",
                    value={"params": params},
                    exc_info=True,
                )
                return None

        logger.error(
            "Google Geocoding API call failed",
            value={"params": params},
            exc_info=True,
        )
        raise
