from flask import request, abort, current_app
import jwt
from models import User
from datetime import datetime, timedelta


def extract_auth_token(authenticated_request):
    auth_header = authenticated_request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ")[1]

def decode_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = int(payload['sub'])
        return user_id
    except jwt.ExpiredSignatureError:
        abort(403, "Token has expired")
    except jwt.InvalidTokenError:
        abort(403, "Invalid token")

def create_token(user_id):
    payload = {
        'exp': datetime.utcnow() + timedelta(days=4),
        'iat': datetime.utcnow(),
        'sub': str(user_id)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token():
    auth_token = extract_auth_token(request)
    if not auth_token:
        abort(403, "Missing token")
    user_id = decode_token(auth_token)
    user = User.query.get(user_id)
    if not user:
        abort(403, "Invalid user")
    return user

def verify_admin_token():
    user = verify_token()
    if user.role != 'admin':
        abort(403, "Admin access required")
    return user
