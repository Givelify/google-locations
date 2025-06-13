"""Module used for regex functions"""

import re

from rapidfuzz import fuzz

from google_api_calls import call_autocomplete


def check_topmost(topmost, donee_info_gp):
    """Function to compare the topmost text search API response against the gp information in out database to verify it is the correct gp"""
    topmost_name = topmost["displayName"]["text"].lower()
    print(f"Checking topmost result {topmost_name} for: {donee_info_gp['name']}")
    # preprocess the strings
    gp_name = donee_info_gp["name"].lower()
    if fuzz.ratio(gp_name, topmost_name) < 90:
        print(
            f"Topmost name {topmost_name} does not match GP name {gp_name}, skipping."
        )
        return False
    return True


# for now just go with the assumption that the topmost one is good if the name matches more than 90


# function changed to place more weight on street part of address than country, city and state
# if len(addr) >= 4, get the last three parts split by ',' and return as dict with street, state, city, and country keys
def normalize_address(address):
    """Function to preprocesses the address strings"""
    # convert country name to standard abb
    country_replacements = {
        # r"\b(United States|United States of America|U(\.)?S(\.)?|U(\.)?S(\.)?A(\.)?|America)\b": "USA",
        r"\b(?:United States of America|United States|America|U\.?S\.?A\.?|USA|US|U\.?S\.?)\b\.?": "USA",
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
        print(f"{address} not complete error")
        raise ValueError("address not complete error:")
    return parsed_address


def fuzzy_address_check(api_address, gp_address):
    """Function that compares the address returned by autocomplete API and the gp address in our database"""
    try:
        preprocessed_api_address = normalize_address(api_address)
    except ValueError as e:
        raise ValueError(f"api_address: {api_address} {e}") from e
    try:
        preprocessed_gp_address = normalize_address(gp_address)
    except ValueError as e:
        raise ValueError(f"api_address: {api_address} {e}") from e

    # return fuzz.ratio(preprocessed_api_address, preprocessed_gp_address)
    # weights for different components of the address
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
    """Function that calls the autocomplete api and then calls fuzzy check on each returned address against the gp address in our database to see if they match"""
    gp_address = ", ".join(
        filter(
            None,
            [
                donee_info_gp.get("address"),
                donee_info_gp.get("city"),
                donee_info_gp.get("state"),
                donee_info_gp.get("country"),
            ],
        )
    )
    print(f"Autocomplete check for: {donee_info_gp['name']}, address: {gp_address}")
    try:
        autocomplete_results = call_autocomplete(donee_info_gp)
    except Exception as e:
        print(f"Error calling autocomplete API: {e}")
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
                except ValueError as e:
                    # TODO: Error log this, say skipping autocomplete check because of e
                    return False, ""
                print(
                    f"auto address: {autocomplete_address}, donee_info address: {gp_address}, sim_score: {similarity_score}"
                )
                if similarity_score > 80:
                    return True, suggestion.get("placePrediction", {}).get(
                        "placeId", ""
                    )
    return False, ""

    # test cases for this function:
    # check for GPs whose addresses cross 80 threshold
    # check for GPs whose addresses do not cross 80 but in fact have same addresses
    # check for GPs who do not have any matching address in autocomplete results
