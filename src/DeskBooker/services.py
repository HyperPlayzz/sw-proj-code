from DeskBooker.models import db, Desk, Booking, User, Site
from datetime import datetime
from typing import Optional, List

class DeskService:
    @staticmethod
    def search_desks(query: Optional[str] = None, site_id: Optional[int] = None) -> List[Desk]:
        q = Desk.query.join(Site)
        if query:
            like_q = f"%{query}%"
            q = q.filter(Desk.desk_number.ilike(like_q))
        if site_id:
            q = q.filter(Desk.site_id == site_id)
        return q.order_by(Desk.desk_number).all()

class BookingService:
    @staticmethod
    def is_desk_available(desk_id: int, start_time: datetime, end_time: datetime, exclude_booking_id: Optional[int] = None) -> bool:
        # start_time/end_time are datetime objects
        q = Booking.query.filter(Booking.desk_id==desk_id, Booking.start_time < end_time, Booking.end_time > start_time)
        if exclude_booking_id:
            q = q.filter(Booking.id != exclude_booking_id)
        return q.count() == 0

    @staticmethod
    def update_booking(booking_id: int, user_id: int, desk_id: int, start_dt: datetime, end_dt: datetime, admin: bool = False) -> Booking:
        booking = Booking.query.get(booking_id)
        if not booking:
            raise ValueError('Booking not found')
        if not admin and booking.user_id != user_id:
            raise PermissionError('Not authorized')

        # validate types and times
        if not isinstance(start_dt, datetime) or not isinstance(end_dt, datetime):
            raise ValueError('start_dt and end_dt must be datetime objects')
        if end_dt <= start_dt:
            raise ValueError('End time must be after start time')
        if start_dt < datetime.utcnow():
            raise ValueError('Cannot set a booking in the past')

        # ensure desk exists
        desk = Desk.query.get(desk_id)
        if not desk:
            raise ValueError('Desk not found')

        # check availability
        if not BookingService.is_desk_available(desk_id, start_dt, end_dt, exclude_booking_id=booking_id):
            raise ValueError('Desk not available')
        booking.desk_id = desk_id
        booking.start_time = start_dt
        booking.end_time = end_dt
        db.session.commit()
        return booking