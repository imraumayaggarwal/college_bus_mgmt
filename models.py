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

# ========================
# BILLING & PAYMENT MODELS
# ========================

class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # 'Monthly', 'Quarterly', 'Yearly'
    price = db.Column(db.Float, nullable=False)  # Price in currency units
    duration_days = db.Column(db.Integer, nullable=False)  # Number of days
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(100), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'paid', 'overdue', 'cancelled'
    issued_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=False)
    paid_date = db.Column(db.DateTime)
    
    description = db.Column(db.Text)
    notes = db.Column(db.Text)
    
    parent = db.relationship('Parent', backref='invoices', foreign_keys=[parent_id])
    student = db.relationship('Student', backref='invoices', foreign_keys=[student_id])
    subscription = db.relationship('Subscription', backref='invoices', foreign_keys=[subscription_id])

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # 'credit_card', 'debit_card', 'bank_transfer', 'upi', 'cash'
    amount = db.Column(db.Float, nullable=False)
    transaction_id = db.Column(db.String(255), unique=True)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='completed')  # 'pending', 'completed', 'failed', 'refunded'
    
    notes = db.Column(db.Text)
    
    invoice = db.relationship('Invoice', backref='payments', foreign_keys=[invoice_id])

class BillingCycle(db.Model):
    __tablename__ = 'billing_cycles'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='billing_cycles', foreign_keys=[student_id])
    subscription = db.relationship('Subscription', backref='billing_cycles', foreign_keys=[subscription_id])

