"""Module that contains helper functions"""

import argparse

from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from google_api_calls import geocoding_api
from models import GivingPartners, GoogleGivingPartnerLocations

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
        gp_info = GoogleGivingPartnerLocations(
            place_id=place_id,
            giving_partner_id=giving_partner_id,
            address=address,
            outlines=outlines,
            latitude=latitude,
            longitude=longitude,
        )
        session.merge(gp_info)
        session.commit()
        logger.info(
            "Succesfully inserted google location data for Giving Partner",
            value={
                "giving_partner_id": str(giving_partner_id),
            },
        )
    except SQLAlchemyError as e:
        logger.error(f"sqlalchemy insertion error: {e}")
        raise


def base_filter():
    "base filter to reuse in SELECT queries to retrieve GPs from donee_info DB"
    return [
        GivingPartners.active == 1,
        GivingPartners.unregistered == 0,
        GivingPartners.country.isnot(None),
        func.trim(GivingPartners.country) != "",
    ]


def get_giving_partners(session, specific_gp_id=None):
    """Function that returns which query to use to get the GPs to process"""
    if specific_gp_id is None:
        query = (
            select(GivingPartners)
            .join(
                GoogleGivingPartnerLocations,
                GivingPartners.id == GoogleGivingPartnerLocations.giving_partner_id,
                isouter=True,
            )
            .where(
                and_(
                    GoogleGivingPartnerLocations.giving_partner_id.is_(None),
                    *base_filter(),
                )
            )
            .limit(1)
        )
    else:
        query = select(GivingPartners).where(
            and_(
                GivingPartners.id == specific_gp_id,
                *base_filter(),
            )
        )
    return session.scalars(query).all()


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
    return parser.parse_args()


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


def process_autocomplete_results(session, giving_partner, place_id):
    """Handles GP location retrieval using Autocomplete API logic"""
    gp_address = f"{giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
    preprocessed_outlines = None
    latitude = giving_partner.latitude
    longitude = giving_partner.longitude
    address = gp_address
    try:
        geocoding_result = geocoding_api(place_id)
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
            place_id=place_id,
            giving_partner_id=giving_partner.id,
            address=address,
            outlines=preprocessed_outlines,
            latitude=latitude,
            longitude=longitude,
            session=session,
        )
    except Exception as e:
        logger.error(
            "Failure in process_autocomplete_results",
            value={
                "exception": str(e),
                "giving_partner_id": str(giving_partner.id),
            },
        )
        return False

    return True


def process_text_search_results(session, giving_partner, text_search_result):
    """Handles GP location retrieval using text search API"""
    preprocessed_outlines = None
    try:
        geocoding_result = geocoding_api(text_search_result["id"])
        results = geocoding_result.get("results", [])
        if results and len(results) > 0:
            building_outlines = results[0]["buildings"][0]["building_outlines"][0][
                "display_polygon"
            ]
            preprocessed_outlines = preprocess_building_outlines(building_outlines)
        insert_google_gp_location(
            text_search_result["id"],
            giving_partner.id,
            text_search_result["formattedAddress"],
            preprocessed_outlines,
            text_search_result["location"]["latitude"],
            text_search_result["location"]["longitude"],
            session,
        )
    except Exception as e:
        logger.error(f"Failure in Text search logic: {e}")
        raise
