"""
Event domain model
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List
from src.models.service_info import ServiceInfo


@dataclass
class Event:
    """
    Represents an actual service occurrence on a specific date.

    Attributes:
        id: Unique identifier (Primary Key)
        date: Date of the event (ISO format: YYYY-MM-DD)
        service_info: Reference to ServiceInfo containing metadata
        members: List of members assigned to this event
    """

    id: Optional[int] = None
    date: date = None
    service_info: Optional[ServiceInfo] = None
    service_info_id: Optional[int] = None  # Foreign key reference

    def validate(self) -> List[str]:
        """
        Validate the Event instance

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        if not self.date:
            errors.append("Event date is required")

        # TODO: Add more validation rules

        return errors

    def to_dict(self) -> dict:
        """Convert Event to dictionary representation"""
        return {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "serviceInfo": self.service_info.to_dict() if self.service_info else None,
            "serviceInfoId": self.service_info_id
        }