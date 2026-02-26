"""
Tests for booking module.
"""

import pytest
from datetime import datetime
from models.booking import AppointmentBooking, PatientInfo


def test_create_booking():
    """Test creating an appointment booking"""
    patient = PatientInfo(
        name="John Doe",
        phone="555-1234",
        email="john@example.com"
    )
    booking = AppointmentBooking(
        booking_id="booking_001",
        patient=patient,
        service_type="cleaning",
        appointment_time=datetime.now()
    )
    assert booking.booking_id == "booking_001"
    assert booking.patient.name == "John Doe"


def test_booking_status():
    """Test booking status"""
    patient = PatientInfo(
        name="Jane Doe",
        phone="555-5678"
    )
    booking = AppointmentBooking(
        booking_id="booking_002",
        patient=patient,
        service_type="checkup",
        appointment_time=datetime.now(),
        status="confirmed"
    )
    assert booking.status == "confirmed"
