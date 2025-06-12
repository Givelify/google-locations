import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("google_api_key")


def text_search(gp):
    gp_name = gp["name"]
    gp_city = gp["address"]
    gp_state = gp["state"]
    # Simulate a text search call
    print(f"Text search called for: {gp_name}, {gp_city}, {gp_state}")
    return


def call_autocomplete(gp):
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

    response = requests.post(base_url, headers=params, data=json.dumps(body))

    if response.status_code == 200:
        data = response.json()
    else:
        print("failed")  # include an ERROR log here
        print(response.text)

    return data
