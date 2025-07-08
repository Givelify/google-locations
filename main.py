"""Module that connects to mysql server and performs database operations"""

import argparse

from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from checks import autocomplete_check, check_topmost
from config import Config
from google_api_calls import geocoding_api, text_search
from models import GivingPartnerLocations as gpl
from models import GivingPartners as gp
from models import get_engine, get_session

logger = Config.logger


def reverse_coordinates(coordinate_pairs):
    """Function to reverse convert coordinate format from [long, lat] to [lat, long] to help support correct MySQL insertion of the building outline polygons"""  # pylint: disable=line-too-long
    reversed_list = []
    for coordinates in coordinate_pairs:
        reversed_list.append(reversed(coordinates))
    return reversed_list


def preprocess_building_outlines(building_outlines):
    """Returns the building outlines co-ordinates as a geometry object"""
    shapely_geometry = None
    if building_outlines and len(building_outlines) > 0:
        coordinates = building_outlines["coordinates"]
        try:
            if building_outlines["type"].lower() == "polygon":
                reversed_coordinates = reverse_coordinates(coordinates[0])
                shapely_geometry = Polygon(reversed_coordinates)
            elif building_outlines["type"].lower() == "multipolygon":
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
            logger.error(e)
            raise e

    if shapely_geometry is not None:
        return shapely_geometry.wkt
    return None


def base_filter(giving_partner, active, unregistered):
    "base filter to reuse in SELECT queries to retrieve GPs from donee_info DB"
    return [
        giving_partner.active == active,
        giving_partner.unregistered == unregistered,
        giving_partner.country.isnot(None),
        func.trim(giving_partner.country) != "",
    ]


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
    try:
        args = parser.parse_args()
    except SystemExit:
        logger.error(
            "parsing command line arguments failed: please ensure you input '--enable_autocomplete' and/or 'id {ID}' and please make sure ID is an integer"  # pylint: disable=line-too-long
        )
        raise
    return args


def main():
    """Main module"""
    try:
        args = parse_args()

        engine = get_engine(
            db_host=Config.DB_HOST,
            db_port=Config.DB_PORT,
            db_user=Config.DB_USER,
            db_password=Config.DB_PASSWORD,
            db_name=Config.DB_NAME,
        )
        # log success
    except SystemExit:
        logger.error("parsing args failed")
        raise
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database engine: {e}")  # error log this
        raise
    active = 1
    unregistered = 0

    if args.id is None:
        query = (
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
    else:
        query = select(gp).where(
            and_(
                gp.id == args.id,
                *base_filter(gp, active, unregistered),
            )
        )
    try:
        with get_session(engine) as session:
            # log the success of creating the session
            result = session.scalars(query).all()
            if len(result) == 0:
                if args.id is None:
                    logger.info("No Giving partners left to process")
                    return
                logger.info(
                    f"No active and unregistered GP exists with the provided id: {args.id} in the donee_info / giving patners table"  # pylint: disable=line-too-long
                )
                return
            for giving_partner in result:
                logger.info(
                    f"Processing donee_id: {giving_partner.id}, name: {giving_partner.name}, address: {giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
                )
                try:
                    process_gp(
                        giving_partner,
                        session,
                        autocomplete_toggle=args.enable_autocomplete,
                    )
                except (KeyError, TypeError) as e:
                    logger.error(f"Error in process_gp(): {e}")
    except SQLAlchemyError as e:
        logger.error(f"failed to create session: {e}")
    finally:
        engine.dispose()


def process_gp(giving_partner, session, autocomplete_toggle=False):
    """Module that processes each GP"""
    if autocomplete_toggle:
        autocomplete_result = autocomplete_check(giving_partner)
        if autocomplete_result:
            gp_address = f"{giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
            try:
                geocoding_result = geocoding_api(autocomplete_result)
                results = geocoding_result.get("results", [])
                if results and len(results) > 0:
                    building_outlines = results[0]["buildings"][0]["building_outlines"][
                        0
                    ]["display_polygon"]
                    preprocessed_outlines = preprocess_building_outlines(
                        building_outlines
                    )
                    location = results[0]["geometry"]["location"]
                    latitude = location["lat"]
                    longitude = location["lng"]
                    address = results[0]["formatted_address"]
                else:
                    raise RuntimeError
            except RuntimeError:
                preprocessed_outlines = None
                latitude = giving_partner.latitude
                longitude = giving_partner.longitude
                address = gp_address
            try:
                gp_info = gpl(
                    place_id=autocomplete_result,
                    giving_partner_id=giving_partner.id,
                    address=address,
                    outlines=preprocessed_outlines,
                    latitude=latitude,
                    longitude=longitude,
                )
                session.add(gp_info)
                session.commit()
                logger.info(f"succesfully processed {giving_partner.name}")
            except SQLAlchemyError as e:
                logger.error(f"sqlalchemy insertion error: {e}")
                raise
            return
    else:
        logger.error(
            "skipping autocomplete check as autocomplete was not toggled on using 'enable_autocomplete'"  # pylint: disable=line-too-long
        )
    try:
        text_search_results = text_search(giving_partner)
    except Exception as e:
        logger.error(f"Error calling google text search API: {e}")
        raise
    if len(text_search_results) > 0:
        # get the topmost result from the text search assuming it is the right GP
        top_result = text_search_results[0]
        if not check_topmost(top_result, giving_partner):
            logger.info(
                f"not processed as the topmost result from text search {top_result["displayName"]["text"]} does not match gp name {giving_partner.name}"  # pylint: disable=line-too-long
            )
            return
        preprocessed_outlines = None
        try:
            geocoding_result = geocoding_api(top_result["id"])
            results = geocoding_result.get("results", [])
            if results and len(results) > 0:
                building_outlines = results[0]["buildings"][0]["building_outlines"][0][
                    "display_polygon"
                ]
                preprocessed_outlines = preprocess_building_outlines(building_outlines)
        except (RuntimeError, ValueError, TypeError) as e:
            logger.error(
                f"Error retrieving building outlines for gp_id: {giving_partner.id}: {e}"
            )
            preprocessed_outlines = None
        try:
            gp_info2 = gpl(
                place_id=top_result["id"],
                giving_partner_id=giving_partner.id,
                address=top_result["formattedAddress"],
                outlines=preprocessed_outlines,
                latitude=top_result["location"]["latitude"],
                longitude=top_result["location"]["longitude"],
            )
            session.add(gp_info2)
            session.commit()
            logger.info(f"succesfully processed {giving_partner.name}")
        except (SQLAlchemyError, KeyError, TypeError) as e:
            logger.error(f"Insertion failed for {giving_partner.name}: {e}")
            raise
        return
    logger.info(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )
    return


if "__main__" == __name__:
    main()
