"""json module for parsing the google API responses"""

import json

import requests
from requests.exceptions import RequestException

from config import Config


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
            base_url, headers=params, data=json.dumps(body), timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get("places", [])
    except RequestException as e:
        raise RuntimeError(
            f"google places API call failed: {e}"
        ) from e  # error log this


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

    if (gp.latitude and gp.latitude != 0) and (gp.longitude and gp.longitude != 0):
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
    except RequestException as e:
        raise RuntimeError(
            f"google places API call failed: {e}"
        ) from e  # error log this
