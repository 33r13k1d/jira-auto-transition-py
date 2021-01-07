from typing import Generator

import pytest
from aioresponses import aioresponses
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def aioresps() -> Generator:
    with aioresponses() as r:
        yield r
