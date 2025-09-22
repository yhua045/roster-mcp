"""
ServiceInfo domain model
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List


@dataclass
class ServiceInfo:
    """
    Holds metadata for a service/session.

    Attributes:
        id: Unique identifier (Primary Key)
        footnote: Optional notes about the service
        skip_service: Whether the service is skipped
        skip_reason: Reason for skipping the service
        date: Date of the service (ISO format: YYYY-MM-DD)
        category: Service category (e.g., 'chinese', 'english', 'sundayschool')
    """

    id: Optional[int] = None
    footnote: Optional[str] = None
    skip_service: bool = False
    skip_reason: Optional[str] = None
    date: date = None
    category: str = None

    # Valid category values
    VALID_CATEGORIES = {'chinese', 'english', 'sundayschool'}

    def validate(self) -> List[str]:
        """
        Validate the ServiceInfo instance

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        if not self.date:
            errors.append("ServiceInfo date is required")

        if not self.category:
            errors.append("ServiceInfo category is required")
        elif self.category.lower() not in self.VALID_CATEGORIES:
            errors.append(f"Invalid category: {self.category}. Must be one of {self.VALID_CATEGORIES}")

        if self.skip_service and not self.skip_reason:
            errors.append("Skip reason is required when skip_service is True")

        return errors

    def to_dict(self) -> dict:
        """Convert ServiceInfo to dictionary representation"""
        return {
            "id": self.id,
            "footnote": self.footnote,
            "skipService": self.skip_service,
            "skipReason": self.skip_reason,
            "date": self.date.isoformat() if self.date else None,
            "category": self.category.lower() if self.category else None
        }