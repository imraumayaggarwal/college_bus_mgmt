# app.py
import os
import json
from datetime import date, datetime, time as dt_time
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from sqlalchemy import or_

# Import your models module --
# models.py must define: db, User, Driver, Parent, Bus, Student, Route, Notification, NotificationReceiver, Attendance
from models import (
    db, User, Driver, Parent, Bus, Student, Route,
    Notification, NotificationReceiver, Attendance,
    Subscription, Invoice, Payment, BillingCycle
)

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'devsecretkey123')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/college_bus_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Default pickup/drop slot times (can be overridden with env vars)
    app.config['SLOT_PICKUP1'] = os.environ.get('SLOT_PICKUP1', '07:00')
    app.config['SLOT_PICKUP2'] = os.environ.get('SLOT_PICKUP2', '07:30')
    app.config['SLOT_DROP1']   = os.environ.get('SLOT_DROP1',   '16:00')
    app.config['SLOT_DROP2']   = os.environ.get('SLOT_DROP2',   '16:30')

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    class LoginUser(UserMixin):
        def __init__(self, user):
            self.id = user.id
            self.email = user.email
            self.role = user.role

    @login_manager.user_loader
    def load_user(user_id):
        try:
            u = User.query.get(int(user_id))
        except Exception:
            u = None
        if not u:
            return None
        return LoginUser(u)

    # -----------------------
    # Landing & Auth
    # -----------------------
    @app.route('/')
    def landing():
        if current_user.is_authenticated:
            return render_template('landing.html', logged_in=True, role=current_user.role, email=current_user.email)
        return render_template('landing.html', logged_in=False)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(LoginUser(user))
                flash('Logged in successfully', 'success')
                # redirect to role-based landing if you prefer
                return redirect(url_for('landing'))
            flash('Invalid credentials', 'danger')
        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logged out', 'info')
        return redirect(url_for('landing'))

    # -----------------------
    # Signups
    # -----------------------
    @app.route('/signup/student', methods=['GET', 'POST'])
    def signup_student():
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            full_name = request.form['full_name'].strip()
            password = request.form['password'].strip()
            roll = request.form.get('roll_number','').strip()
            phone = request.form.get('phone','').strip()
            if not email or not full_name or not password:
                flash('Please provide name, email and password', 'danger')
                return render_template('signup_student.html')
            if User.query.filter_by(email=email).first():
                flash('Email already registered. Try logging in.', 'danger')
                return render_template('signup_student.html')
            u = User(email=email, password_hash=generate_password_hash(password), role='student')
            db.session.add(u)
            db.session.flush()
            s = Student(user_id=u.id, full_name=full_name, phone=phone, roll_number=roll)
            db.session.add(s)
            db.session.commit()
            flash('Student account created. You may now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('signup_student.html')

    @app.route('/signup/parent', methods=['GET', 'POST'])
    def signup_parent():
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            full_name = request.form['full_name'].strip()
            password = request.form['password'].strip()
            phone = request.form.get('phone','').strip()
            if not email or not full_name or not password:
                flash('Please provide name, email and password', 'danger')
                return render_template('signup_parent.html')
            if User.query.filter_by(email=email).first():
                flash('Email already registered. Try logging in.', 'danger')
                return render_template('signup_parent.html')
            u = User(email=email, password_hash=generate_password_hash(password), role='parent')
            db.session.add(u)
            db.session.flush()
            p = Parent(user_id=u.id, full_name=full_name, phone=phone)
            db.session.add(p)
            db.session.commit()
            flash('Parent account created. You may now log in.', 'success')
            return redirect(url_for('login'))
        return render_template('signup_parent.html')

    # -----------------------
    # Admin Dashboard & CRUD
    # -----------------------
    @app.route('/admin')
    @login_required
    def admin_dashboard():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        total_students = Student.query.count()
        total_buses = Bus.query.count()
        total_routes = Route.query.count()
        return render_template('admin_dashboard.html', 
                             total_students=total_students,
                             total_buses=total_buses,
                             total_routes=total_routes)

    @app.route('/admin/drivers')
    @login_required
    def admin_drivers():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        drivers = Driver.query.all()
        # also pass buses so template can try to show assigned bus safely
        buses = Bus.query.all()
        return render_template('admin_drivers.html', drivers=drivers, buses=buses)

    @app.route('/admin/drivers/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_driver():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            full_name = request.form['full_name'].strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', 'Driver@123').strip()
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'danger')
            else:
                u = User(email=email, password_hash=generate_password_hash(password), role='driver')
                db.session.add(u); db.session.flush()
                d = Driver(user_id=u.id, full_name=full_name, phone=phone)
                db.session.add(d); db.session.commit()
                flash(f'Driver created: {email} / {password}', 'success')
                return redirect(url_for('admin_drivers'))
        return render_template('admin_create_driver.html')

    @app.route('/admin/drivers/edit/<int:driver_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_driver(driver_id):
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        driver = Driver.query.get_or_404(driver_id)
        if request.method == 'POST':
            driver.full_name = request.form['full_name'].strip()
            driver.phone = request.form.get('phone', '').strip()
            db.session.commit()
            flash('Driver updated', 'success')
            return redirect(url_for('admin_drivers'))
        return render_template('admin_edit_driver.html', driver=driver)

    @app.route('/admin/parents')
    @login_required
    def admin_parents():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        parents = Parent.query.order_by(Parent.full_name.asc()).all()
        students = Student.query.order_by(Student.full_name.asc()).all()
        return render_template('admin_parents.html', parents=parents, students=students)

    @app.route('/admin/parents/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_parent():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            full_name = request.form['full_name'].strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', 'Parent@123').strip()
            selected_students = request.form.getlist('students')  # optional
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'danger')
            else:
                u = User(email=email, password_hash=generate_password_hash(password), role='parent')
                db.session.add(u); db.session.flush()
                p = Parent(user_id=u.id, full_name=full_name, phone=phone)
                db.session.add(p)
                db.session.flush()
                # assign selected students to this parent (if provided)
                for sid in selected_students:
                    try:
                        s = Student.query.get(int(sid))
                        if s:
                            s.parent_user_id = u.id
                    except Exception:
                        pass
                db.session.commit()
                flash(f'Parent created: {email} / {password}', 'success')
                return redirect(url_for('admin_parents'))
        return render_template('admin_create_parent.html')

    @app.route('/admin/buses')
    @login_required
    def admin_buses():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        buses = Bus.query.order_by(Bus.bus_number.asc()).all()
        drivers = Driver.query.order_by(Driver.full_name.asc()).all()
        return render_template('admin_buses.html', buses=buses, drivers=drivers)

    @app.route('/admin/buses/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_bus():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        drivers = Driver.query.all()
        if request.method == 'POST':
            bus_number = request.form['bus_number'].strip()
            capacity = int(request.form.get('capacity', 0))
            driver_id = request.form.get('driver_id')
            bus = Bus(bus_number=bus_number, capacity=capacity,
                      driver_id=(int(driver_id) if driver_id else None))
            db.session.add(bus)
            db.session.commit()
            flash('Bus created', 'success')
            return redirect(url_for('admin_buses'))
        return render_template('admin_create_bus.html', drivers=drivers)

    @app.route('/admin/buses/edit/<int:bus_id>', methods=['GET', 'POST'])
    @login_required
    def admin_edit_bus(bus_id):
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        bus = Bus.query.get_or_404(bus_id)
        drivers = Driver.query.all()
        if request.method == 'POST':
            bus.bus_number = request.form['bus_number'].strip()
            bus.capacity = int(request.form.get('capacity', 0))
            driver_id = request.form.get('driver_id')
            bus.driver_id = int(driver_id) if driver_id else None
            db.session.commit()
            flash('Bus updated', 'success')
            return redirect(url_for('admin_buses'))
        return render_template('admin_edit_bus.html', bus=bus, drivers=drivers)

    # Admin Students (search-enabled + supply lists for modal)
    @app.route('/admin/students')
    @login_required
    def admin_students():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))

        q = request.args.get('q', '').strip()
        students_query = Student.query
        if q:
            like_q = f"%{q}%"
            students_query = students_query.filter(
                or_(
                    Student.full_name.ilike(like_q),
                    Student.roll_number.ilike(like_q)
                )
            )
        students = students_query.order_by(Student.full_name.asc()).all()
        buses = Bus.query.order_by(Bus.bus_number.asc()).all()
        routes = Route.query.order_by(Route.name.asc()).all()
        parents = Parent.query.order_by(Parent.full_name.asc()).all()
        return render_template('admin_students.html', students=students, buses=buses, routes=routes, parents=parents, q=q)

    @app.route('/admin/students/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_student():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        buses = Bus.query.all()
        routes = Route.query.all()
        parents = Parent.query.all()
        if request.method == 'POST':
            email = request.form['email'].strip().lower()
            full_name = request.form['full_name'].strip()
            phone = request.form.get('phone', '').strip()
            roll = request.form.get('roll_number', '').strip()
            parent_user_id = request.form.get('parent_user_id') or None
            assigned_bus_id = request.form.get('assigned_bus_id') or None
            assigned_route_id = request.form.get('assigned_route_id') or None
            password = request.form.get('password', 'Student@123').strip()
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'danger')
            else:
                u = User(email=email, password_hash=generate_password_hash(password), role='student')
                db.session.add(u)
                db.session.flush()
                s = Student(
                    user_id=u.id, full_name=full_name, phone=phone, roll_number=roll,
                    parent_user_id=(int(parent_user_id) if parent_user_id else None),
                    assigned_bus_id=(int(assigned_bus_id) if assigned_bus_id else None),
                    assigned_route_id=(int(assigned_route_id) if assigned_route_id else None)
                )
                db.session.add(s)
                db.session.commit()
                flash(f'Student created: {email} / {password}', 'success')
                return redirect(url_for('admin_students'))
        return render_template('admin_create_student.html', buses=buses, routes=routes, parents=parents)

    @app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_edit_student(student_id):
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))

        student = Student.query.get(student_id)
        if not student:
            flash('Student not found', 'danger')
            return redirect(url_for('admin_students'))

        parents = Parent.query.all()
        buses = Bus.query.all()
        routes = Route.query.all()

        if request.method == 'POST':
            student.full_name = request.form.get('full_name', student.full_name)
            student.phone = request.form.get('phone', student.phone)
            student.roll_number = request.form.get('roll_number', student.roll_number)

            parent_user_id = request.form.get('parent_user_id') or None
            student.parent_user_id = int(parent_user_id) if parent_user_id else None

            assigned_bus_id = request.form.get('assigned_bus_id') or None
            student.assigned_bus_id = int(assigned_bus_id) if assigned_bus_id else None

            assigned_route_id = request.form.get('assigned_route_id') or None
            student.assigned_route_id = int(assigned_route_id) if assigned_route_id else None

            db.session.commit()
            flash('Student updated successfully', 'success')
            return redirect(url_for('admin_students'))

        return render_template('admin_edit_student.html', student=student, parents=parents, buses=buses, routes=routes)

    @app.route('/admin/parents/<int:parent_id>/edit', methods=['GET', 'POST'])
    @login_required
    def admin_edit_parent(parent_id):
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))

        parent = Parent.query.get(parent_id)
        if not parent:
            flash('Parent not found', 'danger')
            return redirect(url_for('admin_parents'))

        students = Student.query.all()

        if request.method == 'POST':
            selected_student_ids = [int(x) for x in request.form.getlist('students')]
            parent_user_id_val = parent.user_id

            # unassign any previously assigned students that are no longer selected
            for s in Student.query.filter_by(parent_user_id=parent_user_id_val).all():
                if s.id not in selected_student_ids:
                    s.parent_user_id = None

            # assign new selections
            for sid in selected_student_ids:
                s = Student.query.get(sid)
                if s:
                    s.parent_user_id = parent_user_id_val

            db.session.commit()
            flash('Parent–student assignments updated successfully.', 'success')
            return redirect(url_for('admin_parents'))

        assigned_ids = [s.id for s in Student.query.filter_by(parent_user_id=parent.user_id).all()]
        return render_template('admin_edit_parent.html', parent=parent, students=students, assigned_ids=assigned_ids)

    # -----------------------
    # Admin: Routes & Map
    # -----------------------
    @app.route('/admin/map')
    @login_required
    def admin_map():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        db_routes = Route.query.all()
        routes = []
        for r in db_routes:
            routes.append({
                'id': r.id,
                'name': r.name or '',
                'color': r.color or '#3388ff',
                'geojson': r.geojson
            })
        return render_template('admin_map.html', routes=routes)

    @app.route('/admin/save_route', methods=['POST'])
    @login_required
    def admin_save_route():
        if getattr(current_user, 'role', None) != 'admin':
            return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        data = request.get_json()
        name = data.get('name', 'Unnamed Route')
        color = data.get('color', '#3388ff')
        geojson = data.get('geojson')
        if not geojson:
            return jsonify({'status': 'error', 'message': 'No route data provided'}), 400
        try:
            geojson_text = json.dumps(geojson)
        except Exception:
            geojson_text = json.dumps(geojson, default=str)
        r = Route(name=name, color=color, geojson=geojson_text, created_by=current_user.id if getattr(current_user, 'id', None) else None)
        db.session.add(r)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Route saved successfully', 'route_id': r.id})

    # -----------------------
    # Notifications
    # -----------------------
    @app.route('/admin/notifications')
    @login_required
    def admin_notifications():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        notes = Notification.query.order_by(Notification.created_at.desc()).all()
        return render_template('admin_notifications.html', notifications=notes)

    @app.route('/admin/notifications/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_notification():
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            message = request.form.get('message', '').strip()
            send_to_students = bool(request.form.get('students'))
            send_to_parents = bool(request.form.get('parents'))
            if not title or not message:
                flash('Title and message required', 'danger')
            else:
                n = Notification(title=title, message=message, created_by=current_user.id if getattr(current_user, 'id', None) else None)
                db.session.add(n)
                db.session.flush()
                receivers = []
                if send_to_students:
                    receivers += [s.user_id for s in Student.query.all() if s.user_id]
                if send_to_parents:
                    receivers += [p.user_id for p in Parent.query.all() if p.user_id]
                for uid in set(receivers):
                    db.session.add(NotificationReceiver(notification_id=n.id, user_id=uid))
                db.session.commit()
                flash(f'Notification queued to {len(set(receivers))} users', 'success')
                return redirect(url_for('admin_notifications'))
        return render_template('admin_create_notification.html')

    @app.route('/admin/notifications/view/<int:notification_id>')
    @login_required
    def admin_view_notification(notification_id):
        if getattr(current_user, 'role', None) != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        notification = Notification.query.get_or_404(notification_id)
        return render_template('admin_view_notification.html', notification=notification)

    # -----------------------
    # Driver Dashboard & Attendance
    # -----------------------
    @app.route('/driver')
    @login_required
    def driver_dashboard():
        if getattr(current_user, 'role', None) != 'driver':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        drv = Driver.query.filter_by(user_id=current_user.id).first()
        bus = Bus.query.filter_by(driver_id=drv.id).first() if drv else None
        students = Student.query.filter_by(assigned_bus_id=bus.id).all() if bus else []
        return render_template('driver_dashboard.html', driver=drv, bus=bus, students=students)

    @app.route('/driver/attendance', methods=['GET', 'POST'])
    @login_required
    def driver_attendance():
        if getattr(current_user, 'role', None) != 'driver':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))

        drv = Driver.query.filter_by(user_id=current_user.id).first()
        bus = Bus.query.filter_by(driver_id=drv.id).first() if drv else None
        students = Student.query.filter_by(assigned_bus_id=bus.id).all() if bus else []

        slots_display = {
            'pickup1': current_app.config.get('SLOT_PICKUP1'),
            'pickup2': current_app.config.get('SLOT_PICKUP2'),
            'drop1':   current_app.config.get('SLOT_DROP1'),
            'drop2':   current_app.config.get('SLOT_DROP2'),
        }

        if request.method == 'POST':
            chosen_slot = request.form.get('slot')  # e.g. 'pickup1'
            chosen_time = request.form.get('time')  # 'HH:MM'
            if not chosen_slot or not chosen_time:
                flash('Please select a slot and time before submitting.', 'danger')
                return redirect(url_for('driver_attendance'))

            if chosen_slot not in ('pickup1', 'pickup2', 'drop1', 'drop2'):
                flash('Invalid slot selected.', 'danger')
                return redirect(url_for('driver_attendance'))

            try:
                hh, mm = chosen_time.strip().split(':')
                hh_i = int(hh); mm_i = int(mm)
                if not (0 <= hh_i <= 23 and 0 <= mm_i <= 59):
                    raise ValueError()
                attendance_time_obj = dt_time(hh_i, mm_i)
            except Exception:
                flash('Invalid time format. Use HH:MM (24-hour).', 'danger')
                return redirect(url_for('driver_attendance'))

            pickup_or_drop = 'pickup' if chosen_slot.startswith('pickup') else 'drop'
            slot_index = 1 if chosen_slot.endswith('1') else 2

            today = date.today()
            present_ids = [int(x) for x in request.form.getlist('present')]

            for s in students:
                existing = Attendance.query.filter_by(
                    student_id=s.id, attendance_date=today,
                    pickup_or_drop=pickup_or_drop, slot=slot_index
                ).first()
                present = s.id in present_ids
                if existing:
                    existing.present = present
                    if hasattr(existing, 'attendance_time'):
                        try:
                            existing.attendance_time = chosen_time
                        except Exception:
                            pass
                else:
                    att = Attendance(
                        student_id=s.id, driver_id=drv.id if drv else None,
                        bus_id=bus.id if bus else None,
                        route_id=s.assigned_route_id,
                        attendance_date=today,
                        pickup_or_drop=pickup_or_drop,
                        slot=slot_index,
                        present=present
                    )
                    if hasattr(att, 'attendance_time'):
                        try:
                            att.attendance_time = chosen_time
                        except Exception:
                            pass
                    db.session.add(att)
            db.session.commit()
            flash(f'Attendance saved for {chosen_slot} at {chosen_time}', 'success')
            return redirect(url_for('driver_dashboard'))

        return render_template('driver_attendance.html', driver=drv, bus=bus, students=students, slots_display=slots_display)

    # -----------------------
    # Student Dashboard
    # -----------------------
    @app.route('/student')
    @login_required
    def student_dashboard():
        if getattr(current_user, 'role', None) != 'student':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        student = Student.query.filter_by(user_id=current_user.id).first()
        if not student:
            flash('Student profile missing', 'danger')
            return redirect(url_for('landing'))

        assigned_route = None
        if student.assigned_route:
            r = student.assigned_route
            assigned_route = {'id': r.id, 'name': r.name or '', 'color': r.color or '#3388ff', 'geojson': r.geojson}

        attendance = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.attendance_date.desc()).limit(30).all()

        # notifications -> need to convert ORM objects to plain dicts for |tojson usage in templates
        nr_rows = NotificationReceiver.query.filter_by(user_id=current_user.id).all()
        note_ids = [n.notification_id for n in nr_rows]
        notifications = []
        if note_ids:
            note_objs = Notification.query.filter(Notification.id.in_(note_ids)).order_by(Notification.created_at.desc()).all()
            for n in note_objs:
                notifications.append({
                    'id': n.id,
                    'title': getattr(n, 'title', '') or '',
                    'message': getattr(n, 'message', '') or '',
                    'created_at': (n.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(n, 'created_at', None) else '')
                })

        return render_template('student_dashboard.html', student=student, route=assigned_route, attendance=attendance, notifications=notifications)

    # -----------------------
    # Parent Dashboard (FIXED: notifications serialized to plain dicts)
    # -----------------------
    @app.route('/parent')
    @login_required
    def parent_dashboard():
        if getattr(current_user, 'role', None) != 'parent':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))

        # fetch students linked to this parent
        student_objs = Student.query.filter_by(parent_user_id=current_user.id).all()

        # build students list for template (serializable)
        students = []
        for s in student_objs:
            route_dict = None
            if s.assigned_route:
                r = s.assigned_route
                route_dict = {
                    'id': r.id,
                    'name': r.name or '',
                    'color': r.color or '#3388ff',
                    'geojson': r.geojson
                }
            students.append({
                'id': s.id,
                'full_name': s.full_name,
                'roll_number': s.roll_number,
                'route': route_dict
            })

        # fetch NotificationReceiver rows for this parent to get notification ids
        nr_rows = NotificationReceiver.query.filter_by(user_id=current_user.id).all()
        note_ids = [n.notification_id for n in nr_rows]

        # get Notification objects and convert them to plain dicts for tojson usage in templates
        notifications = []
        if note_ids:
            note_objs = Notification.query.filter(Notification.id.in_(note_ids)).order_by(Notification.created_at.desc()).all()
            for n in note_objs:
                notifications.append({
                    'id': n.id,
                    'title': getattr(n, 'title', '') or '',
                    'message': getattr(n, 'message', '') or '',
                    'created_at': (n.created_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(n, 'created_at', None) else '')
                })

        # attendance for the first child (keeps previous behavior)
        attendance = []
        if student_objs:
            sid = student_objs[0].id
            attendance = Attendance.query.filter_by(student_id=sid).order_by(Attendance.attendance_date.desc()).limit(30).all()

        return render_template('parent_dashboard.html',
                               students=students,
                               attendance=attendance,
                               notifications=notifications)

    # -----------------------
    # BILLING & PAYMENTS
    # -----------------------

    @app.route('/admin/subscriptions')
    @login_required
    def admin_subscriptions():
        if current_user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        subscriptions = Subscription.query.all()
        return render_template('admin_subscriptions.html', subscriptions=subscriptions)

    @app.route('/admin/subscriptions/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_subscription():
        if current_user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            price = float(request.form.get('price', 0))
            duration_days = int(request.form.get('duration_days', 30))
            description = request.form.get('description', '').strip()
            
            if not name or price <= 0:
                flash('Please provide valid subscription details', 'danger')
                return render_template('admin_create_subscription.html')
            
            subscription = Subscription(
                name=name,
                price=price,
                duration_days=duration_days,
                description=description
            )
            db.session.add(subscription)
            db.session.commit()
            
            flash(f'Subscription "{name}" created successfully', 'success')
            return redirect(url_for('admin_subscriptions'))
        
        return render_template('admin_create_subscription.html')

    @app.route('/admin/invoices')
    @login_required
    def admin_invoices():
        if current_user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        invoices = Invoice.query.order_by(Invoice.issued_date.desc()).all()
        return render_template('admin_invoices.html', invoices=invoices)

    @app.route('/admin/invoices/create', methods=['GET', 'POST'])
    @login_required
    def admin_create_invoice():
        if current_user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        if request.method == 'POST':
            parent_id = int(request.form.get('parent_id', 0))
            student_id = int(request.form.get('student_id', 0))
            subscription_id = int(request.form.get('subscription_id', 0))
            due_date_str = request.form.get('due_date', '')
            notes = request.form.get('notes', '').strip()
            
            if not parent_id or not student_id or not subscription_id:
                flash('Please select parent, student, and subscription', 'danger')
                return redirect(url_for('admin_create_invoice'))
            
            subscription = Subscription.query.get(subscription_id)
            if not subscription:
                flash('Subscription not found', 'danger')
                return redirect(url_for('admin_create_invoice'))
            
            from datetime import datetime as dt
            due_date = dt.strptime(due_date_str, '%Y-%m-%d')
            
            # Generate invoice number
            import secrets
            invoice_number = f"INV-{dt.now().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"
            
            invoice = Invoice(
                invoice_number=invoice_number,
                parent_id=parent_id,
                student_id=student_id,
                subscription_id=subscription_id,
                amount=subscription.price,
                due_date=due_date,
                notes=notes
            )
            
            db.session.add(invoice)
            db.session.commit()
            
            flash(f'Invoice {invoice_number} created successfully', 'success')
            return redirect(url_for('admin_invoices'))
        
        parents = Parent.query.all()
        # Include all students for the dropdown
        students = Student.query.all()
        subscriptions = Subscription.query.filter_by(is_active=True).all()
        
        if not subscriptions:
            flash('No active subscriptions found. Please create one first.', 'warning')
        
        return render_template('admin_create_invoice.html',
                             parents=parents,
                             students=students,
                             subscriptions=subscriptions)

    @app.route('/api/parent/<int:parent_id>/students')
    @login_required
    def get_parent_students(parent_id):
        """API endpoint to get students linked to a parent"""
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        parent = Parent.query.get(parent_id)
        if not parent:
            return jsonify({'error': 'Parent not found'}), 404
        
        # Get students linked to this parent's user
        students = Student.query.filter_by(parent_user_id=parent.user_id).all()
        
        return jsonify({
            'students': [
                {
                    'id': student.id,
                    'name': student.full_name,
                    'roll': student.roll_number
                }
                for student in students
            ]
        })

    @app.route('/admin/invoices/<int:invoice_id>')
    @login_required
    def admin_view_invoice(invoice_id):
        if current_user.role != 'admin':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        invoice = Invoice.query.get_or_404(invoice_id)
        payments = Payment.query.filter_by(invoice_id=invoice_id).all()
        
        return render_template('admin_view_invoice.html', invoice=invoice, payments=payments)

    @app.route('/admin/invoices/<int:invoice_id>/mark-paid', methods=['POST'])
    @login_required
    def admin_mark_invoice_paid(invoice_id):
        if current_user.role != 'admin':
            return jsonify({'error': 'Access denied'}), 403
        
        invoice = Invoice.query.get_or_404(invoice_id)
        invoice.status = 'paid'
        invoice.paid_date = datetime.utcnow()
        db.session.commit()
        
        flash('Invoice marked as paid', 'success')
        return redirect(url_for('admin_view_invoice', invoice_id=invoice_id))

    @app.route('/parent/invoices')
    @login_required
    def parent_invoices():
        if current_user.role != 'parent':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            flash('Parent profile not found', 'danger')
            return redirect(url_for('landing'))
        
        invoices = Invoice.query.filter_by(parent_id=parent.id).order_by(Invoice.issued_date.desc()).all()
        
        total_pending = sum(inv.amount for inv in invoices if inv.status == 'pending')
        total_paid = sum(inv.amount for inv in invoices if inv.status == 'paid')
        
        return render_template('parent_invoices.html',
                             invoices=invoices,
                             total_pending=total_pending,
                             total_paid=total_paid)

    @app.route('/parent/invoices/<int:invoice_id>')
    @login_required
    def parent_view_invoice(invoice_id):
        if current_user.role != 'parent':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        invoice = Invoice.query.get_or_404(invoice_id)
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        
        if invoice.parent_id != parent.id:
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        payments = Payment.query.filter_by(invoice_id=invoice_id).all()
        
        return render_template('parent_view_invoice.html', invoice=invoice, payments=payments)

    @app.route('/parent/invoices/<int:invoice_id>/pay', methods=['GET', 'POST'])
    @login_required
    def parent_pay_invoice(invoice_id):
        if current_user.role != 'parent':
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        invoice = Invoice.query.get_or_404(invoice_id)
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        
        if invoice.parent_id != parent.id:
            flash('Access denied', 'danger')
            return redirect(url_for('landing'))
        
        if request.method == 'POST':
            payment_method = request.form.get('payment_method', 'credit_card')
            amount = float(request.form.get('amount', invoice.amount))
            transaction_id = request.form.get('transaction_id', '').strip()
            
            if amount <= 0 or amount > invoice.amount:
                flash('Invalid payment amount', 'danger')
                return render_template('parent_pay_invoice.html', invoice=invoice)
            
            payment = Payment(
                invoice_id=invoice_id,
                payment_method=payment_method,
                amount=amount,
                transaction_id=transaction_id or None,
                status='completed'
            )
            
            db.session.add(payment)
            
            # Check if fully paid
            total_paid = sum(p.amount for p in invoice.payments) + amount
            if total_paid >= invoice.amount:
                invoice.status = 'paid'
                invoice.paid_date = datetime.utcnow()
            
            db.session.commit()
            
            flash('Payment recorded successfully', 'success')
            return redirect(url_for('parent_view_invoice', invoice_id=invoice_id))
        
        return render_template('parent_pay_invoice.html', invoice=invoice)

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
            print('✓ Database tables initialized')
        except Exception as e:
            print(f'Database init error: {e}')
    app.run(debug=True)
    

