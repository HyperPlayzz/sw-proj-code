from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import CheckConstraint, UniqueConstraint
from sqlalchemy.orm import validates
import re
from typing import Optional, Dict, Any

db = SQLAlchemy()

# Model for role table
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

# Model for site table
class Site(db.Model):
    __tablename__ = 'sites'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    desks = db.relationship('Desk', backref='site', lazy=True)

    __table_args__ = (
        CheckConstraint('length(name) > 0 AND length(name) <= 120', name='ck_site_name_len'),
    )

    # Validate site name
    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        if not name or len(name.strip()) == 0:
            raise ValueError('Site name required')
        if len(name) > 120:
            raise ValueError('Site name too long (max 120 characters)')
        return name

# Model for user table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    role = db.relationship('Role')
    bookings = db.relationship('Booking', backref='user', lazy=True)

    __table_args__ = (
        CheckConstraint("instr(email, '@') > 1", name='ck_user_email_at'),
        CheckConstraint('length(name) > 0 AND length(name) <= 100', name='ck_user_name_len'),
        CheckConstraint('length(email) <= 120', name='ck_user_email_len'),
    )

# Validations for User model
    @validates('email')
    def validate_email(self, key: str, address: str) -> str:
        if not address or '@' not in address:
            raise ValueError('Invalid email format')
        if len(address) > 120:
            raise ValueError('Email too long (max 120 characters)')
        if len(address) < 5:
            raise ValueError('Email too short (min 5 characters)')
        return address

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        if not name or len(name) == 0:
            raise ValueError('Name required')
        if len(name) > 100:
            raise ValueError('Name too long (max 100 characters)')
        return name

    @validates('password')
    def validate_password(self, key: str, password: str) -> str:
        if not password or len(password) == 0:
            raise ValueError('Password required')
        if len(password) < 6:
            raise ValueError('Password too short (min 6 characters)')
        if len(password) > 255:
            raise ValueError('Password too long (max 255 characters)')
        return password

# Model for desk table
class Desk(db.Model):
    __tablename__ = 'desks'
    id = db.Column(db.Integer, primary_key=True)
    desk_number = db.Column(db.String(20), nullable=False)
    floor = db.Column(db.Integer, nullable=False, default=0)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    bookings = db.relationship('Booking', backref='desk', lazy=True)

    __table_args__ = (
        UniqueConstraint('desk_number', 'site_id', name='uq_desk_number_site'),
        CheckConstraint('length(desk_number) > 0 AND length(desk_number) <= 20', name='ck_desk_number_len'),
    )
    # Validations for Desk model
    @validates('desk_number')
    def validate_desk_number(self, key: str, dn: str) -> str:
        if not dn or len(dn.strip()) == 0:
            raise ValueError('Desk number required')
        dn = dn.strip()
        if len(dn) > 20:
            raise ValueError('Desk number too long (max 20 characters)')
        m = re.match(r'^([A-Za-z]{1,3})([- ]?)([0-9]+[A-Za-z]*)$', dn)
        if not m:
            raise ValueError("Desk number must match pattern like 'SH 154' or 'T-1' or 'SH-154E'")
        prefix = m.group(1).upper()
        sep = m.group(2) or ''
        rest = m.group(3)
        dn = f"{prefix}{sep}{rest}"
        return dn

    @validates('floor')
    def validate_floor(self, key: str, floor: int) -> int:
        if floor is None:
            raise ValueError('Floor required')
        if not isinstance(floor, int):
            raise ValueError('Floor must be an integer')
        if floor < 0:
            raise ValueError('Floor cannot be negative')
        if floor > 100:
            raise ValueError('Floor too high (max 100)')
        return floor

# Model for booking table
class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    desk_id = db.Column(db.Integer, db.ForeignKey('desks.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        CheckConstraint('end_time > start_time', name='ck_booking_time_order'),
    )

    # Validations for Booking model
    @validates('start_time')
    def validate_start_time(self, key: str, start_time: datetime) -> datetime:
        if start_time is None:
            raise ValueError('Start time required')
        if not isinstance(start_time, datetime):
            raise ValueError('Start time must be a datetime')
        return start_time

    @validates('end_time')
    def validate_end_time(self, key: str, end_time: datetime) -> datetime:
        if end_time is None:
            raise ValueError('End time required')
        if not isinstance(end_time, datetime):
            raise ValueError('End time must be a datetime')
        return end_time

    def to_dict(self) -> Dict[str, Any]:
        # Keep machine-readable format for form inputs, and include formatted display values
        return {
            'booking_id': self.id,
            'user_id': self.user_id,
            'desk_id': self.desk_id,
            'desk_number': self.desk.desk_number if self.desk else None,
            'user_name': self.user.name if self.user else None,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M'),
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M'),
            'start_time_formatted': self.start_time.strftime('%d/%m/%Y %H:%M'),
            'end_time_formatted': self.end_time.strftime('%d/%m/%Y %H:%M')
        }