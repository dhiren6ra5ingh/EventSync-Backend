import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_pymongo import PyMongo
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

mongo = PyMongo(app)
jwt = JWTManager(app)

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "EventSync Backend is running successfully!"})

# --- BLUEPRINT REGISTRATION ---
from routes.auth_routes import auth_bp
from routes.event_routes import event_bp
from routes.task_routes import task_bp
from routes.budget_routes import budget_bp
from routes.admin_routes import admin_bp
from routes.package_routes import package_bp

app.register_blueprint(auth_bp)
app.register_blueprint(event_bp)
app.register_blueprint(task_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(package_bp)

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", 5000)))