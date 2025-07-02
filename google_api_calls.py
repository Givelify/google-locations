"""json module for parsing the google API responses"""

import json

import requests
from requests.exceptions import RequestException
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import Config

logger = Config.logger


def is_retryable(exception):
    """function that returns whether the google api call error is a 429 error
    so that the call could be retried"""
    return (
        isinstance(exception, requests.HTTPError)
        and exception.response.status_code == 429
    )


@retry(
    wait=wait_exponential(multiplier=1, min=5, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(is_retryable),
)
def text_search(gp):
    """Function calling text search API"""
    gp_name = gp.name
    gp_city = gp.city
    gp_state = gp.state
    input_string = gp_name + ", " + gp_city + ", " + gp_state
    base_url = "https://places.googleapis.com/v1/places:searchText"

    params = {
        "X-Goog-Api-Key": Config.GOOGLE_API_KEY,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location",
    }

    body = {
        "textQuery": input_string,
    }
    try:
        response = requests.post(
            base_url, headers=params, data=json.dumps(body), timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])
    except requests.HTTPError as http_error:
        if http_error.response.status_code == 429:
            logger.error(
                f"429 Error while calling Google text search API: {http_error}"
            )
            raise http_error
        raise RuntimeError(
            f"google places API call HTTP error occured: {http_error}"
        ) from http_error
    except RequestException as e:
        raise RuntimeError(
            f"google places API call failed: {e}"
        ) from e  # error log this


@retry(
    wait=wait_exponential(multiplier=1, min=5, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(is_retryable),
)
def call_autocomplete(gp):
    """function calling the Autocomplete API"""
    gp_name = gp.name
    base_url = "https://places.googleapis.com/v1/places:autocomplete"

    params = {
        "X-Goog-Api-Key": Config.GOOGLE_API_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "input": gp_name,
    }

    if gp.latitude and gp.longitude:
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": gp.latitude, "longitude": gp.longitude},
                "radius": 50000.0,
            }
        }

    try:
        response = requests.post(
            base_url, headers=params, data=json.dumps(body), timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data
    except requests.HTTPError as http_error:
        if http_error.response.status_code == 429:
            logger.error(
                f"429 Error while calling Google text search API: {http_error}"
            )
            raise http_error
        raise RuntimeError(
            f"google places API call HTTP error occured: {http_error}"
        ) from http_error
    except RequestException as e:
        raise RuntimeError(
            f"google places API call failed: {e}"
        ) from e  # error log this
