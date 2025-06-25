"""
Module for database stuff.
"""

import os
from models.models import db

def init_db(app):
    """
    Initializes the database.

    Args:
        app (Flask): The Flask application
    """
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace("sqlite:///", "")
    print("Database path:", db_path)
    if not os.path.exists(db_path):
        with app.app_context():
            print("Creating new database", db_path)
            db.create_all()
    else:
        print("Already existing databtase, can't make new one:", db_path)
