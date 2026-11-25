import os
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"


def load_dotenv_file(path: Path = ENV_FILE) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


load_dotenv_file()


@dataclass(frozen=True)
class Settings:
    app_name: str = "HubSmart Brainstorm"
    app_env: str = os.getenv("APP_ENV", "development").strip().lower()
    root_dir: Path = ROOT_DIR
    templates_dir: Path = ROOT_DIR / "templates"
    database_url: str | None = os.getenv("DATABASE_URL", "sqlite:///./hubsmart_brainstorm.db")
    test_database_url: str | None = os.getenv(
        "TEST_DATABASE_URL", "sqlite:///./hubsmart_brainstorm_test.db"
    )
    database_pool_size: int = _env_int("DATABASE_POOL_SIZE", 3)
    database_max_overflow: int = _env_int("DATABASE_MAX_OVERFLOW", 2)
    database_pool_timeout_seconds: int = _env_int("DATABASE_POOL_TIMEOUT_SECONDS", 10)
    database_pool_recycle_seconds: int = _env_int("DATABASE_POOL_RECYCLE_SECONDS", 1800)
    dev_user_email: str = os.getenv("DEV_USER_EMAIL", "dev@hubsmart.local")
    dev_user_name: str = os.getenv("DEV_USER_NAME", "HubSmart Dev")
    default_workspace_slug: str = os.getenv("DEFAULT_WORKSPACE_SLUG", "workspace-brainstorm")
    workspace_form_max_bytes: int = _env_int("WORKSPACE_FORM_MAX_BYTES", 256_000)
    workspace_form_max_fields: int = _env_int("WORKSPACE_FORM_MAX_FIELDS", 500)

    def require_database_url(self) -> str:
        if not self.database_url:
            raise RuntimeError("DATABASE_URL precisa estar definida para acessar o banco.")
        return self.database_url

    def require_test_database_url(self) -> str:
        if not self.test_database_url:
            raise RuntimeError("TEST_DATABASE_URL precisa estar definida para testes de banco.")
        return self.test_database_url


settings = Settings()
