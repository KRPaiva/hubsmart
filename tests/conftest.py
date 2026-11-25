import os
from pathlib import Path


def _bootstrap_test_environment() -> None:
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    test_db = os.getenv("TEST_DATABASE_URL")
    if test_db:
        os.environ["DATABASE_URL"] = test_db
    else:
        os.environ.setdefault("DATABASE_URL", "sqlite:///./hubsmart_brainstorm_test.db")


_bootstrap_test_environment()
