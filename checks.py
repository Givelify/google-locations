"""Module used for the fuzzy checking functions"""

import re

from rapidfuzz import fuzz

from config import Config
from google_api_calls import call_autocomplete


def check_topmost(topmost, donee_info_gp):
    """Function to compare the topmost text search API response against the gp information in out database to verify it is the correct gp"""  # pylint: disable=line-too-long
    topmost_name = topmost["displayName"]["text"].lower()
    print(f"Checking topmost result {topmost_name} for: {donee_info_gp.name}")
    gp_name = donee_info_gp.name.lower()
    similarity_score = fuzz.ratio(gp_name, topmost_name)
    if similarity_score < Config.topmost_name_matching_threshold:
        print(
            f"Topmost name {topmost_name} does not match GP name {gp_name} as similarity score is {similarity_score}, skipping."
        )
        return False
    print(
        f"topmost result {topmost["displayName"]["text"]} with address {topmost["formattedAddress"]} matched giving partner name {donee_info_gp.name} with similarity score of {similarity_score}"
    )
    return True


# for now just go with the assumption that the topmost one is good if the name matches more than 90


def normalize_address(address):
    """the Normalization function is written to preprocesses the address strings,
    ensuring they are ready for comparision, and also to split the adderss
    into street, city, state and country components so that different
    weights can be used for each part of the address during comparision
    """
    country_replacements = {
        r"\b(?:United States of America|United States|America|U\.?S\.?A\.?|USA|US|U\.?S\.?)\b\.?": "USA",  # pylint: disable=line-too-long
        r"\b(BHS|Bahamas)": "Bahamas",
    }
    for pattern, replacement in country_replacements.items():
        address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
    address = address.lower()
    parsed_address = {}
    address_parts = address.split(", ")
    if len(address_parts) >= 4:
        parsed_address["street"] = ", ".join(address_parts[: (len(address_parts) - 3)])
        parsed_address["country"] = address_parts[-1]
        parsed_address["state"] = address_parts[-2]
        parsed_address["city"] = address_parts[-3]
    else:
        print(
            f"{address} not complete error"
        )  # add an error log here stating that the DB is missing city, state or country
        raise ValueError("address not complete error:")
    return parsed_address


# pylint: disable=too-many-locals


def fuzzy_address_check(api_address, gp_address):
    """Function that compares the address returned by autocomplete API
    and the gp address in our database"""
    try:
        preprocessed_api_address = normalize_address(api_address)
    except ValueError as e:
        raise ValueError(
            f"api_address: {api_address} {e}"
        ) from e  # error / exception already logged in normalize_address() function
    try:
        preprocessed_gp_address = normalize_address(gp_address)
    except ValueError as f:
        raise ValueError(
            f"api_address: {api_address} {f}"
        ) from f  # error / exception already logged in normalize_address() function

    # weights for different components of the address, we want to place more weight on street comparision pylint: disable=line-too-long
    street_weight = 0.5
    city_weight = 0.2
    state_weight = 0.2
    country_weight = 0.1

    # Extract components from normalized addresses
    api_street = preprocessed_api_address.get("street", "")
    api_city = preprocessed_api_address.get("city", "")
    api_state = preprocessed_api_address.get("state", "")
    api_country = preprocessed_api_address.get("country", "")

    gp_street = preprocessed_gp_address.get("street", "")
    gp_city = preprocessed_gp_address.get("city", "")
    gp_state = preprocessed_gp_address.get("state", "")
    gp_country = preprocessed_gp_address.get("country", "")

    # Calculate fuzzy scores for each component
    street_score = fuzz.ratio(api_street, gp_street) * street_weight
    city_score = fuzz.ratio(api_city, gp_city) * city_weight
    state_score = fuzz.ratio(api_state, gp_state) * state_weight
    country_score = fuzz.ratio(api_country, gp_country) * country_weight

    # Combine the weighted scores
    total_score = street_score + city_score + state_score + country_score

    return total_score


def autocomplete_check(donee_info_gp):
    """Function that calls the autocomplete api and then calls fuzzy check on each returned address
    against the gp address in our database to see if they match. If one of the hits match,
    it returns True"""
    gp_address = ", ".join(
        filter(
            None,
            [
                donee_info_gp.address,
                donee_info_gp.city,
                donee_info_gp.state,
                donee_info_gp.country,
            ],
        )
    )
    print(
        f"Autocomplete check for: {donee_info_gp.name}, address: {gp_address}"
    )  # log this message
    try:
        autocomplete_results = call_autocomplete(donee_info_gp)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error calling autocomplete API: {e}")  # error log this
        return False, ""
    if len(autocomplete_results) > 0:
        for suggestion in autocomplete_results.get("suggestions", []):
            autocomplete_address = (
                suggestion.get("placePrediction", {})
                .get("structuredFormat", {})
                .get("secondaryText", {})
                .get("text", "")
            )
            if autocomplete_address:
                try:
                    similarity_score = fuzzy_address_check(
                        autocomplete_address, gp_address
                    )
                except ValueError as e:  # pylint: disable=unused-variable
                    # Error log this, say skipping autocomplete check because of e
                    return False, ""
                print(
                    f"auto address: {autocomplete_address}, donee_info address: {gp_address}, sim_score: {similarity_score}"  # pylint: disable=line-too-long
                )
                if similarity_score > Config.autocomplete_address_matching_threshold:
                    return True, suggestion.get("placePrediction", {}).get(
                        "placeId", ""
                    )
    return False, ""  # log this stating autocomplete check failed for gp
