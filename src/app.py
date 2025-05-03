"""
Module for setting up the application instance.
"""

#pylint: disable=redefined-outer-name
import os
from flask import Flask
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from routes import setup_routes
from db_utils import init_db

from models.models import db

load_dotenv()

def create_app(test_config=None):
    """
    Loads environment variables, sets up SQLAlchemy, configures Flask-Limiter,
    initializes the database schema, and registers routes.

    Args:
        test_config (dict, optional): Configuration overrides for testing.

    Returns:
        Flask: The configured Flask app instance.
    """
    app = Flask(__name__)
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["50 per hour"],
        storage_uri='memory://',
    )

    project_root = os.path.dirname(os.path.dirname(__file__))  # eli AI-CTO/ ####
    database_path = os.path.join(project_root, 'instance/default.db')  ###
    database_url = os.environ.get("SQLALCHEMY_DATABASE_URI", f"sqlite:///{database_path}")

    if test_config:
        app.config.update(test_config)
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)  # Initialize SQLAlchemy instance
    init_db(app)  # Create tables

    setup_routes(app, limiter)  # Register routes

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
