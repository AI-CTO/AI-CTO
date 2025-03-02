import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

import pytest

from src.app import create_app, init_db


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_app = create_app()
    test_app.config["TESTING"] = True
    test_app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    test_app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    yield test_app


@pytest.fixture
def client(app):
    """A test client for making requests."""
    return app.test_client()
