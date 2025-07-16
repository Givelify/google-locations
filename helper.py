"""Module that contains helper functions"""

import argparse

from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from checks import check_topmost
from config import Config
from google_api_calls import geocoding_api
from models import GivingPartners as gp
from models import GoogleGivingPartnerLocations as gpl

logger = Config.logger


def insert_google_gp_location(  # pylint: disable=too-many-arguments, too-many-positional-arguments
    place_id,
    giving_partner_id,
    address,
    outlines,
    latitude,
    longitude,
    session,
):
    """Handles the MySQL table insertion"""
    try:
        gp_info = gpl(
            place_id=place_id,
            giving_partner_id=giving_partner_id,
            address=address,
            outlines=outlines,
            latitude=latitude,
            longitude=longitude,
        )
        session.add(gp_info)
        session.commit()
        logger.info(
            f"succesfully inserted google location data for gp_id: {giving_partner_id}"
        )
    except SQLAlchemyError as e:
        logger.error(f"sqlalchemy insertion error: {e}")
        raise


def base_filter(giving_partner, active, unregistered):
    "base filter to reuse in SELECT queries to retrieve GPs from donee_info DB"
    return [
        giving_partner.active == active,
        giving_partner.unregistered == unregistered,
        giving_partner.country.isnot(None),
        func.trim(giving_partner.country) != "",
    ]


def mysql_query(specific_gp_id):
    """Function that returns which query to use to get the GPs to process"""
    active = 1
    unregistered = 0
    if specific_gp_id is None:
        return (
            select(gp)
            .join(gpl, gp.id == gpl.giving_partner_id, isouter=True)
            .where(
                and_(
                    gpl.giving_partner_id.is_(None),
                    *base_filter(gp, active, unregistered),
                )
            )
            .limit(1)
        )
    return select(gp).where(
        and_(
            gp.id == specific_gp_id,
            *base_filter(gp, active, unregistered),
        )
    )


def parse_args():
    """function to parse optional giving partner id command line argument"""
    parser = argparse.ArgumentParser(
        description="optional giving partner id and enable autocomplete check toggle"
    )
    parser.add_argument("--id", type=int)

    parser.add_argument(
        "--enable_autocomplete",
        action="store_true",
        help="Enable autocomplete check",
        default=False,
    )
    parser.add_argument(
        "--disable_cache_check",
        action="store_false",
        dest="cache_check",
        default=True,
        help="Redis Cache check for non processed GP IDs",
    )
    try:
        args = parser.parse_args()
        return args
    except SystemExit:
        logger.error(
            "parsing command line arguments failed: please ensure you input '--enable_autocomplete' and/or 'id {ID}' and please make sure ID is an integer"  # pylint: disable=line-too-long
        )
        raise


def reverse_coordinates(coordinate_pairs):
    """Function to reverse convert coordinate format from [long, lat] to [lat, long] to help support correct MySQL insertion of the building outline polygons"""  # pylint: disable=line-too-long
    reversed_list = [reversed(coordinates) for coordinates in coordinate_pairs]
    return reversed_list


def preprocess_building_outlines(outlines):
    """Returns the preprocessed building outlines co-ordinates as a geometry object"""
    shapely_geometry = None
    if outlines and len(outlines) > 0:
        coordinates = outlines["coordinates"]
        t = outlines.get("type", "").lower() if isinstance(outlines, dict) else ""
        try:
            if t == "polygon":
                reversed_coordinates = reverse_coordinates(coordinates[0])
                shapely_geometry = Polygon(reversed_coordinates)
            elif t == "multipolygon":
                polygons = []
                for polygon_coords in coordinates:
                    reversed_coordinates = reverse_coordinates(polygon_coords[0])
                    exterior_ring = reversed_coordinates
                    interior_rings = (
                        reversed_coordinates[1:] if len(polygon_coords) > 1 else None
                    )
                    polygons.append(Polygon(exterior_ring, interior_rings))

                shapely_geometry = MultiPolygon(polygons)
        except (ValueError, TypeError) as e:
            logger.error(f"Preprocessing geocoding API outlines failed: {e}")
            raise e
    if shapely_geometry:
        return shapely_geometry.wkt
    return None


def autocomplete_branch(giving_partner, session, autocomplete_result):
    """Handles GP location retrieval using Autocomplete API logic"""
    gp_address = f"{giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
    preprocessed_outlines = None
    latitude = giving_partner.latitude
    longitude = giving_partner.longitude
    address = gp_address
    try:
        geocoding_result = geocoding_api(autocomplete_result)
        results = geocoding_result.get("results", [])
        if results and len(results) > 0:
            building_outlines = results[0]["buildings"][0]["building_outlines"][0][
                "display_polygon"
            ]
            preprocessed_outlines = preprocess_building_outlines(building_outlines)
            location = results[0]["geometry"]["location"]
            latitude = location["lat"]
            longitude = location["lng"]
            address = results[0]["formatted_address"]
        insert_google_gp_location(
            place_id=autocomplete_result,
            giving_partner_id=giving_partner.id,
            address=address,
            outlines=preprocessed_outlines,
            latitude=latitude,
            longitude=longitude,
            session=session,
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Failure in Automcomplete branch: {e}")
        raise


def text_search_branch(giving_partner, text_search_results, session):
    """Handles GP location retrieval using text search API"""
    # get the topmost result from the text search assuming it is the right GP
    top_result = text_search_results[0]
    if not check_topmost(top_result, giving_partner):
        logger.info(
            f"Text search run failed as the topmost result from text search {top_result["displayName"]["text"]} does not match gp name {giving_partner.name} with gp_id {giving_partner.id}"  # pylint: disable=line-too-long
        )
        return False
    preprocessed_outlines = None
    try:
        geocoding_result = geocoding_api(top_result["id"])
        results = geocoding_result.get("results", [])
        if results and len(results) > 0:
            building_outlines = results[0]["buildings"][0]["building_outlines"][0][
                "display_polygon"
            ]
            preprocessed_outlines = preprocess_building_outlines(building_outlines)
        insert_google_gp_location(
            top_result["id"],
            giving_partner.id,
            top_result["formattedAddress"],
            preprocessed_outlines,
            top_result["location"]["latitude"],
            top_result["location"]["longitude"],
            session,
        )
        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Failure in Text search logic: {e}")
        raise
