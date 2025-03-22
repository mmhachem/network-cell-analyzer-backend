from flask import Flask, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_bcrypt import Bcrypt
from db_config import DB_CONFIG
from models import db, User, user_schema
from routes.app_routes import app_routes 
from routes.admin_routes import admin_routes  
from datetime import datetime, timedelta
import jwt
from dotenv import load_dotenv
import os
from utils.auth_utils import create_token


load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

# ✅ Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONFIG
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

# ✅ Initialize SQLAlchemy & Limiter

db.init_app(app)
limiter = Limiter(key_func=get_remote_address)
limiter.init_app(app)

# ✅ Register app routes
app.register_blueprint(app_routes)
app.register_blueprint(admin_routes)



@app.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    role = "user"  # force role to user, do not allow admin creation here

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409

    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify(user_schema.dump(new_user)), 201


@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=username, role='user').first()  # only normal users
    if not user or not bcrypt.check_password_hash(user.hashed_password, password):
        return jsonify({"error": "Invalid username or password"}), 403

    token = create_token(user.id)
    return jsonify({"token": token}), 200


@app.route('/admin/login', methods=['POST'])
@limiter.limit("5 per minute")
def admin_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=username, role='admin').first()
    if not user:
        return jsonify({"error": "Admin account not found"}), 403

    if not bcrypt.check_password_hash(user.hashed_password, password):
        return jsonify({"error": "Incorrect password"}), 403

    token = create_token(user.id)
    return jsonify({"admin_token": token}), 200



# ✅ Health Check Route
@app.route('/')
def home():
    return "✅ Network Cell Analyzer Backend is running!"


# ✅ Run app
if __name__ == '__main__':
    app.run(debug=True)
