from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role,
            "name": self.name,
            "email": self.email,
        }


class Project(db.Model):
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
        return {
            "id": self.id,
            "x_value": self.x_value,
            "y_value": self.y_value,
            "impact": self.impact,
            "name": self.name,
            "thread_id": self.thread_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "project_type": self.project_type,  # Include project_type
        }
