from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, settings


def create_database_engine(app_settings: Settings = settings) -> Engine:
    database_url = app_settings.require_database_url()
    engine_kwargs = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs.update(
            {
                "pool_size": app_settings.database_pool_size,
                "max_overflow": app_settings.database_max_overflow,
                "pool_timeout": app_settings.database_pool_timeout_seconds,
                "pool_recycle": app_settings.database_pool_recycle_seconds,
            }
        )
    return create_engine(database_url, **engine_kwargs)


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
