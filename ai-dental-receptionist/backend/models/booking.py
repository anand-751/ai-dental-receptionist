# """
# Pydantic models for appointment booking.
# """

# from pydantic import BaseModel, EmailStr
# from datetime import datetime


# class PatientInfo(BaseModel):
#     """Patient information model"""
#     name: str
#     phone: str
#     email: str | None = None
#     date_of_birth: str | None = None


# class AppointmentBooking(BaseModel):
#     """Appointment booking model"""
#     booking_id: str
#     patient: PatientInfo
#     service_type: str
#     appointment_time: datetime
#     duration_minutes: int = 30
#     notes: str | None = None
#     status: str = "confirmed"  


# class BookingConfirmation(BaseModel):
#     """Booking confirmation model"""
#     booking_id: str
#     appointment_time: datetime
#     confirmation_message: str
#     calendar_event_id: str | None = None



"""
Pydantic models for appointment booking.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime


class PatientInfo(BaseModel):
    """Patient information model"""
    name: str
    phone: str
    email: str | None = None
    date_of_birth: str | None = None


class AppointmentBooking(BaseModel):
    """Appointment booking model"""
    booking_id: str
    patient: PatientInfo
    service_type: str
    appointment_time: datetime
    duration_minutes: int = 30
    notes: str | None = None
    status: str = "confirmed"  # confirmed, pending, cancelled


class BookingConfirmation(BaseModel):
    """Booking confirmation model"""
    booking_id: str
    appointment_time: datetime
    confirmation_message: str
    calendar_event_id: str | None = None