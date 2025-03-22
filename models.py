from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt


db = SQLAlchemy()
ma = Marshmallow()
bcrypt = Bcrypt()

class CellRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    operator = db.Column(db.String(50))
    signal_power = db.Column(db.Float)
    sinr = db.Column(db.Float)
    network_type = db.Column(db.String(10))
    frequency_band = db.Column(db.String(50))
    cell_id = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime)
    device_ip = db.Column(db.String(50))
    device_mac = db.Column(db.String(50))
    device_id = db.Column(db.String(100))
    username = db.Column(db.String(50), db.ForeignKey('user.username'), nullable=False)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    hashed_password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), default="user")

    def __init__(self, username, password, role="user"):
        self.username = username
        self.hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.role = role

class UserSchema(ma.Schema):
    class Meta:
        fields = ("id", "username", "role")

user_schema = UserSchema()
users_schema = UserSchema(many=True)
