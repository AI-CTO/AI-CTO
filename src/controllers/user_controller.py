from flask import Blueprint, jsonify, request
from models.models import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route("/add_user", methods=["POST"])
def add_user():
    try:
        data = request.get_json()
        new_user = User(**data)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User added!", "user": new_user.to_dict()}), 201
    except Exception as e:
        return jsonify({"error": "Failed to add user", "details": str(e)}), 500