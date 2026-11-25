import os
import unittest
from pathlib import Path


def load_test_env() -> None:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_test_env()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or "sqlite:///./hubsmart_brainstorm_test.db"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import engine as app_engine
from app.db import get_db
from app.main import create_app
from app.models import Base
from app.services.bootstrap import ensure_dev_context

SAFE_TEST_DATABASE_NAME_FRAGMENTS = ("test", "pytest", "ci")


def assert_safe_test_database_url(database_url: str | None = TEST_DATABASE_URL) -> str:
    if not database_url:
        raise RuntimeError("TEST_DATABASE_URL precisa estar definida para testes com banco real.")
    url = make_url(database_url)
    database_name = (url.database or "").lower()
    if not any(fragment in database_name for fragment in SAFE_TEST_DATABASE_NAME_FRAGMENTS):
        raise RuntimeError("TEST_DATABASE_URL precisa apontar para um banco descartável de teste.")
    return database_url


def create_test_engine():
    database_url = assert_safe_test_database_url(settings.require_test_database_url())
    engine_kwargs = {}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **engine_kwargs)


def create_test_sessionmaker(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def reset_test_database(engine) -> None:
    app_engine.dispose()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


class DatabaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = create_test_engine()
        cls.SessionLocal = create_test_sessionmaker(cls.engine)

    @classmethod
    def tearDownClass(cls) -> None:
        app_engine.dispose()
        cls.engine.dispose()

    def setUp(self) -> None:
        reset_test_database(self.engine)
        self.db = self.SessionLocal()
        self.user, self.workspace = ensure_dev_context(self.db)
        self.user_id = self.user.id
        self.workspace_id = self.workspace.id

    def tearDown(self) -> None:
        self.db.close()

    def make_client(self) -> TestClient:
        app = create_app()

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        return TestClient(app)
