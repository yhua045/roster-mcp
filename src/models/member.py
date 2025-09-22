"""
Member domain model
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Member:
    """
    Links a person to an Event with a specific role.
    Also known as EventMember.

    Attributes:
        id: Unique identifier (Primary Key)
        event_id: Reference to the Event (Foreign Key)
        role: Role in the event (e.g., '證道', '司會', '詩歌讚美', '招待', '音控')
        name: Name of the person (current identifier)
        person_id: Optional reference to People registry for robust linking
    """

    id: Optional[int] = None
    event_id: int = None
    role: str = None
    name: str = None
    person_id: Optional[int] = None

    # Common role types (can be extended)
    COMMON_ROLES = {
        '證道',      # Preacher
        '司會',      # Host/MC
        '詩歌讚美',  # Worship/Praise
        '招待',      # Usher/Greeter
        '音控',      # Sound Control
        '司琴',      # Pianist
        '領詩',      # Song Leader
        '翻譯',      # Translator
    }

    def validate(self) -> List[str]:
        """
        Validate the Member instance

        Returns:
            List of validation error messages, empty if valid
        """
        errors = []

        if not self.event_id:
            errors.append("Member event_id is required")

        if not self.role:
            errors.append("Member role is required")

        if not self.name and not self.person_id:
            errors.append("Either name or person_id must be provided")

        # Note: Role validation is flexible - accepts free text but logs if not in common roles

        return errors

    def to_dict(self) -> dict:
        """Convert Member to dictionary representation"""
        return {
            "id": self.id,
            "eventId": self.event_id,
            "role": self.role,
            "name": self.name,
            "personId": self.person_id
        }