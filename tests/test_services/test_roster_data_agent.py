"""
Unit tests for RosterDataAgent
"""

import unittest
from unittest.mock import Mock
from datetime import date, timedelta
import json

from src.services.roster_data_agent import RosterDataAgent
from src.services.roster_api_client import RosterAPIClient
from src.exceptions import InvalidCategoryError, APIError


class TestRosterDataAgentInit(unittest.TestCase):
    """Test RosterDataAgent initialization"""

    def test_init(self):
        """Test RosterDataAgent initialization with API client"""
        mock_client = Mock(spec=RosterAPIClient)
        agent = RosterDataAgent(mock_client)
        self.assertEqual(agent.api_client, mock_client)


class TestFetchHistoricalEvents(unittest.TestCase):
    """Test fetch_historical_events method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = RosterDataAgent(self.mock_client)

    def test_fetch_historical_events_default_months(self):
        """Test fetching events with default 3 months"""
        mock_events = [
            {"id": 1, "date": "2024-01-01"},
            {"id": 2, "date": "2024-01-08"}
        ]
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.fetch_historical_events()

        # Verify correct date range (today - 90 days to today)
        today = date.today()
        from_date = today - timedelta(days=90)

        self.mock_client.get_events.assert_called_once_with(
            category=None,
            from_date=from_date,
            to_date=today
        )
        self.assertEqual(result, mock_events)

    def test_fetch_historical_events_custom_months(self):
        """Test fetching events with custom months parameter"""
        mock_events = [{"id": 1}]
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.fetch_historical_events(months=6)

        # Verify 6 months back
        today = date.today()
        from_date = today - timedelta(days=180)

        self.mock_client.get_events.assert_called_once_with(
            category=None,
            from_date=from_date,
            to_date=today
        )

    def test_fetch_historical_events_with_category(self):
        """Test fetching events with category filter"""
        mock_events = [
            {"id": 1, "date": "2024-01-01", "category": "chinese"},
            {"id": 2, "date": "2024-01-08", "category": "chinese"}
        ]
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.fetch_historical_events(months=3, category="chinese")

        # Verify category was passed
        today = date.today()
        from_date = today - timedelta(days=90)

        self.mock_client.get_events.assert_called_once_with(
            category="chinese",
            from_date=from_date,
            to_date=today
        )
        self.assertEqual(result, mock_events)

    def test_fetch_historical_events_invalid_months(self):
        """Test that invalid months raises error"""
        with self.assertRaises(ValueError) as context:
            self.agent.fetch_historical_events(months=0)
        self.assertIn("must be positive", str(context.exception))

        with self.assertRaises(ValueError):
            self.agent.fetch_historical_events(months=-1)

    def test_fetch_historical_events_empty_result(self):
        """Test fetching events with empty result"""
        self.mock_client.get_events.return_value = []

        result = self.agent.fetch_historical_events()

        self.assertEqual(result, [])

    def test_fetch_historical_events_invalid_category(self):
        """Test that invalid category raises error"""
        self.mock_client.get_events.side_effect = InvalidCategoryError(
            "invalid",
            {'chinese', 'english', 'sundayschool'}
        )

        with self.assertRaises(InvalidCategoryError):
            self.agent.fetch_historical_events(category="invalid")

    def test_fetch_historical_events_api_error(self):
        """Test that API errors are propagated"""
        self.mock_client.get_events.side_effect = APIError("Network error")

        with self.assertRaises(APIError):
            self.agent.fetch_historical_events()


class TestEvaluateMemberAvailability(unittest.TestCase):
    """Test evaluate_member_availability method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = RosterDataAgent(self.mock_client)

    def test_evaluate_member_availability_basic(self):
        """Test availability evaluation with basic member list"""
        members = [
            {"name": "張三", "role": "證道"},
            {"name": "李四", "role": "司會"}
        ]

        result = self.agent.evaluate_member_availability(members)

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

    def test_evaluate_member_availability_deterministic(self):
        """Test that evaluation returns deterministic results"""
        members = [{"name": "張三", "role": "證道"}]

        result1 = self.agent.evaluate_member_availability(members)
        result2 = self.agent.evaluate_member_availability(members)

        # Both should mark members as available
        self.assertEqual(
            result1["members"]["張三"]["available"],
            result2["members"]["張三"]["available"]
        )

    def test_evaluate_member_availability_empty_members(self):
        """Test evaluation with empty member list"""
        members = []

        result = self.agent.evaluate_member_availability(members)

        self.assertEqual(result["status"], "placeholder")
        self.assertEqual(result["members"], {})

    def test_evaluate_member_availability_duplicate_names(self):
        """Test evaluation with duplicate member names"""
        members = [
            {"name": "張三", "role": "證道"},
            {"name": "張三", "role": "司會"},
            {"name": "李四", "role": "招待"}
        ]

        result = self.agent.evaluate_member_availability(members)

        # Should only have 2 unique members
        self.assertEqual(len(result["members"]), 2)
        self.assertIn("張三", result["members"])
        self.assertIn("李四", result["members"])

    def test_evaluate_member_availability_missing_names(self):
        """Test evaluation with members missing name field"""
        members = [
            {"role": "證道"},  # No name
            {"name": "李四", "role": "司會"}
        ]

        result = self.agent.evaluate_member_availability(members)

        # Should only include member with name
        self.assertEqual(len(result["members"]), 1)
        self.assertIn("李四", result["members"])

    def test_evaluate_member_availability_structure(self):
        """Test that evaluation output has correct structure"""
        members = [{"name": "張三", "role": "證道"}]

        result = self.agent.evaluate_member_availability(members)

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


class TestPrepareAnalysisData(unittest.TestCase):
    """Test prepare_analysis_data method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = RosterDataAgent(self.mock_client)

    def test_prepare_analysis_data_basic(self):
        """Test preparing analysis data with basic parameters"""
        mock_events = [
            {"id": 1, "date": "2024-01-01", "members": [{"name": "張三", "role": "證道"}]},
            {"id": 2, "date": "2024-01-08", "members": [{"name": "李四", "role": "司會"}]}
        ]
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.prepare_analysis_data()

        # Check structure
        self.assertIn("historical_events", result)
        self.assertIn("availability", result)
        self.assertIn("metadata", result)

        # Check historical events
        self.assertEqual(result["historical_events"], mock_events)

        # Check availability
        self.assertEqual(len(result["availability"]["members"]), 2)
        self.assertIn("張三", result["availability"]["members"])
        self.assertIn("李四", result["availability"]["members"])

        # Check metadata
        metadata = result["metadata"]
        self.assertEqual(metadata["total_events"], 2)
        self.assertEqual(metadata["unique_members"], 2)
        self.assertEqual(metadata["months_analyzed"], 3)

    def test_prepare_analysis_data_with_category(self):
        """Test preparing data with category filter"""
        mock_events = [{"id": 1, "members": []}]
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.prepare_analysis_data(category="chinese")

        self.assertEqual(result["metadata"]["category"], "chinese")

    def test_prepare_analysis_data_custom_months(self):
        """Test preparing data with custom months"""
        mock_events = []
        self.mock_client.get_events.return_value = mock_events

        result = self.agent.prepare_analysis_data(months=6)

        self.assertEqual(result["metadata"]["months_analyzed"], 6)

    def test_prepare_analysis_data_no_events(self):
        """Test preparing data when no events are found"""
        self.mock_client.get_events.return_value = []

        result = self.agent.prepare_analysis_data()

        self.assertEqual(result["historical_events"], [])
        self.assertEqual(result["availability"]["members"], {})
        self.assertEqual(result["metadata"]["total_events"], 0)
        self.assertEqual(result["metadata"]["unique_members"], 0)


class TestExtractMembersFromEvents(unittest.TestCase):
    """Test extract_members_from_events method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = RosterDataAgent(self.mock_client)

    def test_extract_members_basic(self):
        """Test extracting members from events"""
        events = [
            {"id": 1, "members": [{"name": "張三"}, {"name": "李四"}]},
            {"id": 2, "members": [{"name": "王五"}]}
        ]

        result = self.agent.extract_members_from_events(events)

        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "張三")
        self.assertEqual(result[1]["name"], "李四")
        self.assertEqual(result[2]["name"], "王五")

    def test_extract_members_empty_events(self):
        """Test extracting from empty event list"""
        events = []
        result = self.agent.extract_members_from_events(events)
        self.assertEqual(result, [])

    def test_extract_members_no_member_field(self):
        """Test extracting when events have no members field"""
        events = [{"id": 1}, {"id": 2}]
        result = self.agent.extract_members_from_events(events)
        self.assertEqual(result, [])

    def test_extract_members_empty_member_lists(self):
        """Test extracting when events have empty member lists"""
        events = [{"id": 1, "members": []}, {"id": 2, "members": []}]
        result = self.agent.extract_members_from_events(events)
        self.assertEqual(result, [])


class TestRosterDataAgentIntegration(unittest.TestCase):
    """Integration tests for RosterDataAgent workflow"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock(spec=RosterAPIClient)
        self.agent = RosterDataAgent(self.mock_client)

    def test_full_workflow(self):
        """Test complete workflow: fetch → extract → evaluate → prepare"""
        # Setup mock
        mock_events = [
            {"id": 1, "date": "2024-01-01", "members": [{"name": "張三", "role": "證道"}]},
            {"id": 2, "date": "2024-01-08", "members": [{"name": "李四", "role": "司會"}]}
        ]
        self.mock_client.get_events.return_value = mock_events

        # Execute workflow
        data = self.agent.prepare_analysis_data(category="chinese")

        # Verify structure
        self.assertIn("historical_events", data)
        self.assertIn("availability", data)
        self.assertIn("metadata", data)

        # Verify data is complete
        self.assertEqual(len(data["historical_events"]), 2)
        self.assertEqual(len(data["availability"]["members"]), 2)
        self.assertEqual(data["metadata"]["category"], "chinese")

        # Verify it's a complete data package ready for analysis
        self.assertIsInstance(data, dict)
        json.dumps(data)  # Should be JSON serializable

    def test_workflow_with_no_events(self):
        """Test workflow when no historical events are found"""
        self.mock_client.get_events.return_value = []

        data = self.agent.prepare_analysis_data()

        self.assertEqual(data["historical_events"], [])
        self.assertEqual(data["availability"]["members"], {})
        self.assertEqual(data["metadata"]["total_events"], 0)


if __name__ == "__main__":
    unittest.main()
