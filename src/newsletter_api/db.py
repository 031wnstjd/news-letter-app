from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import Settings


def get_engine():
    settings = Settings()
    return create_engine(settings.database_url, future=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
