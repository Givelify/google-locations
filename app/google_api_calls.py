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


@retry(
    wait=wait_exponential(multiplier=1, min=5, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(is_retryable),
)
def text_search(giving_partner):
    """Function calling text search API"""
    input_string = (
        giving_partner.name
        + ", "
        + giving_partner.city
        + ", "
        + giving_partner.state
        + ", "
        + giving_partner.country
    )
    base_url = "https://places.googleapis.com/v1/places:searchText"

    params = {
        "X-Goog-Api-Key": Config.GOOGLE_API_KEY,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location",
    }

    body = {
        "textQuery": input_string,
    }

    response = requests.post(
        base_url, headers=params, data=json.dumps(body), timeout=30
    )
    response.raise_for_status()
    data = response.json()
    return data.get("places", [])


@retry(
    wait=wait_exponential(multiplier=1, min=5, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(is_retryable),
)
def call_autocomplete(giving_partner):
    """function calling the Autocomplete API"""
    name = giving_partner.name
    autocomplete_url = "https://places.googleapis.com/v1/places:autocomplete"

    params = {
        "X-Goog-Api-Key": Config.GOOGLE_API_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "input": name,
    }

    if giving_partner.latitude and giving_partner.longitude:
        body["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": giving_partner.latitude,
                    "longitude": giving_partner.longitude,
                },
                "radius": 50000.0,
            }
        }

    response = requests.post(
        autocomplete_url, headers=params, data=json.dumps(body), timeout=30
    )
    response.raise_for_status()
    data = response.json()
    return data


def geocoding_api_coordinate(latitude, longitude):
    """Function calling text search API"""
    data = {
        "locationQuery": {"location": {"latitude": latitude, "longitude": longitude}}
    }

    return _call_geocoding_api(data)


def geocoding_api_id(place_id):
    """Function calling text search API"""
    data = {"place": f"places/{place_id}"}

    return _call_geocoding_api(data)


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
        if (
            isinstance(e, requests.HTTPError)
            and e.response is not None
            and e.response.status_code == 429
        ):
            logger.error(
                "429 Error while calling Google geocoding API",
                value={"params": {k: v for k, v in data.items() if k != "key"}},
                exc_info=True,
            )
        else:
            logger.error(
                "Google Geocoding API call failed",
                value={"params": {k: v for k, v in data.items() if k != "key"}},
                exc_info=True,
            )
        raise
