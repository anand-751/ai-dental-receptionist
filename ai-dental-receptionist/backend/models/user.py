from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class UserProfile:
    """User profile for appointment booking"""
    name: str
    phone: str
    email: str
    address: str
    city: str
    purpose_of_visit: str
    medical_history: Optional[str] = None
    allergies: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "city": self.city,
            "purpose_of_visit": self.purpose_of_visit,
            "medical_history": self.medical_history,
            "allergies": self.allergies,
            "notes": self.notes,
        }

    def to_calendar_description(self) -> str:
        """Format user data for Google Calendar event description"""
        lines = [
            f"Patient Name: {self.name}",
            f"Phone: {self.phone}",
            f"Email: {self.email}",
            f"Address: {self.address}, {self.city}",
            f"Purpose of Visit: {self.purpose_of_visit}",
        ]
        
        if self.medical_history:
            lines.append(f"Medical History: {self.medical_history}")
        if self.allergies:
            lines.append(f"Allergies: {self.allergies}")
        if self.notes:
            lines.append(f"Notes: {self.notes}")
        
        return "\n".join(lines)