from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from DeskBooker.models import db, User, Site, Desk, Booking
from DeskBooker.repositories import UserRepo, DeskRepo, BookingRepo
from DeskBooker.services import BookingService, DeskService
from DeskBooker.db import init_db
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError


# Func to create Flask app
def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = "supersecretkey123"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # keep object attributes available after commit to avoid expired/deleted-instance surprises in tests
    app.config['SQLALCHEMY_EXPIRE_ON_COMMIT'] = False
    if test_config:
        app.config.update(test_config)
    db.init_app(app)

    with app.app_context():
        init_db(app)

    # Decorator to require login for routes
    def login_required(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in first")
                return redirect(url_for("login_page"))
            return func(*args, **kwargs)
        return wrapper

    # Routes
    @app.route('/', methods=['GET', 'POST'])
    # Combined login and registration page for simplicity
    def login_page():
        if request.method == 'POST':
            action = request.form.get('action', 'login')
            
            # Handle registration
            if action == 'register':
                name = request.form['reg_name']
                email = request.form['reg_email']
                password = request.form['reg_password']
                role_id = int(request.form['role'])
                
                if UserRepo.get_by_email(email):
                    flash('Email already registered', 'register')
                    return redirect(url_for('login_page'))
                
                # Attempt to create user and handle validation errors
                try:
                    UserRepo.create(name=name, email=email, password=password, role_id=role_id)
                    flash('Account created successfully! Please log in.', 'register')
                    return redirect(url_for('login_page'))
                except ValueError as e:
                    flash(f'Registration error: {str(e)}', 'register')
                    return redirect(url_for('login_page'))
                except IntegrityError:
                    db.session.rollback()
                    flash('Email already registered', 'register')
                    return redirect(url_for('login_page'))
            
            else:
                # Handle login
                email = request.form['email']
                password = request.form['password']
                user = UserRepo.get_by_email(email)
                if user and check_password_hash(user.password, password):
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['role_id'] = user.role_id
                    return redirect(url_for('dashboard'))
                flash('Incorrect login details', 'login')
                return redirect(url_for('login_page'))
        return render_template('login.html')

# Logout route
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login_page'))

    # Dashboard route
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/book_desk', methods=['GET', 'POST'])
    @login_required
    def book_desk():
        # Handle booking form submission
        if request.method == 'POST':
            try:
                site_id = int(request.form['site_id'])
                desk_id = int(request.form['desk_id'])
            except (ValueError, TypeError):
                flash('Invalid site or desk selection')
                return redirect(url_for('book_desk'))
            start_time = request.form['start_time']
            end_time = request.form['end_time']
            # Validate input and convert times
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
                end_dt = datetime.strptime(end_time, '%Y-%m-%dT%H:%M')
            except ValueError:
                # Invalid datetime format
                flash('Invalid datetime format')
                return redirect(url_for('book_desk'))

            # Validate that start time is in the future and end time is after start time
            if start_dt < datetime.now():
                flash('Cannot book in the past')
                return redirect(url_for('book_desk'))
            
            # Validate that end time is after start time
            if end_dt <= start_dt:
                flash('End time must be after start time')
                return redirect(url_for('book_desk'))

            # Check if desk exists
            try:
                if not BookingService.is_desk_available(desk_id, start_dt, end_dt):
                    flash('Desk not available for this time')
                    return redirect(url_for('book_desk'))

                BookingRepo.create(session['user_id'], desk_id, start_dt, end_dt)
                flash('Desk booked successfully')
            # Handle validation errors from service/repository layer
            except ValueError as e:
                flash(str(e))

        sites = [ {'id': s.id, 'name': s.name} for s in Site.query.order_by(Site.name).all() ]
        desks = [ {'id': d.id, 'desk_number': d.desk_number, 'site_id': d.site_id} for d in Desk.query.order_by(Desk.desk_number).all() ]
        max_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%dT%H:%M')
        min_date = datetime.now().strftime('%Y-%m-%dT%H:%M')
        return render_template('book_desk.html', sites=sites, desks=desks, max_date=max_date, min_date=min_date)

    @app.route('/edit_bookings', methods=['GET', 'POST'])
    @login_required
    def edit_bookings():
        # Edit bookings route
        user_id = session['user_id']
        role_id = session['role_id']
        desks = [ {'id': d.id, 'desk_number': d.desk_number} for d in Desk.query.order_by(Desk.desk_number).all() ]

        # Determine if admin view is enabled based on query/form parameters and user role
        admin_view = False
        q = None
        if request.method == 'GET':
            admin_view = (request.args.get('admin_view') == '1') and (role_id == 1)
            q = request.args.get('q')
        else:
            admin_view = (request.form.get('admin_view') == '1') and (role_id == 1)

        # Handle booking update form submission
        if request.method == 'POST':
            booking_id = int(request.form['booking_id'])
            desk_id = int(request.form['desk_id'])
            start_time_str = request.form['start_time']
            end_time_str = request.form['end_time']
            # Validate input and convert times
            try:
                start_dt = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
                end_dt = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid datetime format')
                return redirect(url_for('edit_bookings'))

            # Validate that start time is in the future and end time is after start time
            if start_dt < datetime.now():
                flash('Cannot set a booking in the past')
                return redirect(url_for('edit_bookings'))
            
            # Validate that end time is after start time
            if end_dt <= start_dt:
                flash('End time must be after start time')
                return redirect(url_for('edit_bookings'))

            # Check if desk exists
            try:
                BookingService.update_booking(booking_id, user_id, desk_id, start_dt, end_dt, admin=(role_id==1 and admin_view))
                flash('Booking updated')

            # Handle validation errors from service layer
            except ValueError as e:
                flash(str(e))
            return redirect(url_for('edit_bookings'))

        # Fetch bookings based on admin view and optional search query
        if role_id == 1 and admin_view:
            page = int(request.args.get('page', 1) or 1)
            per_page = int(request.args.get('per_page', 10) or 10)
            bookings, total = BookingRepo.page(page=page, per_page=per_page, name_query=q)
            total_pages = (total + per_page - 1) // per_page if per_page else 1
            bookings_out = [ b.to_dict() for b in bookings ]

        # Regular user view - show only their bookings
        else:
            bookings = BookingRepo.get_by_user(user_id)
            bookings_out = [ b.to_dict() for b in bookings ]
            page = 1
            per_page = len(bookings_out)
            total = len(bookings_out)
            total_pages = 1

        # provide a single JSON config object for client JS
        config = {
            'apiUrl': url_for('api_bookings'),
            'editUrl': url_for('edit_bookings'),
            'desks': desks,
            'isAdmin': (role_id==1),
            'admin_view': admin_view,
            'q': q,
            'initialPage': page,
            'initialPerPage': per_page,
            'initialTotalPages': total_pages,
            'initialTotal': total
        }

        return render_template('edit_bookings.html', bookings=bookings_out, desks=desks, is_admin=(role_id==1), admin_view=admin_view, q=q, page=page, per_page=per_page, total=total, total_pages=total_pages, config=config)

    @app.route('/lookup_bookings', methods=['GET'])
    @login_required
    def lookup_bookings():
        site_id = request.args.get('site_id')
        desk_q = request.args.get('desk_q', '').strip()

        # Fetch sites for dropdown
        sites = [ {'id': s.id, 'name': s.name} for s in Site.query.order_by(Site.name).all() ]
        selected_site_id = None
        if site_id:
            try:
                selected_site_id = int(site_id)
            except ValueError:
                selected_site_id = None

        # Build query for bookings with joins
        q = Booking.query.join(Desk).join(Site).join(User)
        if selected_site_id:
            q = q.filter(Site.id == selected_site_id)
        if desk_q:
            q = q.filter(Desk.desk_number.ilike(f"%{desk_q}%"))
        q = q.order_by(Booking.start_time)

        bookings = q.all()
        results = []
        for b in bookings:
            results.append({
                'desk_number': b.desk.desk_number if b.desk else '',
                'site_name': b.desk.site.name if b.desk and b.desk.site else '',
                'user_name': b.user.name if b.user else '',
                'start_time': b.start_time.strftime('%Y-%m-%d %H:%M'),
                'end_time': b.end_time.strftime('%Y-%m-%d %H:%M'),
                'start_time_formatted': b.start_time.strftime('%d/%m/%Y %H:%M'),
                'end_time_formatted': b.end_time.strftime('%d/%m/%Y %H:%M')
            })

        return render_template('lookup_bookings.html', sites=sites, selected_site_id=selected_site_id, desk_q=desk_q, bookings=results)

    @app.route('/delete_bookings', methods=['GET', 'POST'])
    @login_required
    def delete_bookings():
        # Delete bookings route
        user_id = session['user_id']
        role_id = session['role_id']

        # Determine if admin view is enabled based on query/form parameters and user role
        admin_view = False
        q = None
        if request.method == 'GET':
            admin_view = (request.args.get('admin_view') == '1') and (role_id == 1)
            q = request.args.get('q')
        else:
            admin_view = (request.form.get('admin_view') == '1') and (role_id == 1)

# Handle booking deletion form submission
        if request.method == 'POST':
            booking_id = int(request.form['booking_id'])
            if role_id == 1 and admin_view:
                BookingRepo.delete(booking_id)
                flash('Booking deleted')
                return redirect(url_for('delete_bookings'))
            booking = BookingRepo.get(booking_id)
            if not booking or booking.user_id != user_id:
                flash('Not authorized to delete this booking')
                return redirect(url_for('delete_bookings'))
            BookingRepo.delete(booking_id)
            flash('Booking deleted')
            return redirect(url_for('delete_bookings'))

        # Fetch bookings based on admin view and optional search query
        if role_id == 1 and admin_view:
            page = int(request.args.get('page', 1) or 1)
            per_page = int(request.args.get('per_page', 10) or 10)
            bookings, total = BookingRepo.page(page=page, per_page=per_page, name_query=q)
            total_pages = (total + per_page - 1) // per_page if per_page else 1
            bookings_out = [ b.to_dict() for b in bookings ]

        # Regular user view - show only their bookings
        else:
            bookings = BookingRepo.get_by_user(user_id)
            bookings_out = [ b.to_dict() for b in bookings ]
            page = 1
            per_page = len(bookings_out)
            total = len(bookings_out)
            total_pages = 1

        # provide config for delete_bookings client JS
        config = {
            'apiUrl': url_for('api_bookings'),
            'deleteUrl': url_for('delete_bookings'),
            'isAdmin': (role_id==1),
            'admin_view': admin_view,
            'q': q,
            'initialPage': page,
            'initialPerPage': per_page,
            'initialTotalPages': total_pages,
            'initialTotal': total
        }

        return render_template('delete_bookings.html', bookings=bookings_out, is_admin=(role_id==1), admin_view=admin_view, q=q, page=page, per_page=per_page, total=total, total_pages=total_pages, config=config)

    @app.route('/account', methods=['GET', 'POST'])
    @login_required
    def account():
        # Account management route
        user_id = session['user_id']
        role_id = session['role_id']
        user = UserRepo.get_by_id(user_id)
        # Handle account update form submission
        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            # Validate input and update user
            if password:
                user.password = generate_password_hash(password)
            user.name = name
            user.email = email
            db.session.commit()
            flash('Account updated')
            return redirect(url_for('account'))
        return render_template('account.html', user={'id': user.id, 'name': user.name, 'email': user.email}, role_id=role_id)

    @app.route('/manage_desks', methods=['GET', 'POST'])
    @login_required
    def manage_desks():
        # Admin-only desk management route
        if session.get('role_id') != 1:
            flash('Admin access required')
            return redirect(url_for('dashboard'))
        # POST actions remain for create/update/delete
        if request.method == 'POST':
            action = request.form['action']
            # Validate input and perform action
            try:
                # iF creating or updating, validate desk number and floor
                if action == 'create':
                    d = Desk(desk_number=request.form['desk_number'], floor=request.form['floor'], site_id=request.form['site_id'])
                    db.session.add(d)
                    db.session.commit()
                    flash('Desk created')

                # If updating, validate that desk exists and then update fields
                elif action == 'update':
                    d = Desk.query.get(request.form['desk_id'])
                    d.desk_number = request.form['desk_number']
                    d.floor = request.form['floor']
                    d.site_id = request.form['site_id']
                    db.session.commit()
                    flash('Desk updated')

                # If deleting, validate that desk exists and then delete
                elif action == 'delete':
                    Desk.query.filter_by(id=request.form['desk_id']).delete()
                    db.session.commit()
                    flash('Desk deleted')
                # Handle validation errors from model layer
            except ValueError as e:
                db.session.rollback()
                flash(str(e))

            return redirect(url_for('manage_desks'))

        
        sites = [ {'id': s.id, 'name': s.name} for s in Site.query.order_by(Site.name).all() ]
        # serve template; table will be fetched via JS from /api/desks
        config = {
            'apiUrl': url_for('api_desks'),
            'sites': sites
        }
        return render_template('manage_desks.html', sites=sites, config=config)

    @app.route('/api/desks')
    @login_required
    def api_desks():
        # admin-only endpoint
        if session.get('role_id') != 1:
            return jsonify({'error': 'Admin required'}), 403
        q = request.args.get('q') or None

        # Validate pagination parameters
        try:
            page = int(request.args.get('page', 1) or 1)
            per_page = int(request.args.get('per_page', 10) or 10)

        # Handle invalid pagination parameters by falling back to defaults
        except ValueError:
            page = 1
            per_page = 10
        site_filter = request.args.get('site_id') or None

        # Validate site filter parameter
        try:
            site_id = int(site_filter) if site_filter else None

        # Handle invalid site filter parameter by ignoring it
        except (ValueError, TypeError):
            site_id = None
        desks, total = DeskRepo.page(page=page, per_page=per_page, desk_query=q, site_id=site_id)
        total_pages = (total + per_page - 1) // per_page if per_page else 1
        desks_out = [ { 'id': d.id, 'desk_number': d.desk_number, 'floor': d.floor, 'site_id': d.site_id, 'site_name': d.site.name if d.site else '' } for d in desks ]
        return jsonify({ 'desks': desks_out, 'page': page, 'per_page': per_page, 'total': total, 'total_pages': total_pages })

    @app.route('/manage_sites', methods=['GET', 'POST'])
    @login_required
    def manage_sites():
        # Admin-only site management route
        if session.get('role_id') != 1:
            flash('Admin access required')
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            action = request.form['action']
            if action == 'create':
                s = Site(name=request.form['name'])
                db.session.add(s)
                db.session.commit()
                flash('Site created')
            elif action == 'update':
                s = Site.query.get(request.form['site_id'])
                s.name = request.form['name']
                db.session.commit()
                flash('Site updated')
            elif action == 'delete':
                Site.query.filter_by(id=request.form['site_id']).delete()
                db.session.commit()
                flash('Site deleted')
            return redirect(url_for('manage_sites'))
        sites = [ {'id': s.id, 'name': s.name} for s in Site.query.order_by(Site.name).all() ]
        return render_template('sites.html', sites=sites)

    @app.route('/api/bookings')
    @login_required
    def api_bookings():
        role_id = session.get('role_id')
        user_id = session.get('user_id')
        admin_view = (request.args.get('admin_view') == '1') and (role_id == 1)
        q = request.args.get('q') or None
        try:
            page = int(request.args.get('page', 1) or 1)
            per_page = int(request.args.get('per_page', 10) or 10)
        except ValueError:
            page = 1
            per_page = 10

        if admin_view:
            bookings, total = BookingRepo.page(page=page, per_page=per_page, name_query=q)
            total_pages = (total + per_page - 1) // per_page if per_page else 1
            b_out = [ b.to_dict() for b in bookings ]
        else:
            bookings = BookingRepo.get_by_user(user_id)
            total = len(bookings)
            page = 1
            per_page = total or 10
            total_pages = 1
            b_out = [ b.to_dict() for b in bookings ]

        return jsonify({ 'bookings': b_out, 'page': page, 'per_page': per_page, 'total': total, 'total_pages': total_pages })

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)