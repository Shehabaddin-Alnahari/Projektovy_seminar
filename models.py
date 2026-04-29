from database import db
from datetime import datetime, timezone
from flask_login import UserMixin

# UserMixin dodá Flasku metody, díky kterým ví, že je uživatel přihlášený
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='teacher')
    faculty = db.Column(db.String(50), nullable=True)
    
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(20), nullable=False)
    building = db.Column(db.String(50), nullable=False)
    floor = db.Column(db.Integer)
    capacity = db.Column(db.Integer)
    room_type = db.Column(db.String(50))    # např. PC laboratoř, pracovna...
    faculty = db.Column(db.String(100))
    notes = db.Column(db.Text)      # poznámky ze STAGu
    
    reservations = db.relationship('Reservation', backref='room', lazy=True)

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    
    # Stavy: pending (čeká), approved (schváleno), rejected (zamítnuto), canceled (zrušeno)
    status = db.Column(db.String(20), default='pending')
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    approval_date = db.Column(db.DateTime) # datum schválení/zrušení