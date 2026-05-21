from collections.abc import Generator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

engine = create_engine(
    get_settings().database_url,
    echo=get_settings().debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)


def init_db() -> None:
    # Import models so metadata is registered before create_all.
    from app.models import ledger, outbox  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
