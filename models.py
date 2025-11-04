# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin','student','parent','driver'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))

    # explicitly state foreign_keys so SQLAlchemy knows which column to join on
    user = db.relationship('User', backref='driver', uselist=False, foreign_keys=[user_id])

class Parent(db.Model):
    __tablename__ = 'parents'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))

    user = db.relationship('User', backref='parent', uselist=False, foreign_keys=[user_id])

class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    route_code = db.Column(db.String(100))
    geojson = db.Column(db.Text)  # optional, to be filled later by map UI
    color = db.Column(db.String(20))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Bus(db.Model):
    __tablename__ = 'buses'
    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, default=0)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id', ondelete='SET NULL'))

    driver = db.relationship('Driver', backref='buses', foreign_keys=[driver_id])

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))
    roll_number = db.Column(db.String(100))
    parent_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    assigned_bus_id = db.Column(db.Integer, db.ForeignKey('buses.id', ondelete='SET NULL'))
    assigned_route_id = db.Column(db.Integer, db.ForeignKey('routes.id', ondelete='SET NULL'))

    # VERY IMPORTANT: disambiguate which foreign key each relationship uses
    user = db.relationship('User', backref='student', uselist=False, foreign_keys=[user_id])
    parent_user = db.relationship('User', foreign_keys=[parent_user_id])
    assigned_bus = db.relationship('Bus', foreign_keys=[assigned_bus_id])
    assigned_route = db.relationship('Route', foreign_keys=[assigned_route_id])

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NotificationReceiver(db.Model):
    __tablename__ = 'notification_receivers'
    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey('notifications.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'))
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'))
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'))
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    attendance_date = db.Column(db.Date, nullable=False)
    pickup_or_drop = db.Column(db.String(10), nullable=False)
    slot = db.Column(db.Integer, nullable=False)
    present = db.Column(db.Boolean, default=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    __tablename__ = 'contacts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    relation = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(255))
