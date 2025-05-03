
"""
Database models to represent application users and projects
"""

#pylint: disable=too-few-public-methods

from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class User(db.Model):
    """
    Represents a user in the system

    Attributes:
        id (int): Primary key
        role (str): Role of the user
        name (str): Name of user
        email (str): Unique email address
    """

    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self):
        """
        Converts user class instance to dictionary.

        Returns:
            dict: Dictionary with user data.
        """
        return {
            "id": self.id,
            "role": self.role,
            "name": self.name,
            "email": self.email,
        }

class Project(db.Model):
    """
    Represents a project or project idea submitted by a user.

    Attributes:
        d (int): Primary key.
        x_value (decimal): X-axis value
        y_value (decimal): Y-axis value
        impact (decimal): Impact score
        name (str): Name of the project
        thread_id (str): Unique ID for thread
        timestamp (datetime): Timestamp of creation or last update
        type (str): Type of the project

    """
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    x_value = db.Column(db.Numeric, nullable=False)
    y_value = db.Column(db.Numeric, nullable=False)
    impact = db.Column(db.Numeric, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    thread_id = db.Column(db.String, nullable=False, unique=True)
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    type = db.Column(db.String, nullable=False, default="Idea")  # New field

    def to_dict(self):
        """
        Converts project class instance to a dictionary.

        Returns:
            dict: Dictionary with project data.
        """

        return {
            "id": self.id,
            "x_value": self.x_value,
            "y_value": self.y_value,
            "impact": self.impact,
            "name": self.name,
            "thread_id": self.thread_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "project_type": self.type,
        }
