from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from bson.objectid import ObjectId
from bson.errors import InvalidId

event_bp = Blueprint('events', __name__)

@event_bp.route("/api/events", methods=["POST"])
@jwt_required()
def create_event():
    from app import mongo
    current_user_id = get_jwt_identity()
    claims = get_jwt()
    
    if claims.get("role") not in ["admin", "vendor"]:
        return jsonify({"error": "Unauthorized access."}), 403

    data = request.get_json()
    vendor_id = data.get("vendor_id")
    event_date = data.get("event_date")
    start_time = data.get("start_time")
    end_time = data.get("end_time")

    existing_conflict = mongo.db.events.find_one({
        "vendor_id": vendor_id,
        "event_date": event_date,
        "$or": [
            {"start_time": {"$lte": end_time}, "end_time": {"$gte": start_time}}
        ]
    })

    if existing_conflict:
        return jsonify({
            "error": "Scheduling conflict detected!",
            "message": f"Vendor is already booked on {event_date} between {existing_conflict.get('start_time')} and {existing_conflict.get('end_time')}."
        }), 409

    new_event = {
        "title": data.get("title"),
        "vendor_id": vendor_id,
        "event_date": event_date,
        "start_time": start_time,
        "end_time": end_time,
        "created_by_id": current_user_id
    }
    mongo.db.events.insert_one(new_event)
    return jsonify({"message": "Event created successfully without conflicts!"}), 201
@event_bp.route('/api/client/my-events', methods=['GET'])
@jwt_required()
def get_my_events():
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "client":
        return jsonify({"error": "Unauthorized. Only clients can view this."}), 403

    current_client_id = get_jwt_identity()
    events = list(mongo.db.events.find({"client_id": current_client_id}))
    for ev in events:
        ev["_id"] = str(ev["_id"])
    return jsonify(events), 200

@event_bp.route('/api/events', methods=['GET'])
@jwt_required()
def get_all_events():
    from app import mongo
    events = list(mongo.db.events.find())
    for event in events:
        event["_id"] = str(event["_id"])
    return jsonify(events), 200

@event_bp.route("/api/events/<event_id>", methods=["PUT", "DELETE"])
@jwt_required()
def manage_event(event_id):
    from app import mongo
    current_user = get_jwt()
    if current_user.get("role") != "admin":
        return jsonify({"error": "Unauthorized. Only admins can modify events."}), 403

    try:
        obj_id = ObjectId(event_id)
    except InvalidId:
        return jsonify({"error": "Invalid Event ID format"}), 400

    if request.method == "DELETE":
        result = mongo.db.events.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Event not found"}), 404
        return jsonify({"message": "Event deleted successfully."}), 200

    if request.method == "PUT":
        data = request.get_json()
        result = mongo.db.events.update_one({"_id": obj_id}, {"$set": data})
        if result.matched_count == 0:
            return jsonify({"error": "Event not found"}), 404
        return jsonify({"message": "Event updated successfully."}), 200

@event_bp.route("/api/events/<event_id>/book", methods=["POST"])
@jwt_required()
def book_event(event_id):
    from app import mongo
    claims = get_jwt()
    
    if claims.get("role") != "client":
        return jsonify({"error": "Access forbidden: Clients only!"}), 403
        
    client_id = get_jwt_identity()
    
    try:
        event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            return jsonify({"error": "Event not found"}), 404
    except InvalidId:
        return jsonify({"error": "Invalid Event ID format"}), 400
        
    booking = {
        "event_id": event_id,
        "client_id": client_id,
        "status": "confirmed"
    }
    
    mongo.db.bookings.insert_one(booking)
    return jsonify({"message": "Event booked successfully!"}), 201

@event_bp.route('/api/client/request-event', methods=['POST'])
@jwt_required()
def request_event():
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "client":
        return jsonify({"error": "Only clients can request an event."}), 403

    client_id = get_jwt_identity()
    data = request.get_json()
    title = data.get("title")
    preferred_date = data.get("preferred_date")
    preferred_start_time = data.get("preferred_start_time")
    preferred_end_time = data.get("preferred_end_time")
    description = data.get("description")
    package_id = data.get("package_id")
    guest_count = data.get("guest_count")

    if not title or not preferred_date or not preferred_start_time or not preferred_end_time:
        return jsonify({"error": "Title, date, start time and end time are all required."}), 400

    new_event = {
        "title": title,
        "preferred_date": preferred_date,
        "preferred_start_time": preferred_start_time,
        "preferred_end_time": preferred_end_time,
        "description": description,
        "client_id": client_id,
        "package_id": package_id,
        "status": "pending",
        "vendor_id": None,
        "event_date": None,
        "start_time": None,
        "end_time": None,
        "guest_count": guest_count,
    }

    result = mongo.db.events.insert_one(new_event)
    return jsonify({"message": "Event request submitted!", "event_id": str(result.inserted_id)}), 201

@event_bp.route('/api/admin/pending-events', methods=['GET'])
@jwt_required()
def get_pending_events():
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403

    events = list(mongo.db.events.find({"status": "pending"}))
    for ev in events:
        ev["_id"] = str(ev["_id"])
    return jsonify(events), 200

@event_bp.route('/api/admin/confirm-event/<event_id>', methods=['PUT'])
@jwt_required()
def confirm_event(event_id):
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403

    try:
        obj_id = ObjectId(event_id)
    except InvalidId:
        return jsonify({"error": "Invalid Event ID format"}), 400

    original_event = mongo.db.events.find_one({"_id": obj_id})
    if not original_event:
        return jsonify({"error": "Event not found"}), 404

    data = request.get_json()
    vendor_id = data.get("vendor_id")

    # Time now comes from the client's original request, not from admin input
    event_date = original_event.get("preferred_date")
    start_time = original_event.get("preferred_start_time")
    end_time = original_event.get("preferred_end_time")

    existing_conflict = mongo.db.events.find_one({
        "_id": {"$ne": obj_id},
        "vendor_id": vendor_id,
        "event_date": event_date,
        "start_time": {"$lte": end_time},
        "end_time": {"$gte": start_time}
    })

    if existing_conflict:
        return jsonify({
            "error": "Scheduling conflict detected!",
            "message": f"Vendor is already booked on {event_date} between {existing_conflict.get('start_time')} and {existing_conflict.get('end_time')}."
        }), 409

    result = mongo.db.events.update_one(
        {"_id": obj_id},
        {"$set": {
            "vendor_id": vendor_id,
            "event_date": event_date,
            "start_time": start_time,
            "end_time": end_time,
            "status": "confirmed"
        }}
    )

    return jsonify({"message": "Event confirmed successfully!"}), 200

@event_bp.route('/api/admin/vendor-schedule', methods=['GET'])
@jwt_required()
def get_vendor_schedule():
    from app import mongo
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "Unauthorized."}), 403

    vendor_id = request.args.get("vendor_id")
    date = request.args.get("date")

    if not vendor_id or not date:
        return jsonify({"error": "vendor_id and date are required."}), 400

    events = list(mongo.db.events.find({
        "vendor_id": vendor_id,
        "event_date": date
    }))
    tasks = list(mongo.db.tasks.find({
        "vendor_id": vendor_id,
        "event_date": date
    })) if mongo.db.tasks.find_one({"vendor_id": vendor_id, "event_date": date}) else []

    # Tasks don't store event_date directly in your schema, so pull it from parent events
    all_tasks = list(mongo.db.tasks.find({"vendor_id": vendor_id}))
    matching_tasks = []
    for t in all_tasks:
        parent_event = mongo.db.events.find_one({"_id": ObjectId(t["event_id"])}) if t.get("event_id") else None
        if parent_event and parent_event.get("event_date") == date:
            matching_tasks.append(t)

    schedule = []
    for ev in events:
        schedule.append({
            "type": "event",
            "label": ev.get("title", "Event"),
            "start_time": ev.get("start_time"),
            "end_time": ev.get("end_time"),
        })
    for t in matching_tasks:
        schedule.append({
            "type": "task",
            "label": f'{t.get("description", "Task")} ({t.get("venue", "")})',
            "start_time": t.get("start_time"),
            "end_time": t.get("end_time"),
        })

    return jsonify(schedule), 200
@event_bp.route('/api/client/event-status/<event_id>', methods=['GET'])
@jwt_required()
def get_event_status(event_id):
    from app import mongo
    current_user = get_jwt()
    
    if current_user.get("role") not in ["client", "admin"]:
        return jsonify({"error": "Unauthorized. Only clients and admins can view this."}), 403

    try:
        event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            return jsonify({"error": "Event not found."}), 404
    except InvalidId:
        return jsonify({"error": "Invalid Event ID format"}), 400

    tasks = list(mongo.db.tasks.find({"event_id": event_id}))
    total_tasks = len(tasks)
    completed_tasks = sum(1 for task in tasks if task.get("status") == "Completed")
    
    progress_percentage = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

    budget = mongo.db.budgets.find_one({"event_id": event_id})
    
    if budget:
        budget_summary = {
            "total_allocated": budget.get("total_allocated", 0),
            "spent": budget.get("spent", 0),
            "remaining": budget.get("remaining", 0),
            "categories": budget.get("categories", {})
        }
    else:
        budget_summary = {
            "total_allocated": 0,
            "spent": 0,
            "remaining": 0,
            "categories": {}
        }

    return jsonify({
        "event_title": event.get("title", "Unnamed Event"),
        "date": event.get("event_date", "TBD"),
        "task_progress": f"{progress_percentage}%",
        "tasks_completed": f"{completed_tasks} out of {total_tasks}",
        "guest_count": event.get("guest_count"),
        "budget_overview": budget_summary
        
    }), 200