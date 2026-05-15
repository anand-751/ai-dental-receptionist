"""
Pydantic models for appointment booking.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class PatientInfo(BaseModel):
    """Patient information model"""
    name: str
    phone: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None


class AppointmentBooking(BaseModel):
    """Appointment booking model"""
    booking_id: str
    patient: PatientInfo
    service_type: str
    appointment_time: datetime
    duration_minutes: int = 30
    notes: Optional[str] = None
    status: str = "confirmed"


class BookingConfirmation(BaseModel):
    """Booking confirmation model"""
    booking_id: str
    appointment_time: datetime
    confirmation_message: str
    calendar_event_id: Optional[str] = None


class Booking(BaseModel):
    """
    Lightweight booking model used in conversation session.
    payment_status: None → "pending" → "completed"
    """
    patient_name: str
    patient_phone: str
    date: str
    time: str
    payment_status: Optional[str] = "pending"
    stripe_session_id: Optional[str] = None