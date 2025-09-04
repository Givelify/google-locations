"""Module containing service functions for the location and outlines path"""

from app.checks import autocomplete_check, text_search_similarity_check
from app.config import Config
from app.google_api_calls import geocoding_api_id, text_search
from app.helper import extract_building_polygons, insert_google_data

logger = Config.logger


def process_location_and_outlines(session, giving_partner):
    """Module that processes location and outlines each GP"""
    logger.info(
        "Processing location and outline for giving partner",
        value={
            "giving_partner_id": str(giving_partner.id),
        },
    )

    # Autocomplete checks if Google has matching location details.
    # If so, we skip the more expensive text search call.
    if Config.ENABLE_AUTOCOMPLETE:
        place_id = autocomplete_check(giving_partner)
        if place_id and process_autocomplete_results(session, giving_partner, place_id):
            logger.info(
                "Autocomplete process successful for GP",
                value={
                    "giving_partner_id": str(giving_partner.id),
                    "status": "success",
                },
            )
            return

    text_search_results = text_search(giving_partner)
    if not text_search_results:
        logger.info(
            "No text search results for GP",
            value={
                "giving_partner_id": str(giving_partner.id),
            },
        )
        return

    top_text_search_result = text_search_results[0]
    if text_search_similarity_check(giving_partner, top_text_search_result):
        process_text_search_results(session, giving_partner, top_text_search_result)
        logger.info(
            "Text search process successful for GP",
            value={"giving_partner_id": str(giving_partner.id), "status": "success"},
        )
    else:
        logger.info(
            "Top most text search result is not viable for GP",
            value={
                "giving_partner_id": str(giving_partner.id),
                "top_text_search_result": top_text_search_result,
            },
        )

    return


def process_autocomplete_results(session, giving_partner, place_id):
    """Handles GP location retrieval using Autocomplete API logic"""
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
    latitude = giving_partner.latitude
    longitude = giving_partner.longitude
    address = gp_address
    try:
        geocoding_result = geocoding_api_id(place_id)
        destinations = geocoding_result.get("destinations", [])
        building_outlines = extract_building_polygons(destinations)

        # retrieve location details from google api
        if destinations:
            primary = destinations[0].get("primary", {})

            location = primary.get("location")
            if location:
                latitude = location.get("latitude", latitude)
                longitude = location.get("longitude", longitude)

            formatted_address = primary.get("formattedAddress")
            if formatted_address:
                address = formatted_address

        insert_google_data(
            session,
            giving_partner.id,
            place_id,
            address,
            latitude,
            longitude,
            building_outlines,
        )
    except Exception:
        logger.error(
            "Failure in process_autocomplete_results",
            value={
                "giving_partner_id": str(giving_partner.id),
            },
            exc_info=True,
        )
        return False

    return True


def process_text_search_results(session, giving_partner, text_search_result):
    """Handles GP location retrieval using text search API"""
    try:
        geocoding_result = geocoding_api_id(text_search_result["id"])
        destinations = geocoding_result.get("destinations", [])
        building_outlines = extract_building_polygons(destinations)

        insert_google_data(
            session,
            giving_partner.id,
            text_search_result["id"],
            text_search_result["formattedAddress"],
            text_search_result["location"]["latitude"],
            text_search_result["location"]["longitude"],
            building_outlines,
        )
    except Exception:
        logger.error(
            "Failure in process_text_search_results",
            value={
                "giving_partner_id": str(giving_partner.id),
            },
            exc_info=True,
        )
