# pylint: disable=too-many-locals
"""Module used for the fuzzy checking functions"""

import re

from rapidfuzz import fuzz

from app.config import Config
from app.google_api_calls import call_autocomplete

logger = Config.logger


def text_search_similarity_check(giving_partner, text_search_result):
    """Function to compare the topmost text search API response against
    the gp information in our database to verify it is the correct gp"""
    text_search_name = text_search_result["displayName"]["text"].lower()
    gp_name = giving_partner.name.lower()
    similarity_score = fuzz.ratio(gp_name, text_search_name)
    logger.info(
        "Checking topmost result in text search",
        value={
            "giving_partner_id": str(giving_partner.id),
            "giving_partner_name": gp_name,
            "text_search_name": text_search_name,
            "similarity_score": str(similarity_score),
        },
    )
    return similarity_score > Config.TEXT_SEARCH_MATCHING_THRESHOLD


def normalize_address(address):
    """the Normalization function is written to preprocesses the address strings,
    ensuring they are ready for comparision, and also to split the adderss
    into street, city, state and country components so that different
    weights can be used for each part of the address during comparision
    """
    original_address = address
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
        raise ValueError(f"Incomplete address: {original_address}")
    return parsed_address


def autocomplete_name_fuzzy_check(gp_id, gp_name, api_name):
    """Function that compares the name returned by autocomplete API
    with gp data in our database"""
    gp_name = gp_name.lower()
    name_score = fuzz.ratio(gp_name, api_name)
    logger.info(
        "Autocomplete name fuzzy check results",
        value={
            "giving_partner_id": str(gp_id),
            "giving_partner_name": gp_name,
            "api_name": api_name,
            "name_score": str(name_score),
        },
    )
    return name_score


def autocomplete_address_fuzzy_check(gp_id, gp_address, api_address):
    """Function that compares the address returned by autocomplete API
    with gp data in our database"""
    try:
        preprocessed_api_address = normalize_address(api_address)
        preprocessed_gp_address = normalize_address(gp_address)
    except ValueError as e:
        raise ValueError(f"Error normalizing address {e}") from e

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
    address_score = street_score + city_score + state_score + country_score

    logger.info(
        "Autocomplete address fuzzy check results",
        value={
            "giving_partner_id": str(gp_id),
            "giving_partner_address": gp_address,
            "api_address": api_address,
            "address_score": str(address_score),
        },
    )

    return address_score


def autocomplete_check(giving_partner):
    """Function that calls the autocomplete api and then calls fuzzy check on each returned address
    against the gp address in our database to see if they match. If one of the hits match,
    it returns True"""
    gp_address = ", ".join(
        filter(
            None,
            [
                giving_partner.address,
                giving_partner.city,
                giving_partner.state,
                giving_partner.country,
            ],
        )
    )
    try:
        logger.info(
            "Running Autocomplete check",
            value={"giving_partner_id": str(giving_partner.id)},
        )
        autocomplete_results = call_autocomplete(giving_partner)
    except Exception:
        logger.error(
            "Google Autocomplete API call failed",
            value={
                "giving_partner_id": str(giving_partner.id),
            },
            exc_info=True,
        )
        return None

    if len(autocomplete_results) > 0:
        for suggestion in autocomplete_results.get("suggestions", []):
            autocomplete_address = (
                suggestion.get("placePrediction", {})
                .get("structuredFormat", {})
                .get("secondaryText", {})
                .get("text", "")
            )
            autocomplete_name = (
                suggestion.get("placePrediction", {})
                .get("structuredFormat", {})
                .get("mainText", {})
                .get("text", "")
            )
            if not (autocomplete_address and autocomplete_name):
                continue

            try:
                name_score = autocomplete_name_fuzzy_check(
                    giving_partner.id,
                    giving_partner.name,
                    autocomplete_name,
                )

                if name_score <= Config.AUTOCOMPLETE_MATCHING_THRESHOLD:
                    continue

                address_score = autocomplete_address_fuzzy_check(
                    giving_partner.id,
                    gp_address,
                    autocomplete_address,
                )

                if address_score <= Config.AUTOCOMPLETE_MATCHING_THRESHOLD:
                    continue

                return suggestion.get("placePrediction", {}).get("placeId", None)

            except Exception:
                logger.warn(
                    "Skipping suggestion due to autocomplete fuzzy check error",
                    value={
                        "giving_partner_id": str(giving_partner.id),
                    },
                    exc_info=True,
                )
                continue
    logger.info(
        "Autocomplete check unable to return any viable results",
        value={
            "giving_partner_id": str(giving_partner.id),
        },
    )
    return None
