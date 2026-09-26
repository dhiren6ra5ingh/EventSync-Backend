from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from bson.objectid import ObjectId

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/api/register", methods=["POST"])
def register_user():
    from app import mongo 
    data = request.get_json()
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")
    role = "client"

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are all required."}), 400

    if "@" not in email or "." not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters long."}), 400

    if mongo.db.users.find_one({"email": email}):
        return jsonify({"error": "User with this email already exists."}), 400

    hashed_password = generate_password_hash(password)
    mongo.db.users.insert_one({
        "username": username,
        "email": email,
        "password": hashed_password,
        "role": role
    })
    return jsonify({"message": "User registered successfully!", "role": role}), 201

@auth_bp.route("/api/login", methods=["POST"])
def login_user():
    from app import mongo
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = mongo.db.users.find_one({"email": email})

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    access_token = create_access_token(identity=str(user["_id"]), additional_claims={"role": user["role"]})
    refresh_token = create_refresh_token(identity=str(user["_id"]), additional_claims={"role": user["role"]})

    return jsonify({
        "message": "Login successful!",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user["role"]
    }), 200

@auth_bp.route("/api/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh_token():
    from app import mongo
    current_user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
    
    if not user:
        return jsonify({"error": "User not found"}), 404

    new_access_token = create_access_token(identity=current_user_id, additional_claims={"role": user["role"]})
    return jsonify({"access_token": new_access_token}), 200