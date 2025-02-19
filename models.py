from flask_sqlalchemy import SQLAlchemy

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

    id = db.Column(db.Integer, primary_key=True)
    x_value = db.Column(db.Float, nullable=False)
    y_value = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    thread_id = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        return {
            "x_value": self.x_value,
            "y_value": self.y_value,
            "name": self.name,
            "thread_id": self.thread_id,
        }
