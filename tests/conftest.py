import atexit
import os
import tempfile

_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_db_path}"
os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
atexit.register(os.remove, _db_path)

from unittest.mock import AsyncMock, patch  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with (
        patch("app.main.build_bot", return_value=object()),
        patch("app.main.start_polling", new=AsyncMock()),
        patch("app.main.stop_polling", new=AsyncMock()),
        TestClient(app) as test_client,
    ):
        yield test_client
