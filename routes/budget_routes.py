from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt

budget_bp = Blueprint('budgets', __name__)

@budget_bp.route('/api/budgets', methods=['POST'])
@jwt_required()
def create_or_update_budget():
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can manage budgets."}), 403

    data = request.get_json()
    event_id = data.get("event_id")
    total_allocated = data.get("total_allocated")
    categories = data.get("categories", {})
    spent = data.get("spent", 0)

    if not event_id or total_allocated is None:
        return jsonify({"error": "event_id and total_allocated are required."}), 400

    budget_data = {
        "event_id": event_id,
        "total_allocated": float(total_allocated),
        "spent": float(spent),
        "remaining": float(total_allocated) - float(spent),
        "categories": categories
    }

    mongo.db.budgets.update_one(
        {"event_id": event_id},
        {"$set": budget_data},
        upsert=True
    )

    return jsonify({"message": "Budget successfully saved!", "budget": budget_data}), 201