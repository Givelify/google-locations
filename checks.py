"""Module used for regex functions"""

import re

from rapidfuzz import fuzz

from google_api_calls import call_autocomplete


def check_topmost(topmost, donee_info_gp):
    """Function to compare the topmost text search API response against the gp information in out database to verify it is the correct gp"""
    print(f"Checking topmost result for: {donee_info_gp['name']}")
    return True


def normalize_address(address):
    """Function to preprocesses the address strings"""
    # convert country name to standard abb
    country_replacements = {
        r"\b(United States|United States of America | US | U\.S\.A\.?|U\.S\.|America)\b": "USA",
        r"\b(BHS|Bahamas)": "Bahamas",
    }
    for pattern, replacement in country_replacements.items():
        address = re.sub(pattern, replacement, address, flags=re.IGNORECASE)
    address = address.lower()
    return address


def fuzzy_address_check(api_address, gp_address):
    """Function that compares the address returned by autocomplete API and the gp address in our database"""
    preprocessed_api_address = normalize_address(api_address)
    preprocessed_gp_address = normalize_address(gp_address)
    return fuzz.ratio(preprocessed_api_address, preprocessed_gp_address)


def autocomplete_check(donee_info_gp):
    """Function that calls the autocomplete api and then calls fuzzy check on each returned address against the gp address in our database to see if they match"""
    gp_address = (
        donee_info_gp["address"]
        + ", "
        + donee_info_gp["city"]
        + ", "
        + donee_info_gp["state"]
        + ", "
        + donee_info_gp["country"]
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
                similarity_score = fuzzy_address_check(autocomplete_address, gp_address)
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
