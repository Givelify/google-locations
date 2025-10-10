"""Module that connects to mysql server and performs database operations"""

import sys

import sentry_sdk

from app.config import Config
from app.models import get_engine, get_session
from app.services.building_outlines import run_outlines

logger = Config.logger

sentry_sdk.init(
    dsn=Config.SENTRY_DSN,
    send_default_pii=True,
    environment=Config.APP_ENV,
)


def main():
    """Main module"""
    engine = None
    try:
        engine = get_engine(
            db_host=Config.PLATFORM_DB_HOST_WRITE,
            db_port=Config.PLATFORM_DB_PORT,
            db_user=Config.PLATFORM_DB_USERNAME,
            db_password=Config.PLATFORM_DB_PASSWORD,
            db_name=Config.PLATFORM_DB_DATABASE,
        )
        with get_session(engine) as session:
            run_outlines(session)
    except Exception:
        logger.error("Failed to update with Google data.", exc_info=True)
        return 1
    finally:
        if engine:
            engine.dispose()
    return 0


if "__main__" == __name__:
    sys.exit(main())
