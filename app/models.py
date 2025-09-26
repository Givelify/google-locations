# pylint: disable=too-few-public-methods
"""datetime object for defining created_at, updated_at columns"""

from sqlalchemy import JSON, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import Config

Base = declarative_base()


class GivingPartnerOutlines(Base):
    """giving_partner_outlines table"""

    __tablename__ = "giving_partner_outlines"
    __table_args__ = {"schema": Config.PLATFORM_DB_DATABASE}

    giving_partner_id = Column(Integer, primary_key=True)
    outlines = Column(JSON, nullable=False)


class GivingPartners(Base):
    """giving_partners table"""

    __tablename__ = "donee_info"
    __table_args__ = {"schema": Config.MONO_DB_DATABASE}

    donee_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(55), nullable=False)
    state = Column(String(55), nullable=False)
    country = Column(String(50), nullable=True)
    zip = Column(String(10), nullable=False)
    donee_lat = Column(Float, nullable=False)
    donee_lon = Column(Float, nullable=False)
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
