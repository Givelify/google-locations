"""Module that connects to mysql server and performs database operations"""

import os

from dotenv import load_dotenv
from sqlalchemy import MetaData, Table, and_, create_engine, insert, or_, select

from checks import autocomplete_check, check_topmost
from google_api_calls import text_search

load_dotenv()
username = os.getenv("database_username")
password = os.getenv("database_password")
host = os.getenv("host")
port = os.getenv("port")


def main():
    """Main module"""

    engine = create_engine(
        f"mysql+mysqlconnector://{username}:{password}@{host}:{port}/givelify"
    )
    metadata = MetaData()

    donee_info = Table("donee_info", metadata, autoload_with=engine)
    giving_partner_locations = Table(
        "giving_partner_locations",
        metadata,
        schema="platform",
        autoload_with=engine,
    )
    a = donee_info.alias("a")
    b = giving_partner_locations.alias("b")

    active = 1
    unregistered = 0

    query = (
        select(a)
        .select_from(a.outerjoin(b, a.c.donee_id == b.c.giving_partner_id))
        .where(
            or_(
                b.c.giving_partner_id is None,
                and_(
                    b.c.giving_partner_id is not None,
                    a.c.active == active,
                    a.c.unregistered == unregistered,
                ),
            )
        )
        .limit(1)
    )

    with engine.begin() as conn:
        result = conn.execute(query)
        dict_data = result.mappings().all()

        for gp in dict_data:
            print(
                f"Processing donee_id: {gp['donee_id']}, name: {gp['name']}, address: {gp['address']}"
            )
            process_gp(gp, conn, giving_partner_locations)
    engine.dispose()


def process_gp(gp, connection, gp_table):
    """Module that processes each GP"""
    autocomplete_result = autocomplete_check(gp)
    # autocomplete_result is a tuple of type (bool, place_id)
    if autocomplete_result[0]:
        gp_address = f"{gp['address']}, {gp['city']}, {gp['state']}, {gp['country']}"
        write_query = insert(gp_table).values(
            giving_partner_id=gp["donee_id"],
            phone_number=gp["phone"],
            address=gp_address,
            latitude=gp["donee_lat"],
            longitude=gp["donee_lon"],
            api_id=autocomplete_result[1],
            source="Google",
        )
        connection.execute(write_query)
        print(f"succesfully processed {gp["name"]}")  # log this sucessfull processing
        return True
    text_search_results = text_search(gp)
    if len(text_search_results) > 0:
        # get the topmost result from the text search assuming it is the right GP
        top_result = text_search_results[0]
        valid = check_topmost(top_result, gp)
        if not valid:
            print(
                f"not processed as the topmost result from text search {top_result["displayName"]["text"]} does not match gp name {gp["name"]}"  # pylint: disable=line-too-long
            )
            return False
        write_query = insert(gp_table).values(
            giving_partner_id=gp["donee_id"],
            phone_number=gp["phone"],
            address=top_result["formattedAddress"],
            latitude=top_result["location"]["latitude"],
            longitude=top_result["location"]["longitude"],
            api_id=top_result["id"],
            source="Google",
        )
        connection.execute(write_query)
        print(f"succesfully processed {gp["name"]}")  # log this sucessful processing
        return True
    print(
        "not processed as neither autocomplete check passed nor the topmost result from text search does not match"  # pylint: disable=line-too-long
    )  # log the failure to process the GP
    return False


if "__main__" == __name__:
    main()
