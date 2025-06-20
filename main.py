"""Module that connects to mysql server and performs database operations"""

from sqlalchemy import and_, func, select
from sqlalchemy.exc import SQLAlchemyError

from checks import autocomplete_check, check_topmost
from config import Config
from google_api_calls import text_search
from models import GivingPartnerLocations as gpl
from models import GivingPartners as gp
from models import get_engine, get_session


def main():
    """Main module"""

    try:
        engine = get_engine(
            db_host=Config.DB_HOST,
            db_port=Config.DB_PORT,
            db_user=Config.DB_USER,
            db_password=Config.DB_PASSWORD,
            db_name=Config.DB_NAME,
        )
        # log the success
    except SQLAlchemyError as e:
        print(f"Failed to initialize database engine: {e}")  # error log this
        raise

    active = 1
    unregistered = 0

    query = (
        select(gp)
        .join(gpl, gp.id == gpl.giving_partner_id, isouter=True)
        .where(
            and_(
                gpl.giving_partner_id.is_(None),
                gp.active == active,
                gp.unregistered == unregistered,
                gp.country.isnot(None),
                func.trim(gp.country) != "",
            )
        )
        .limit(1)
    )
    try:
        with get_session(engine) as session:
            # log the success of creating the session
            result = session.scalars(query).all()
            for giving_partner in result:
                print(
                    f"Processing donee_id: {giving_partner.id}, name: {giving_partner.name}, address: {giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"  # pylint: disable=line-too-long
                )  # log this
                process_gp(giving_partner, session, gpl)
    except SQLAlchemyError as e:
        print(f"failed to create session: {e}")  # error log this
    engine.dispose()


def process_gp(giving_partner, session, gp_table):
    """Module that processes each GP"""
    autocomplete_result = autocomplete_check(giving_partner)
    # autocomplete_result is a tuple of type (bool, place_id)
    if autocomplete_result[0]:
        gp_address = f"{giving_partner.address}, {giving_partner.city}, {giving_partner.state}, {giving_partner.country}"
        gp_info = gp_table(
            giving_partner_id=giving_partner.id,
            phone_number=giving_partner.phone,
            address=gp_address,
            latitude=giving_partner.latitude,
            longitude=giving_partner.longitude,
            api_id=autocomplete_result[1],
            source="Google",
        )
        try:
            session.add(gp_info)
            session.commit()
            print(
                f"succesfully processed {giving_partner.name}"
            )  # log this sucessfull processing
        except SQLAlchemyError as e:
            print(f"sqlalchemy insertion error: {e}")  # error log this
            raise
        return True
    try:
        text_search_results = text_search(giving_partner)
    except RuntimeError as e:
        print(f"{e}")  # error log this
        raise

    if len(text_search_results) > 0:
        # get the topmost result from the text search assuming it is the right GP
        top_result = text_search_results[0]
        valid = check_topmost(top_result, giving_partner)
        if not valid:
            print(
                f"not processed as the topmost result from text search {top_result["displayName"]["text"]} does not match gp name {giving_partner.name}"  # pylint: disable=line-too-long
            )
            return False
        gp_info = gp_table(
            giving_partner_id=giving_partner.id,
            phone_number=giving_partner.phone,
            address=top_result["formattedAddress"],
            latitude=top_result["location"]["latitude"],
            longitude=top_result["location"]["longitude"],
            api_id=top_result["id"],
            source="Google",
        )
        try:
            session.add(gp_info)
            session.commit()
            print(
                f"succesfully processed {giving_partner.name}"
            )  # log this sucessful processing
        except SQLAlchemyError as e:
            print(f"sqlalchemy insertion error: {e}")  # error log this
            raise
        return True
    print(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )  # log the failure to process the GP
    return False


if "__main__" == __name__:
    main()
