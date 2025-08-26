# pylint: disable=too-few-public-methods
"""datetime object for defining created_at, updated_at columns"""


from geoalchemy2 import Geometry
from sqlalchemy import Column, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class GoogleGivingPartnerLocations(Base):
    """google_giving_partner_locations table"""

    __tablename__ = "google_giving_partner_locations"

    giving_partner_id = Column(Integer, primary_key=True)
    place_id = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)


class GoogleGivingPartnerOutlines(Base):
    """google_giving_partner_outlines table"""

    __tablename__ = "google_giving_partner_outlines"

    giving_partner_id = Column(Integer, primary_key=True)
    outlines = Column(Text, nullable=False)


class GivingPartners(Base):
    """giving_partners table"""

    __tablename__ = "giving_partners"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(25), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(55), nullable=False)
    state = Column(String(55), nullable=False)
    country = Column(String(50), nullable=True)
    zip = Column(String(10), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    active = Column(Integer, nullable=False)
    unregistered = Column(Integer, nullable=False)


# Database setup function
def get_engine(db_host, db_port, db_user, db_password, db_name):
    """function to create the mysql engine"""
    connection_string = (
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    engine = create_engine(connection_string, pool_recycle=3600)
    return engine


# Session factory
def get_session(engine):
    """function to create the session for the mysql database"""
    session = sessionmaker(bind=engine)
    return session()
