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
    description = db.Column(db.String(255), nullable=False)
    returned_x_value = db.Column(db.Float, nullable=False)
    returned_y_value = db.Column(db.Float, nullable=False)
    impact = db.Column(db.Float, nullable=False)
    x_value_justification = db.Column(db.Text, nullable=False)
    y_value_justification = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    type = db.Column(
        db.Enum("existing", "idea", name="project_type_enum"), nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.description,
            "returned_x_value": self.returned_x_value,
            "returned_y_value": self.returned_y_value,
            "impact": self.impact,
            "x_value_justification": self.x_value_justification,
            "y_value_justification": self.y_value_justification,
            "type": self.type,
        }
