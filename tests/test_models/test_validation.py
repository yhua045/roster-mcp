"""
Unit tests for model validation
"""

import unittest
from datetime import date
from src.models import Event, ServiceInfo, Member


class TestEventValidation(unittest.TestCase):
    """Test Event model validation"""

    def test_event_requires_date(self):
        """Test that Event requires a date"""
        event = Event()
        errors = event.validate()
        self.assertIn("Event date is required", errors)

    def test_valid_event(self):
        """Test valid Event passes validation"""
        event = Event(date=date(2024, 1, 14))
        errors = event.validate()
        self.assertEqual(len(errors), 0)


class TestServiceInfoValidation(unittest.TestCase):
    """Test ServiceInfo model validation"""

    def test_service_info_requires_date(self):
        """Test that ServiceInfo requires a date"""
        service_info = ServiceInfo(category="chinese")
        errors = service_info.validate()
        self.assertIn("ServiceInfo date is required", errors)

    def test_service_info_requires_category(self):
        """Test that ServiceInfo requires a category"""
        service_info = ServiceInfo(date=date(2024, 1, 14))
        errors = service_info.validate()
        self.assertIn("ServiceInfo category is required", errors)

    def test_invalid_category(self):
        """Test that invalid category is rejected"""
        service_info = ServiceInfo(
            date=date(2024, 1, 14),
            category="invalid"
        )
        errors = service_info.validate()
        self.assertTrue(any("Invalid category" in e for e in errors))

    def test_valid_categories(self):
        """Test that valid categories are accepted"""
        for category in ['chinese', 'english', 'sundayschool']:
            service_info = ServiceInfo(
                date=date(2024, 1, 14),
                category=category
            )
            errors = service_info.validate()
            self.assertEqual(len(errors), 0)

    def test_skip_service_requires_reason(self):
        """Test that skip_service requires a reason"""
        service_info = ServiceInfo(
            date=date(2024, 1, 14),
            category="chinese",
            skip_service=True
        )
        errors = service_info.validate()
        self.assertIn("Skip reason is required when skip_service is True", errors)

    def test_valid_skip_service(self):
        """Test valid skip_service with reason"""
        service_info = ServiceInfo(
            date=date(2024, 1, 14),
            category="chinese",
            skip_service=True,
            skip_reason="Holiday"
        )
        errors = service_info.validate()
        self.assertEqual(len(errors), 0)


class TestMemberValidation(unittest.TestCase):
    """Test Member model validation"""

    def test_member_requires_event_id(self):
        """Test that Member requires event_id"""
        member = Member(role="證道", name="John")
        errors = member.validate()
        self.assertIn("Member event_id is required", errors)

    def test_member_requires_role(self):
        """Test that Member requires a role"""
        member = Member(event_id=1, name="John")
        errors = member.validate()
        self.assertIn("Member role is required", errors)

    def test_member_requires_identifier(self):
        """Test that Member requires either name or person_id"""
        member = Member(event_id=1, role="證道")
        errors = member.validate()
        self.assertIn("Either name or person_id must be provided", errors)

    def test_valid_member_with_name(self):
        """Test valid Member with name"""
        member = Member(event_id=1, role="證道", name="Pastor Chen")
        errors = member.validate()
        self.assertEqual(len(errors), 0)

    def test_valid_member_with_person_id(self):
        """Test valid Member with person_id"""
        member = Member(event_id=1, role="證道", person_id=42)
        errors = member.validate()
        self.assertEqual(len(errors), 0)

    def test_valid_member_with_both_identifiers(self):
        """Test valid Member with both name and person_id"""
        member = Member(
            event_id=1,
            role="證道",
            name="Pastor Chen",
            person_id=42
        )
        errors = member.validate()
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()