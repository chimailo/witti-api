import os

from flask import current_app

from src import create_app
from src.config import TestingConfig, ProductionConfig


def test_development_config(client):
    """Test create_app with development config."""
    app = create_app()
    assert current_app is not None
    assert app.config["SECRET_KEY"] == "top_secret"
    assert app.config["SQLALCHEMY_DATABASE_URI"] == \
        os.environ.get("DATABASE_DEV_URL")


def test_testing_config(client):
    """Test create_app with Test config."""
    app = create_app(config=TestingConfig)
    assert app.config["TESTING"] is True
    assert app.config["SECRET_KEY"] == "top_secret"
    assert app.config["ITEMS_PER_PAGE"] == 2
    assert app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] is False
    assert app.config["SQLALCHEMY_DATABASE_URI"] == \
        os.environ.get("DATABASE_TEST_URL")


def test_production_config(client):
    """Test create_app with development config."""
    app = create_app(config=ProductionConfig)
    assert len(app.config["SECRET_KEY"]) >= 64
    assert app.config["TESTING"] is False
    assert app.config["DEBUG"] is False
