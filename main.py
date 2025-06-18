"""Module that connects to mysql server and performs database operations"""

import os

from dotenv import load_dotenv
from sqlalchemy import and_, func, select

from checks import autocomplete_check, check_topmost
from google_api_calls import text_search
from models import GivingPartnerLocations, GivingPartners, get_engine, get_session

load_dotenv()
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


def main():
    """Main module"""

    engine = get_engine(DB_HOST, DB_PORT, DB_USERNAME, DB_PASSWORD, "platform")

    active = 1
    unregistered = 0

    gp = GivingPartners
    gpl = GivingPartnerLocations

    query = (
        select(gp)
        .join(gpl, gp.id == gpl.giving_partner_id, isouter=True)
        .where(
            and_(
                gpl.giving_partner_id.is_(None),
                gp.active == active,
                gp.unregistered == unregistered,
                gp.country.isnot(None),
                func.trim(gp.country) == "",
            )
        )
        .limit(3)
    )
    with get_session(engine) as session:
        result = session.scalars(query).all()
        for gp in result:
            print(
                f"Processing donee_id: {gp.id}, name: {gp.name}, address: {gp.address}, {gp.city}, {gp.state}, {gp.country}"  # pylint: disable=line-too-long
            )  # log this
            process_gp(gp, session, GivingPartnerLocations)
    engine.dispose()


def process_gp(gp, session, gp_table):
    """Module that processes each GP"""
    autocomplete_result = autocomplete_check(gp)
    # autocomplete_result is a tuple of type (bool, place_id)
    if autocomplete_result[0]:
        gp_address = f"{gp.address}, {gp.city}, {gp.state}, {gp.country}"
        gp_info = gp_table(
            giving_partner_id=gp.id,
            phone_number=gp.phone,
            address=gp_address,
            latitude=gp.latitude,
            longitude=gp.longitude,
            api_id=autocomplete_result[1],
            source="Google",
        )
        session.add(gp_info)
        session.commit()
        print(f"succesfully processed {gp.name}")  # log this sucessfull processing
        return True
    text_search_results = text_search(gp)
    if len(text_search_results) > 0:
        # get the topmost result from the text search assuming it is the right GP
        top_result = text_search_results[0]
        valid = check_topmost(top_result, gp)
        if not valid:
            print(
                f"not processed as the topmost result from text search {top_result["displayName"]["text"]} does not match gp name {gp.name}"  # pylint: disable=line-too-long
            )
            return False
        gp_info = gp_table(
            giving_partner_id=gp.id,
            phone_number=gp.phone,
            address=top_result["formattedAddress"],
            latitude=top_result["location"]["latitude"],
            longitude=top_result["location"]["longitude"],
            api_id=top_result["id"],
            source="Google",
        )
        session.add(gp_info)
        session.commit()
        print(f"succesfully processed {gp.name}")  # log this sucessful processing
        return True
    print(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )  # log the failure to process the GP
    return False


if "__main__" == __name__:
    main()
