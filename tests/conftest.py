import os

os.environ["ENABLE_BACKGROUND_JOBS"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.features.catalog import service as catalog_service  # noqa: E402
from app.features.devices import repository as devices_repo  # noqa: E402
from app.features.notification import notice_watch  # noqa: E402
from app.features.notification import service as notification_service  # noqa: E402
from app.features.centers import service as centers_service  # noqa: E402
from app.features.forwarding import repository as forwarding_repo  # noqa: E402
from app.features.hooks import service as hooks_service  # noqa: E402
from app.features.mailbox import repository as mailbox_repo  # noqa: E402
from app.features.reservation import repository as reservation_repo  # noqa: E402
from app.features.stock import repository as stock_repo  # noqa: E402
from app.features.subscription import repository as subscription_repo  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def _reset():
    for repo in (stock_repo, mailbox_repo, reservation_repo, subscription_repo, forwarding_repo, hooks_service,
                 devices_repo, notification_service, notice_watch):
        repo.reset()
    catalog_service._cache.clear()
    centers_service._centers_cache.clear()
    centers_service._calendar_cache.clear()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
