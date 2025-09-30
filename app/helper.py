"""Module that contains helper functions"""

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.config import Config
from app.models import GivingPartnerOutlines, GivingPartners

logger = Config.logger


def insert_google_data(
    session,
    giving_partner,
    latitude,
    longitude,
    outlines,
):
    """Insert both location and outline data in a single transaction."""
    try:
        giving_partner.donee_lat = latitude
        giving_partner.donee_lon = longitude

        if outlines:
            gp_outline_data = GivingPartnerOutlines(
                giving_partner_id=giving_partner.donee_id,
                outlines=outlines,
            )
            session.merge(gp_outline_data)
        else:
            logger.info(
                "Unable to find outlines for giving partner",
                value={
                    "giving_partner_id": str(giving_partner.donee_id),
                },
            )

        session.commit()
        logger.info(
            "Succesfully inserted google data for Giving Partner",
            value={
                "giving_partner_id": str(giving_partner.donee_id),
            },
        )
    except SQLAlchemyError:
        session.rollback()
        logger.error(
            "Error inserting google data",
            value={
                "giving_partner_id": str(giving_partner.donee_id),
            },
        )
        raise


def insert_google_outlines(
    session,
    giving_partner_id,
    outlines,
):
    """Handles the MySQL table insertion"""
    try:
        gp_info = GivingPartnerOutlines(
            giving_partner_id=giving_partner_id,
            outlines=outlines,
        )
        session.merge(gp_info)
        session.commit()
        logger.info(
            "Succesfully inserted google outline data for Giving Partner",
            value={
                "giving_partner_id": str(giving_partner_id),
            },
        )
    except SQLAlchemyError:
        session.rollback()
        logger.error(
            "Error inserting google outlines",
            value={
                "giving_partner_id": str(giving_partner_id),
            },
        )
        raise


def get_giving_partners(session, gp_ids=None):
    """Function that returns which query to use to get the GPs to process"""
    if gp_ids:
        query = select(GivingPartners).where(GivingPartners.donee_id.in_(gp_ids))
        logger.info("Retrieving GPs defined in GP_IDS", value={"gp_ids": str(gp_ids)})
    else:
        query = (
            select(GivingPartners)
            .where(GivingPartners.donee_lat == 0)
            .limit(Config.DAILY_ITERATION_LIMIT)
        )

    return session.scalars(query).all()


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


def get_lat_lon(data):
    """Extracts the first coordinate from list of destinations"""
    return (
        (
            data[0].get("primary", {}).get("location", {}).get("latitude", -1),
            data[0].get("primary", {}).get("location", {}).get("longitude", -1),
        )
        if data
        else (-1, -1)
    )
