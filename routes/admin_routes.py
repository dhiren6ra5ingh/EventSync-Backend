from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/api/admin-dashboard", methods=["GET"])
@jwt_required()
def admin_dashboard():
    from app import mongo
    jwt_claims = get_jwt()
    if jwt_claims.get("role") != "admin":
        return jsonify({"error": "Access forbidden: Admins only!"}), 403
        
    # Fetch the actual username from the database using the token ID
    current_user_id = get_jwt_identity()
    admin_user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
    username = admin_user.get("username", "Admin") if admin_user else "Admin"
    
    return jsonify({"message": f"Welcome to the Admin Dashboard, {username}!"}), 200

@admin_bp.route("/api/bookings", methods=["GET"])
@jwt_required()
def get_bookings():
    from app import mongo
    bookings_cursor = mongo.db.bookings.find()
    bookings_list = []
    for booking in bookings_cursor:
        booking["_id"] = str(booking["_id"])
        bookings_list.append(booking)
    return jsonify(bookings_list), 200

@admin_bp.route('/api/requests', methods=['POST'])
@jwt_required()
def submit_client_request():
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "client":
        return jsonify({"error": "Unauthorized. Only clients can submit requests."}), 403

    data = request.get_json()
    event_id = data.get("event_id")
    request_text = data.get("request_text")

    if not event_id or not request_text:
        return jsonify({"error": "Both event_id and request_text are required."}), 400

    new_request = {
        "event_id": event_id,
        "client_id": get_jwt_identity(), # Renamed from client_email
        "request_text": request_text,
        "status": "open"
    }
    
    mongo.db.client_requests.insert_one(new_request)
    return jsonify({"message": "Request submitted successfully!"}), 201

@admin_bp.route("/api/requests", methods=["GET"])
@jwt_required()
def view_client_requests():
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can view client requests."}), 403

    requests_cursor = mongo.db.client_requests.find()
    requests_list = []
    for req in requests_cursor:
        req["_id"] = str(req["_id"])
        requests_list.append(req)
        
    return jsonify(requests_list), 200

@admin_bp.route('/api/analytics/summary', methods=['GET'])
@jwt_required()
def get_analytics_summary():
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can access analytics."}), 403

    events = list(mongo.db.events.find())
    tasks = list(mongo.db.tasks.find())
    budgets = list(mongo.db.budgets.find())

    for event in events:
        event["_id"] = str(event["_id"])
    for task in tasks:
        task["_id"] = str(task["_id"])
    for budget in budgets:
        if "_id" in budget:
            budget["_id"] = str(budget["_id"])

    analytics_data = {
        "total_events": len(events),
        "total_tasks": len(tasks),
        "total_budgets_tracked": len(budgets),
        "events": events,
        "tasks": tasks,
        "budgets": budgets
    }
    return jsonify(analytics_data), 200

@admin_bp.route("/api/admin/users", methods=["POST"])
@jwt_required()
def create_elevated_user():
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can create accounts."}), 403

    data = request.get_json()
    email = data.get("email")
    role = data.get("role")
    
    if role not in ["vendor", "admin"]:
        return jsonify({"error": "Role must be 'vendor' or 'admin'."}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"error": "User already exists."}), 400

    new_user = {
        "username": data.get("username"),
        "email": email,
        "password": generate_password_hash(data.get("password")),
        "role": role
    }
    mongo.db.users.insert_one(new_user)
    return jsonify({"message": f"{role.capitalize()} account created successfully!"}), 201
@admin_bp.route("/api/requests/<request_id>/resolve", methods=["PUT"])
@jwt_required()
def resolve_request(request_id):
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can resolve requests."}), 403

    try:
        obj_id = ObjectId(request_id)
    except Exception:
        return jsonify({"error": "Invalid Request ID format"}), 400

    result = mongo.db.client_requests.update_one(
        {"_id": obj_id},
        {"$set": {"status": "resolved"}}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Request not found"}), 404

    return jsonify({"message": "Request marked as resolved!"}), 200

@admin_bp.route("/api/vendors", methods=["GET"])
@jwt_required()
def get_all_vendors():
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can view the vendor list."}), 403

    vendors_cursor = mongo.db.users.find({"role": "vendor"}, {"password": 0})
    vendors = []
    for vendor in vendors_cursor:
        vendor["_id"] = str(vendor["_id"])
        vendors.append(vendor)
    
    return jsonify(vendors), 200