"""json module for parsing the API responses"""

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("google_api_key")


def text_search(gp):
    """Function calling text search API"""
    gp_name = gp["name"]
    gp_city = gp["city"]
    gp_state = gp["state"]
    input_string = gp_name + ", " + gp_city + ", " + gp_state
    base_url = "https://places.googleapis.com/v1/places:searchText"

    params = {
        "X-Goog-Api-Key": api_key,
        "Content-Type": "application/json",
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location",
    }

    body = {
        "textQuery": input_string,
    }
    response = requests.post(
        base_url, headers=params, data=json.dumps(body), timeout=10
    )
    if response.status_code == 200:
        data = response.json()
    else:
        # include an error log here
        print(response.text)
        return None
    return data.get("places", [])


def call_autocomplete(gp):
    """function calling the Autocomplete API"""
    gp_name = gp["name"]
    base_url = "https://places.googleapis.com/v1/places:autocomplete"

    params = {"X-Goog-Api-Key": api_key, "Content-Type": "application/json"}

    body = {
        "input": gp_name,
    }

    if (gp["donee_lat"] and gp["donee_lat"] != 0) and (
        gp["donee_lon"] and gp["donee_lon"] != 0
    ):
        body["locationBias"] = {
            "circle": {
                "center": {"latitude": gp["donee_lat"], "longitude": gp["donee_lon"]},
                "radius": 50000.0,
            }
        }

    response = requests.post(
        base_url, headers=params, data=json.dumps(body), timeout=10
    )

    if response.status_code == 200:
        data = response.json()
    else:
        # include an ERROR log here
        print(response.text)
        return None

    return data
