"""
Module for user-related API routes.
The user functionality has not yet been implemented in the application
"""

from flask import Blueprint, jsonify, request
from models.models import db, User

user_bp = Blueprint('user', __name__)

@user_bp.route("/add_user", methods=["POST"])
def add_user():
    """Function for creating a user

    Returns:
        JSON message
    """
    try:
        data = request.get_json()
        new_user = User(**data)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User added!", "user": new_user.to_dict()}), 201
    except Exception as e: # pylint: disable=broad-except
        return jsonify({"error": "Failed to add user", "details": str(e)}), 500
