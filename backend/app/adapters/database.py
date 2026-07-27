from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import Settings


class Base(DeclarativeBase):
    pass


def create_database_engine(settings: Settings) -> Engine:
    return create_engine(settings.database_url)


def create_session_factory(settings: Settings) -> sessionmaker[Session]:
    return sessionmaker(create_database_engine(settings), expire_on_commit=False)
