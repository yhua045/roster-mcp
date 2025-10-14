"""
Unit tests for AIAgent
"""

import unittest
from unittest.mock import Mock
from datetime import date, timedelta
import json
import uuid

from src.services.ai_agent import AIAgent
from src.services.roster_api_client import RosterAPIClient
from src.exceptions import InvalidCategoryError, APIError


class TestAIAgentInit(unittest.TestCase):
    """Test AIAgent initialization"""

    def test_init(self):
        """Test AIAgent initialization with API client"""
        mock_client = Mock(spec=RosterAPIClient)
        agent = AIAgent(mock_client)
        self.assertEqual(agent.api_client, mock_client)


class TestFetchLastThreeMonths(unittest.TestCase):
    """Test fetch_last_three_months method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = AIAgent(self.mock_client)

    def test_fetch_last_three_months_no_category(self):
        """Test fetching events without category filter"""
        mock_events = [
            {"id": 1, "date": "2024-01-01"},
            {"id": 2, "date": "2024-01-08"}
        ]
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.fetch_last_three_months()

        # Verify correct date range (today - 90 days to today)
        today = date.today()
        from_date = today - timedelta(days=90)

        self.mock_client.get_events.assert_called_once_with(
            category=None,
            from_date=from_date,
            to_date=today
        )
        self.assertEqual(result, mock_events)

    def test_fetch_last_three_months_with_category(self):
        """Test fetching events with category filter"""
        mock_events = [
            {"id": 1, "date": "2024-01-01", "category": "chinese"},
            {"id": 2, "date": "2024-01-08", "category": "chinese"}
        ]
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.fetch_last_three_months(category="chinese")

        # Verify category was passed
        today = date.today()
        from_date = today - timedelta(days=90)

        self.mock_client.get_events.assert_called_once_with(
            category="chinese",
            from_date=from_date,
            to_date=today
        )
        self.assertEqual(result, mock_events)

    def test_fetch_last_three_months_empty_result(self):
        """Test fetching events with empty result"""
        self.mock_client.get_events.return_value = []

        result = self.agent.fetch_last_three_months()

        self.assertEqual(result, [])

    def test_fetch_last_three_months_invalid_category(self):
        """Test that invalid category raises error"""
        self.mock_client.get_events.side_effect = InvalidCategoryError(
            "invalid",
            {'chinese', 'english', 'sundayschool'}
        )

        with self.assertRaises(InvalidCategoryError):
            self.agent.fetch_last_three_months(category="invalid")

    def test_fetch_last_three_months_api_error(self):
        """Test that API errors are propagated"""
        self.mock_client.get_events.side_effect = APIError("Network error")

        with self.assertRaises(APIError):
            self.agent.fetch_last_three_months()

    def test_fetch_last_three_months_date_range(self):
        """Test that the date range is exactly 90 days"""
        self.mock_client.get_events.return_value = []

        self.agent.fetch_last_three_months()

        # Verify the call
        call_args = self.mock_client.get_events.call_args
        from_date = call_args[1]['from_date']
        to_date = call_args[1]['to_date']

        # Check it's exactly 90 days
        delta = to_date - from_date
        self.assertEqual(delta.days, 90)

        # Check to_date is today
        self.assertEqual(to_date, date.today())


class TestEvaluateAvailabilityPlaceholder(unittest.TestCase):
    """Test evaluate_availability_placeholder method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = AIAgent(self.mock_client)

    def test_evaluate_availability_placeholder_basic(self):
        """Test placeholder availability with basic member list"""
        members = [
            {"name": "張三", "role": "證道"},
            {"name": "李四", "role": "司會"}
        ]

        result = self.agent.evaluate_availability_placeholder(members)

        # Check structure
        self.assertEqual(result["status"], "placeholder")
        self.assertIn("evaluation_date", result)
        self.assertIn("members", result)

        # Check that all members are included
        self.assertIn("張三", result["members"])
        self.assertIn("李四", result["members"])

        # Check default availability
        self.assertTrue(result["members"]["張三"]["available"])
        self.assertTrue(result["members"]["李四"]["available"])

    def test_evaluate_availability_placeholder_deterministic(self):
        """Test that placeholder returns deterministic results"""
        members = [
            {"name": "張三", "role": "證道"}
        ]

        result1 = self.agent.evaluate_availability_placeholder(members)
        result2 = self.agent.evaluate_availability_placeholder(members)

        # Both should mark members as available
        self.assertEqual(
            result1["members"]["張三"]["available"],
            result2["members"]["張三"]["available"]
        )

    def test_evaluate_availability_placeholder_empty_members(self):
        """Test placeholder with empty member list"""
        members = []

        result = self.agent.evaluate_availability_placeholder(members)

        self.assertEqual(result["status"], "placeholder")
        self.assertEqual(result["members"], {})

    def test_evaluate_availability_placeholder_duplicate_names(self):
        """Test placeholder with duplicate member names"""
        members = [
            {"name": "張三", "role": "證道"},
            {"name": "張三", "role": "司會"},
            {"name": "李四", "role": "招待"}
        ]

        result = self.agent.evaluate_availability_placeholder(members)

        # Should only have 2 unique members
        self.assertEqual(len(result["members"]), 2)
        self.assertIn("張三", result["members"])
        self.assertIn("李四", result["members"])

    def test_evaluate_availability_placeholder_missing_names(self):
        """Test placeholder with members missing name field"""
        members = [
            {"role": "證道"},  # No name
            {"name": "李四", "role": "司會"}
        ]

        result = self.agent.evaluate_availability_placeholder(members)

        # Should only include member with name
        self.assertEqual(len(result["members"]), 1)
        self.assertIn("李四", result["members"])

    def test_evaluate_availability_placeholder_structure(self):
        """Test that placeholder output has correct structure"""
        members = [{"name": "張三", "role": "證道"}]

        result = self.agent.evaluate_availability_placeholder(members)

        # Check top-level structure
        self.assertIn("status", result)
        self.assertIn("evaluation_date", result)
        self.assertIn("members", result)

        # Check member structure
        member_data = result["members"]["張三"]
        self.assertIn("available", member_data)
        self.assertIn("preferences", member_data)
        self.assertIn("constraints", member_data)
        self.assertIsInstance(member_data["available"], bool)
        self.assertIsInstance(member_data["preferences"], dict)
        self.assertIsInstance(member_data["constraints"], list)


class TestBuildAIPayload(unittest.TestCase):
    """Test build_ai_payload method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = AIAgent(self.mock_client)

        # Sample data
        self.historical_events = [
            {"id": 1, "date": "2024-01-01", "category": "chinese"},
            {"id": 2, "date": "2024-01-08", "category": "chinese"}
        ]
        self.availability = {
            "status": "placeholder",
            "members": {
                "張三": {"available": True},
                "李四": {"available": True}
            }
        }

    def test_build_ai_payload_basic(self):
        """Test building AI payload with basic parameters"""
        payload = self.agent.build_ai_payload(
            self.historical_events,
            self.availability,
            months_ahead=3,
            category="chinese"
        )

        # Check top-level structure
        self.assertIn("metadata", payload)
        self.assertIn("historical_events", payload)
        self.assertIn("availability", payload)
        self.assertIn("generation_params", payload)

        # Check metadata
        self.assertEqual(payload["metadata"]["category"], "chinese")
        self.assertIn("generation_request_id", payload["metadata"])
        self.assertIn("date_range", payload["metadata"])
        self.assertIn("generated_at", payload["metadata"])

        # Check data is included
        self.assertEqual(payload["historical_events"], self.historical_events)
        self.assertEqual(payload["availability"], self.availability)

        # Check generation params
        self.assertEqual(payload["generation_params"]["months_ahead"], 3)

    def test_build_ai_payload_unique_request_id(self):
        """Test that each payload gets a unique request ID"""
        payload1 = self.agent.build_ai_payload(
            self.historical_events,
            self.availability
        )
        payload2 = self.agent.build_ai_payload(
            self.historical_events,
            self.availability
        )

        request_id1 = payload1["metadata"]["generation_request_id"]
        request_id2 = payload2["metadata"]["generation_request_id"]

        self.assertNotEqual(request_id1, request_id2)

        # Check they are valid UUIDs
        uuid.UUID(request_id1)  # Will raise if invalid
        uuid.UUID(request_id2)  # Will raise if invalid

    def test_build_ai_payload_date_range_calculation(self):
        """Test that date range is calculated correctly"""
        payload = self.agent.build_ai_payload(
            self.historical_events,
            self.availability,
            months_ahead=3
        )

        date_range = payload["metadata"]["date_range"]
        from_date = date.fromisoformat(date_range["from"])
        to_date = date.fromisoformat(date_range["to"])

        # From should be today
        self.assertEqual(from_date, date.today())

        # To should be approximately 3 months ahead (90 days)
        expected_to_date = date.today() + timedelta(days=90)
        self.assertEqual(to_date, expected_to_date)

    def test_build_ai_payload_different_months_ahead(self):
        """Test with different months_ahead values"""
        for months in [1, 2, 3, 6, 12]:
            with self.subTest(months=months):
                payload = self.agent.build_ai_payload(
                    self.historical_events,
                    self.availability,
                    months_ahead=months
                )

                self.assertEqual(payload["generation_params"]["months_ahead"], months)

                # Check date range
                date_range = payload["metadata"]["date_range"]
                to_date = date.fromisoformat(date_range["to"])
                expected_to = date.today() + timedelta(days=30 * months)
                self.assertEqual(to_date, expected_to)

    def test_build_ai_payload_without_category(self):
        """Test building payload without category"""
        payload = self.agent.build_ai_payload(
            self.historical_events,
            self.availability
        )

        self.assertIsNone(payload["metadata"]["category"])

    def test_build_ai_payload_invalid_months_ahead(self):
        """Test that invalid months_ahead raises error"""
        invalid_values = [0, -1, -10]

        for invalid_months in invalid_values:
            with self.subTest(months=invalid_months):
                with self.assertRaises(ValueError) as context:
                    self.agent.build_ai_payload(
                        self.historical_events,
                        self.availability,
                        months_ahead=invalid_months
                    )
                self.assertIn("must be positive", str(context.exception))

    def test_build_ai_payload_json_serializable(self):
        """Test that payload is JSON serializable"""
        payload = self.agent.build_ai_payload(
            self.historical_events,
            self.availability,
            months_ahead=3,
            category="chinese"
        )

        # This should not raise an exception
        json_str = json.dumps(payload)
        self.assertIsInstance(json_str, str)

        # Should be able to parse it back
        parsed = json.loads(json_str)
        self.assertEqual(parsed["metadata"]["category"], "chinese")

    def test_build_ai_payload_empty_historical_events(self):
        """Test building payload with empty historical events"""
        payload = self.agent.build_ai_payload(
            [],
            self.availability,
            months_ahead=3
        )

        self.assertEqual(payload["historical_events"], [])
        self.assertIn("metadata", payload)

    def test_build_ai_payload_empty_availability(self):
        """Test building payload with empty availability"""
        empty_availability = {"status": "placeholder", "members": {}}

        payload = self.agent.build_ai_payload(
            self.historical_events,
            empty_availability,
            months_ahead=3
        )

        self.assertEqual(payload["availability"]["members"], {})

    def test_build_ai_payload_default_strategy(self):
        """Test that default strategy is included"""
        payload = self.agent.build_ai_payload(
            self.historical_events,
            self.availability
        )

        self.assertEqual(payload["generation_params"]["strategy"], "balanced")

    def test_build_ai_payload_generated_at_is_today(self):
        """Test that generated_at is today's date"""
        payload = self.agent.build_ai_payload(
            self.historical_events,
            self.availability
        )

        generated_at = date.fromisoformat(payload["metadata"]["generated_at"])
        self.assertEqual(generated_at, date.today())


class TestAIAgentIntegration(unittest.TestCase):
    """Integration tests for AIAgent workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = AIAgent(self.mock_client)

    def test_full_workflow(self):
        """Test complete workflow: fetch -> evaluate -> build"""
        # Setup mock
        mock_events = [
            {"id": 1, "date": "2024-01-01", "members": [{"name": "張三", "role": "證道"}]},
            {"id": 2, "date": "2024-01-08", "members": [{"name": "李四", "role": "司會"}]}
        ]
        self.mock_client.get_events.return_value = mock_events

        # Step 1: Fetch historical events
        events = self.agent.fetch_last_three_months(category="chinese")
        self.assertEqual(len(events), 2)

        # Step 2: Extract members and evaluate availability
        members = []
        for event in events:
            members.extend(event.get("members", []))

        availability = self.agent.evaluate_availability_placeholder(members)
        self.assertEqual(availability["status"], "placeholder")
        self.assertEqual(len(availability["members"]), 2)

        # Step 3: Build AI payload
        payload = self.agent.build_ai_payload(
            events,
            availability,
            months_ahead=3,
            category="chinese"
        )

        # Verify final payload structure
        self.assertIn("metadata", payload)
        self.assertIn("historical_events", payload)
        self.assertIn("availability", payload)
        self.assertIn("generation_params", payload)

        # Verify it's JSON serializable
        json.dumps(payload)

    def test_workflow_with_no_events(self):
        """Test workflow when no historical events are found"""
        self.mock_client.get_events.return_value = []

        events = self.agent.fetch_last_three_months()
        availability = self.agent.evaluate_availability_placeholder([])
        payload = self.agent.build_ai_payload(events, availability)

        self.assertEqual(payload["historical_events"], [])
        self.assertEqual(payload["availability"]["members"], {})


if __name__ == "__main__":
    unittest.main()
