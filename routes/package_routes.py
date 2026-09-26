from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from bson.objectid import ObjectId
from bson.errors import InvalidId

package_bp = Blueprint('packages', __name__)

@package_bp.route('/api/packages', methods=['POST'])
@jwt_required()
def create_package():
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Only admins can create packages."}), 403

    data = request.get_json()
    title = data.get("title")
    description = data.get("description")
    price = data.get("price")
    audience = data.get("audience")
    category = data.get("category", "Other")
    featured = data.get("featured", False)
    inclusions = data.get("inclusions", [])
    image_url = data.get("image_url")

    if not title or audience not in ["client", "vendor", "both"]:
        return jsonify({"error": "Title and a valid audience (client/vendor/both) are required."}), 400

    package = {
        "title": title,
        "description": description,
        "price": price,
        "audience": audience,
        "category": category,
        "featured": bool(featured),
        "inclusions": inclusions,
        "image_url": image_url,
    }
    result = mongo.db.packages.insert_one(package)
    return jsonify({"message": "Package created!", "package_id": str(result.inserted_id)}), 201


@package_bp.route('/api/packages', methods=['GET'])
@jwt_required()
def get_packages():
    from app import mongo
    claims = get_jwt()
    role = claims.get("role")

    if role == "admin":
        query = {}
    elif role == "client":
        query = {"audience": {"$in": ["client", "both"]}}
    elif role == "vendor":
        query = {"audience": {"$in": ["vendor", "both"]}}
    else:
        return jsonify({"error": "Unauthorized"}), 403

    packages = list(mongo.db.packages.find(query))
    for p in packages:
        p["_id"] = str(p["_id"])
        if role == "admin":
            p["usage_count"] = mongo.db.events.count_documents({"package_id": p["_id"]})

    return jsonify(packages), 200


@package_bp.route('/api/public/packages', methods=['GET'])
def get_public_packages():
    from app import mongo
    packages = list(mongo.db.packages.find({"audience": {"$in": ["client", "both"]}}))
    for p in packages:
        p["_id"] = str(p["_id"])
    return jsonify(packages), 200


@package_bp.route('/api/packages/<package_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_package(package_id):
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Only admins can modify packages."}), 403

    try:
        obj_id = ObjectId(package_id)
    except InvalidId:
        return jsonify({"error": "Invalid Package ID format"}), 400

    if request.method == "DELETE":
        result = mongo.db.packages.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Package not found"}), 404
        return jsonify({"message": "Package deleted successfully."}), 200

    if request.method == "PUT":
        data = request.get_json()
        result = mongo.db.packages.update_one({"_id": obj_id}, {"$set": data})
        if result.matched_count == 0:
            return jsonify({"error": "Package not found"}), 404
        return jsonify({"message": "Package updated successfully."}), 200