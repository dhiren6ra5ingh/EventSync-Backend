from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from bson.objectid import ObjectId
from bson.errors import InvalidId

task_bp = Blueprint('tasks', __name__)

@task_bp.route('/api/client/event-tasks/<event_id>', methods=['GET'])
@jwt_required()
def get_event_tasks_for_client(event_id):
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "client":
        return jsonify({"error": "Unauthorized."}), 403

    try:
        obj_id = ObjectId(event_id)
    except InvalidId:
        return jsonify({"error": "Invalid Event ID"}), 400

    client_id = get_jwt_identity()
    event = mongo.db.events.find_one({"_id": obj_id, "client_id": client_id})
    if not event:
        return jsonify({"error": "Event not found or not yours."}), 404

    tasks = list(mongo.db.tasks.find({"event_id": event_id}))
    for t in tasks:
        t["_id"] = str(t["_id"])

    return jsonify(tasks), 200

@task_bp.route('/api/tasks', methods=['POST'])
@jwt_required()
def assign_task():
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can assign tasks."}), 403

    data = request.get_json()
    requested_venue = data.get("venue")
    req_start = data.get("start_time")
    req_end = data.get("end_time")

    if requested_venue and req_start and req_end:
        clash = mongo.db.tasks.find_one({
            "venue": requested_venue,
            "start_time": {"$lt": req_end},
            "end_time": {"$gt": req_start}
        })
        
        if clash:
            return jsonify({"error": f"Resource conflict: {requested_venue} is already booked during this time."}), 409

    task = {
        "vendor_id": data.get("vendor_id"),
        "event_id": data.get("event_id"),
        "description": data.get("description"),
        "venue": requested_venue,
        "start_time": req_start,
        "end_time": req_end,
        "status": "Pending"
    }
    
    result = mongo.db.tasks.insert_one(task)
    return jsonify({
        "message": "Task assigned successfully!", 
        "task_id": str(result.inserted_id)
    }), 201

@task_bp.route('/api/tasks/<task_id>/status', methods=['PUT'])
@jwt_required()
def update_task_status(task_id):
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "vendor":
        return jsonify({"error": "Unauthorized. Only vendors can update tasks."}), 403

    data = request.get_json()
    new_status = data.get("status")

    if new_status not in ["In Progress", "Completed"]:
        return jsonify({"error": "Invalid status. Must be 'In Progress' or 'Completed'."}), 400

    try:
        result = mongo.db.tasks.update_one(
            {"_id": ObjectId(task_id)},
            {"$set": {"status": new_status}}
        )
    except InvalidId:
        return jsonify({"error": "Invalid Task ID format"}), 400

    if result.matched_count == 0:
        return jsonify({"error": "Task not found."}), 404

    return jsonify({"message": f"Task status successfully updated to '{new_status}'!"}), 200

@task_bp.route('/api/tasks/my-tasks', methods=['GET'])
@jwt_required()
def get_vendor_tasks():
    from app import mongo
    
    # The identity is now the user ID string
    current_user_id = get_jwt_identity()
    claims = get_jwt()

    if claims.get("role") != "vendor":
        return jsonify({"error": "Unauthorized. Only vendors can view this page."}), 403

    # Look up the vendor using their ObjectId, not their email
    vendor_user = mongo.db.users.find_one({"_id": ObjectId(current_user_id)})
    if not vendor_user:
        return jsonify({"error": "Vendor account not found."}), 404
        
    vendor_id_str = str(vendor_user["_id"])

    # Search for tasks assigned to this vendor ID
    tasks_cursor = mongo.db.tasks.find({
        "vendor_id": vendor_id_str
    })

    vendor_tasks = []
    for task in tasks_cursor:
        task["_id"] = str(task["_id"])
        vendor_tasks.append(task)

    return jsonify(vendor_tasks), 200

@task_bp.route("/api/tasks/<task_id>", methods=["PUT", "DELETE"])
@jwt_required()
def manage_task_admin(task_id):
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can modify tasks."}), 403

    try:
        obj_id = ObjectId(task_id)
    except InvalidId:
        return jsonify({"error": "Invalid Task ID format"}), 400

    if request.method == "DELETE":
        result = mongo.db.tasks.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"message": "Task deleted successfully."}), 200

    if request.method == "PUT":
        data = request.get_json()
        result = mongo.db.tasks.update_one({"_id": obj_id}, {"$set": data})
        if result.matched_count == 0:
            return jsonify({"error": "Task not found"}), 404
        return jsonify({"message": "Task updated successfully."}), 200