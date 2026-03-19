from DeskBooker.models import db, Role, Site, User, Desk, Booking
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# DB initialisation
def init_db(app=None):
    """
    Initialize DB schema and populate default data if tables are empty.
    Call with a Flask app instance inside the app factory after db.init_app(app).
    This function is idempotent and will only insert data into empty tables.
    """

    with app.app_context():
        # Create tables
        db.create_all()

        # Roles: Administrator and User
        if Role.query.count() == 0:
            admin_role = Role(name='Administrator')
            user_role = Role(name='User')
            db.session.add_all([admin_role, user_role])
            db.session.commit()

        # Sites: 10 entries
        if Site.query.count() == 0:
            site_names = [
                'Edinburgh','Basildon','London','Manchester','Birmingham',
                'Leeds','Glasgow','Cardiff','Bristol','Liverpool'
            ]
            for name in site_names:
                db.session.add(Site(name=name))
            db.session.commit()

        # Users: 10 users, first is Administrator (ALWAYS, REMEMBER THIS!!)
        if User.query.count() == 0:
            users = [
                ("Alice", "alice@test.com", "pass", 'Administrator'),
                ("Bob", "bob@test.com", "pass", 'User'),
                ("Charlie", "charlie@test.com", "pass", 'User'),
                ("David", "david@test.com", "pass", 'User'),
                ("Eve", "eve@test.com", "pass", 'User'),
                ("Frank", "frank@test.com", "pass", 'User'),
                ("Grace", "grace@test.com", "pass", 'User'),
                ("Hank", "hank@test.com", "pass", 'User'),
                ("Ivy", "ivy@test.com", "pass", 'User'),
                ("Jack", "jack@test.com", "pass", 'User'),
            ]
            roles = {r.name: r.id for r in Role.query.all()}
            for name, email, pwd, role_name in users:
                role_id = roles.get(role_name) or roles.get('User')
                u = User(name=name, email=email, password=generate_password_hash(pwd), role_id=role_id)
                db.session.add(u)
            db.session.commit()

        # Desks: 10 desks with site associations
        if Desk.query.count() == 0:
            desks = [
                ("SH 101A", 1, 1), ("SH 102B", 1, 1), ("SH 103C", 1, 1),
                ("SH 201A", 2, 2), ("SH 202B", 2, 2), ("MH 101A", 1, 3),
                ("MH 102B", 1, 3), ("MH 201A", 2, 4), ("MH 202B", 2, 4), ("MH 203C", 2, 5)
            ]
            for desk_number, floor, site_id in desks:
                db.session.add(Desk(desk_number=desk_number, floor=floor, site_id=site_id))
            db.session.commit()

        # Bookings: 10 bookings (one per user) non-overlapping
        if Booking.query.count() == 0:
            base = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            for i in range(10):
                user = User.query.order_by(User.id).offset(i).first()
                desk = Desk.query.order_by(Desk.id).offset(i).first()
                if not user or not desk:
                    continue
                start_dt = base + timedelta(days=i)
                end_dt = start_dt + timedelta(hours=4)
                b = Booking(user_id=user.id, desk_id=desk.id, start_time=start_dt, end_time=end_dt)
                db.session.add(b)
            db.session.commit()

# Data access functions
def get_all_desks():
    return [{'id': d.id, 'desk_number': d.desk_number, 'floor': d.floor, 'site_id': d.site_id} for d in Desk.query.order_by(Desk.desk_number).all()]

# Get all sites for dropdowns
def get_all_sites():
    return [{'id': s.id, 'name': s.name} for s in Site.query.order_by(Site.name).all()]

# Get user by email, returns None if not found
def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

# Get user by ID, returns None if not found
def get_user_by_id(user_id):
    return User.query.get(user_id)

# Check password for a given email, returns True if valid, False otherwise
def check_password(email, password):
    user = get_user_by_email(email)
    return check_password_hash(user.password, password) if user else False

# Admin function to update a user by ID
def update_user(user_id, name, email, password=None):
    user = get_user_by_id(user_id)
    if user:
        user.name = name
        user.email = email
        if password:
            user.password = generate_password_hash(password)
        db.session.commit()

# Get all users (for admin view)
def get_all_users():
    return [{'id': u.id, 'name': u.name, 'email': u.email, 'role_id': u.role_id} for u in User.query.all()]

# Get all bookings for a user
def get_user_bookings(user_id):
    return Booking.query.filter_by(user_id=user_id).order_by(Booking.start_time).all()

# Get all bookings with user and desk info (for admin view)
def get_all_bookings():
    return Booking.query.join(Desk).join(User).order_by(Booking.start_time).all()

# Admin function to create a desk
def create_desk(desk_number, floor, site_id):
    db.session.add(Desk(desk_number=desk_number, floor=floor, site_id=site_id))
    db.session.commit()

# Admin function to update a desk by ID
def update_desk(desk_id, desk_number, floor, site_id):
    desk = Desk.query.get(desk_id)
    if desk:
        desk.desk_number = desk_number
        desk.floor = floor
        desk.site_id = site_id
        db.session.commit()

# Admin function to delete a desk by ID (also deletes associated bookings via cascade)
def delete_desk(desk_id):
    desk = Desk.query.get(desk_id)
    if desk:
        db.session.delete(desk)
        db.session.commit()

# Get desks by site ID
def get_desks_by_site(site_id):
    return Desk.query.filter_by(site_id=site_id).order_by(Desk.desk_number).all()

# Search desks with optional query and site filter
def search_desks(desk_query=None, site_id=None):
    query = Desk.query.join(Site)
    if desk_query:
        query = query.filter(Desk.desk_number.ilike(f"%{desk_query}%"))
    if site_id:
        query = query.filter(Desk.site_id == site_id)
    return query.order_by(Desk.desk_number).all()

# Admin function to create a site
def create_site(name):
    db.session.add(Site(name=name))
    db.session.commit()

# Admin function to update a site by ID
def update_site(site_id, name):
    site = Site.query.get(site_id)
    if site:
        site.name = name
        db.session.commit()

# Admin function to delete a site by ID (also deletes associated desks and bookings via cascade)
def delete_site(site_id):
    site = Site.query.get(site_id)
    if site:
        db.session.delete(site)
        db.session.commit()

# Create a booking with validation
def create_booking(user_id, desk_id, start_time, end_time):
    fmt_input = "%Y-%m-%dT%H:%M"
    start_dt = datetime.strptime(start_time, fmt_input)
    end_dt = datetime.strptime(end_time, fmt_input)
    db.session.add(Booking(user_id=user_id, desk_id=desk_id, start_time=start_dt, end_time=end_dt))
    db.session.commit()

# Update a booking with validation
def update_booking(booking_id, user_id, desk_id, start_time, end_time):
    booking = Booking.query.get(booking_id)
    if booking:
        booking.desk_id = desk_id
        start_time = start_time.replace("T", " ")
        end_time = end_time.replace("T", " ")
        fmt = "%Y-%m-%d %H:%M"
        start_dt = datetime.strptime(start_time, fmt)
        end_dt = datetime.strptime(end_time, fmt)
        booking.start_time = start_dt
        booking.end_time = end_dt
        db.session.commit()

# Admin function to update a booking without user_id check
def update_booking_admin(booking_id, desk_id, start_time, end_time):
    update_booking(booking_id, None, desk_id, start_time, end_time)

# Admin function to delete a booking by ID
def delete_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        db.session.delete(booking)
        db.session.commit()

# Check if a desk is available for the given time range, excluding a specific booking ID if provided (for updates)
def is_desk_available(desk_id, start_time, end_time, exclude_booking_id=None):
    start_time = start_time.replace("T", " ")
    end_time = end_time.replace("T", " ")
    fmt = "%Y-%m-%d %H:%M"
    start_dt = datetime.strptime(start_time, fmt)
    end_dt = datetime.strptime(end_time, fmt)
    query = Booking.query.filter_by(desk_id=desk_id).filter(Booking.start_time < end_dt, Booking.end_time > start_dt)
    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)
    return query.count() == 0

# Additional functions for admin booking search and pagination
def search_bookings_by_user_name(name_query):
    like_q = f"%{name_query}%"
    return Booking.query.join(User).filter(User.name.ilike(like_q)).order_by(Booking.start_time).all()

# Get paginated bookings with optional user name filter
def get_bookings_page(page=1, per_page=10, name_query=None):
    query = Booking.query.join(User).join(Desk)
    if name_query:
        query = query.filter(User.name.ilike(f"%{name_query}%"))
    total = query.count()
    bookings = query.order_by(Booking.start_time).limit(per_page).offset((page-1)*per_page).all()
    return bookings, total

# Get booking by id, returns None if not found
def get_booking_by_id(booking_id):
    return Booking.query.filter(Booking.id==booking_id).join(Desk).join(User).first()