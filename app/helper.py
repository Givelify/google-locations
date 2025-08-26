"""Module that contains helper functions"""

from shapely.geometry import MultiPolygon, Polygon
from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.enums import FilterType
from app.models import (
    GivingPartners,
    GoogleGivingPartnerLocations,
    GoogleGivingPartnerOutlines,
)

logger = Config.logger


def insert_google_data(
    session,
    giving_partner_id,
    place_id,
    address,
    latitude,
    longitude,
    outlines,
):
    """Insert both location and outline data in a single transaction."""
    try:
        gp_location_data = GoogleGivingPartnerLocations(
            giving_partner_id=giving_partner_id,
            place_id=place_id,
            address=address,
            latitude=latitude,
            longitude=longitude,
        )
        session.merge(gp_location_data)
        if outlines:
            gp_outline_data = GoogleGivingPartnerOutlines(
                giving_partner_id=giving_partner_id,
                outlines=str(outlines),
            )
            session.merge(gp_outline_data)
            logger.info(
                "Prepared Google outline insert",
                value={"giving_partner_id": giving_partner_id},
            )

        session.commit()
        logger.info(
            "Succesfully inserted google data for Giving Partner",
            value={
                "giving_partner_id": str(giving_partner_id),
            },
        )
    except SQLAlchemyError as e:
        logger.error(f"sqlalchemy insertion error: {e}")
        raise


def insert_google_outlines(
    session,
    giving_partner_id,
    outlines,
):
    """Handles the MySQL table insertion"""
    try:
        gp_info = GoogleGivingPartnerOutlines(
            giving_partner_id=giving_partner_id,
            outlines=str(outlines),
        )
        session.merge(gp_info)
        session.commit()
        logger.info(
            "Succesfully inserted google outline data for Giving Partner",
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


def get_giving_partners(session, filter_type):
    """Function that returns which query to use to get the GPs to process"""
    gp_ids = [x.strip() for x in Config.GP_IDS.split(",") if x.strip()]
    if gp_ids:
        # Use provided GP IDs directly
        query = select(GivingPartners).where(GivingPartners.id.in_(gp_ids))
        logger.info("Retrieving GPs defined in GP_IDS", value={"gp_ids": str(gp_ids)})
    else:
        # Determine which join table to use
        join_table = (
            GoogleGivingPartnerLocations
            if filter_type == FilterType.LOCATION_AND_OUTLINES
            else GoogleGivingPartnerOutlines
        )

        query = (
            select(GivingPartners)
            .join(
                join_table,
                GivingPartners.id == join_table.giving_partner_id,
                isouter=True,
            )
            .where(
                and_(
                    join_table.giving_partner_id.is_(None),
                    *base_filter(),
                )
            )
            .limit(1)
        )

    return session.scalars(query).all()


def preprocess_building_outlines(outlines):
    """Returns the preprocessed building outlines co-ordinates as a geometry object"""
    shapely_geometry = None
    if outlines and len(outlines) > 0:
        coordinates = outlines["coordinates"]
        t = outlines.get("type", "").lower() if isinstance(outlines, dict) else ""
        try:
            if t == "polygon":
                shapely_geometry = Polygon(coordinates[0])
            elif t == "multipolygon":
                polygons = []
                for polygon_coords in coordinates:
                    exterior_ring = polygon_coords[0]
                    interior_rings = (
                        polygon_coords[1:] if len(polygon_coords) > 1 else None
                    )
                    polygons.append(Polygon(exterior_ring, interior_rings))

                shapely_geometry = MultiPolygon(polygons)
        except (ValueError, TypeError) as e:
            logger.error(f"Preprocessing geocoding API outlines failed: {e}")
            raise e
    if shapely_geometry:
        return shapely_geometry.wkt
    return None


def extract_building_polygons(data):
    """
    Recursively extract displayPolygon where structureType is 'BUILDING'
    """
    polygons = []

    if isinstance(data, dict):
        if data.get("structureType") == "BUILDING" and "displayPolygon" in data:
            polygons.append(data["displayPolygon"])
        # Recursively check all dictionary values
        for value in data.values():
            polygons.extend(extract_building_polygons(value))

    elif isinstance(data, list):
        for item in data:
            polygons.extend(extract_building_polygons(item))

    return polygons
