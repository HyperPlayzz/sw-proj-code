from DeskBooker.models import db, Desk, Booking, User, Site
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from typing import Optional, List, Tuple

class UserRepo:
    @staticmethod
    # Get user by email, returns None if not found
    def get_by_email(email: str) -> Optional[User]:
        return User.query.filter_by(email=email).first()

    @staticmethod
    # Get user by id, returns None if not found
    def get_by_id(user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    @staticmethod
    # Create a user with validation, returns the created User object
    def create(name: str, email: str, password: str, role_id: int = 2) -> User:
        if not name or len(name.strip()) == 0:
            raise ValueError('Name required')
        if len(name) > 100:
            raise ValueError('Name too long (max 100 characters)')
        if not email or len(email.strip()) == 0:
            raise ValueError('Email required')
        if '@' not in email:
            raise ValueError('Invalid email format')
        if len(email) > 120:
            raise ValueError('Email too long (max 120 characters)')
        if len(email) < 5:
            raise ValueError('Email too short (min 5 characters)')
        if not password or len(password) == 0:
            raise ValueError('Password required')
        if len(password) < 6:
            raise ValueError('Password too short (min 6 characters)')
        if len(password) > 255:
            raise ValueError('Password too long')
        if role_id not in [1, 2]:
            raise ValueError('Invalid role')
        
        hashed = generate_password_hash(password)
        u = User(name=name, email=email, password=hashed, role_id=role_id)
        db.session.add(u)
        db.session.commit()
        return u

class DeskRepo:
    @staticmethod
    # Get all desks with optional search and site filter
    def all() -> List[Desk]:
        return Desk.query.order_by(Desk.desk_number).all()

    @staticmethod
    # Get desks with optional search and site filter
    def search(desk_query: Optional[str] = None, site_id: Optional[int] = None) -> List[Desk]:
        q = Desk.query.join(Site)
        if desk_query:
            q = q.filter(Desk.desk_number.ilike(f"%{desk_query}%"))
        if site_id:
            q = q.filter(Desk.site_id==site_id)
        return q.order_by(Desk.desk_number).all()

    @staticmethod
    # Get paginated desks with optional search and site filter
    def page(page: int = 1, per_page: int = 10, desk_query: Optional[str] = None, site_id: Optional[int] = None) -> Tuple[List[Desk], int]:
        q = Desk.query.join(Site)
        if desk_query:
            q = q.filter(Desk.desk_number.ilike(f"%{desk_query}%"))
        if site_id:
            q = q.filter(Desk.site_id==site_id)
        total = q.count()
        items = q.order_by(Desk.desk_number).limit(per_page).offset((page-1)*per_page).all()
        return items, total

class BookingRepo:
    # Get paginated bookings with optional user name filter
    @staticmethod
    def page(page: int = 1, per_page: int = 10, name_query: Optional[str] = None) -> Tuple[List[Booking], int]:
        q = Booking.query.join(User).join(Desk)
        if name_query:
            q = q.filter(User.name.ilike(f"%{name_query}%"))
        total = q.count()
        items = q.order_by(Booking.start_time).limit(per_page).offset((page-1)*per_page).all()
        return items, total

    # Get all bookings for a user
    @staticmethod
    def get_by_user(user_id: int) -> List[Booking]:
        return Booking.query.join(Desk).join(User).filter(Booking.user_id==user_id).order_by(Booking.start_time).all()

    # Get booking by id, returns None if not found
    @staticmethod
    def get(booking_id: int) -> Optional[Booking]:
        return Booking.query.get(booking_id)

    # Create a booking with validation
    @staticmethod
    def create(user_id: int, desk_id: int, start_time: datetime, end_time: datetime) -> Booking:
        if not user_id or user_id <= 0:
            raise ValueError('Invalid user')
        if not desk_id or desk_id <= 0:
            raise ValueError('Invalid desk')
        if start_time is None:
            raise ValueError('Start time required')
        if end_time is None:
            raise ValueError('End time required')
        if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
            raise ValueError('Invalid datetime format')
        if end_time <= start_time:
            raise ValueError('End time must be after start time')
        
        b = Booking(user_id=user_id, desk_id=desk_id, start_time=start_time, end_time=end_time)
        db.session.add(b)
        db.session.commit()
        return b

#Method to delete booking by id, returns True if deleted, False if not found
    @staticmethod
    def delete(booking_id: int) -> bool:
        b = Booking.query.get(booking_id)
        if b:
            db.session.delete(b)
            db.session.commit()
            return True
        return False