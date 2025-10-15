"""
Unit tests for RosterOrchestrator
"""

import unittest
from unittest.mock import Mock, patch
from datetime import date, timedelta

from src.services.roster_orchestrator import RosterOrchestrator
from src.services.roster_data_agent import RosterDataAgent
from src.services.ai_analyzer import AIAnalyzer


class TestRosterOrchestratorInit(unittest.TestCase):
    """Test RosterOrchestrator initialization"""

    def test_init(self):
        """Test orchestrator initialization"""
        mock_data_agent = Mock(spec=RosterDataAgent)
        mock_analyzer = Mock(spec=AIAnalyzer)

        orchestrator = RosterOrchestrator(mock_data_agent, mock_analyzer)

        self.assertEqual(orchestrator.data_agent, mock_data_agent)
        self.assertEqual(orchestrator.analyzer, mock_analyzer)


class TestGenerateRosterForUpcomingMonths(unittest.TestCase):
    """Test generate_roster_for_upcoming_months method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_agent = Mock(spec=RosterDataAgent)
        self.mock_analyzer = Mock(spec=AIAnalyzer)
        self.orchestrator = RosterOrchestrator(
            self.mock_data_agent,
            self.mock_analyzer
        )

    def test_generate_roster_full_workflow(self):
        """Test complete workflow execution"""
        # Setup mocks
        mock_data = {
            "historical_events": [{"id": 1}],
            "availability": {"members": {"張三": {"available": True}}},
            "metadata": {"total_events": 1}
        }
        self.mock_data_agent.prepare_analysis_data.return_value = mock_data

        mock_patterns = {
            "total_events": 1,
            "member_frequency": {"張三": 1},
            "role_distribution": {},
            "member_roles": {},
            "workload_balance": {},
            "common_pairings": [],
            "insights": []
        }
        self.mock_analyzer.analyze_historical_patterns.return_value = mock_patterns

        mock_rosters = [
            {"date": "2024-01-15", "assignments": [{"role": "證道", "name": "張三"}]}
        ]
        self.mock_analyzer.generate_roster.return_value = mock_rosters

        mock_validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        self.mock_analyzer.validate_roster.return_value = mock_validation

        # Execute
        result = self.orchestrator.generate_roster_for_upcoming_months(
            months_ahead=1,
            category="chinese"
        )

        # Verify all steps were called
        self.mock_data_agent.prepare_analysis_data.assert_called_once()
        self.mock_analyzer.analyze_historical_patterns.assert_called_once()
        self.mock_analyzer.generate_roster.assert_called_once()
        self.mock_analyzer.validate_roster.assert_called_once()

        # Verify result structure
        self.assertIn("rosters", result)
        self.assertIn("validation", result)
        self.assertIn("patterns", result)
        self.assertIn("metadata", result)

        # Verify metadata
        self.assertEqual(result["metadata"]["months_ahead"], 1)
        self.assertEqual(result["metadata"]["category"], "chinese")
        self.assertEqual(result["metadata"]["workflow_status"], "success")

    def test_generate_roster_with_custom_roles(self):
        """Test roster generation with custom required roles"""
        # Setup mocks
        self.mock_data_agent.prepare_analysis_data.return_value = {
            "historical_events": [],
            "availability": {"members": {}},
            "metadata": {}
        }
        self.mock_analyzer.analyze_historical_patterns.return_value = {
            "total_events": 0,
            "member_frequency": {},
            "role_distribution": {},
            "member_roles": {},
            "workload_balance": {},
            "common_pairings": [],
            "insights": []
        }
        self.mock_analyzer.generate_roster.return_value = []
        self.mock_analyzer.validate_roster.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        custom_roles = ["證道", "司會"]

        # Execute
        result = self.orchestrator.generate_roster_for_upcoming_months(
            required_roles=custom_roles
        )

        # Verify custom roles were used
        call_args = self.mock_analyzer.generate_roster.call_args
        self.assertEqual(call_args[1]["required_roles"], custom_roles)

    def test_generate_roster_validation_failure(self):
        """Test workflow when validation fails"""
        # Setup mocks with validation failure
        self.mock_data_agent.prepare_analysis_data.return_value = {
            "historical_events": [],
            "availability": {"members": {}},
            "metadata": {}
        }
        self.mock_analyzer.analyze_historical_patterns.return_value = {
            "total_events": 0,
            "member_frequency": {},
            "role_distribution": {},
            "member_roles": {},
            "workload_balance": {},
            "common_pairings": [],
            "insights": []
        }
        self.mock_analyzer.generate_roster.return_value = []
        self.mock_analyzer.validate_roster.return_value = {
            "is_valid": False,
            "errors": ["Test error"],
            "warnings": [],
            "statistics": {}
        }

        # Execute
        result = self.orchestrator.generate_roster_for_upcoming_months()

        # Verify workflow status reflects failure
        self.assertEqual(result["metadata"]["workflow_status"], "completed_with_warnings")


class TestGenerateTargetDates(unittest.TestCase):
    """Test _generate_target_dates method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_agent = Mock(spec=RosterDataAgent)
        self.mock_analyzer = Mock(spec=AIAnalyzer)
        self.orchestrator = RosterOrchestrator(
            self.mock_data_agent,
            self.mock_analyzer
        )

    @patch('src.services.roster_orchestrator.date')
    def test_generate_target_dates_sundays(self, mock_date):
        """Test that target dates are Sundays"""
        # Mock today as Monday 2024-01-01
        mock_date.today.return_value = date(2024, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        dates = self.orchestrator._generate_target_dates(1)

        # All dates should be Sundays (weekday() == 6)
        for d in dates:
            self.assertEqual(d.weekday(), 6, f"{d} is not a Sunday")

    @patch('src.services.roster_orchestrator.date')
    def test_generate_target_dates_count(self, mock_date):
        """Test that correct number of dates are generated"""
        mock_date.today.return_value = date(2024, 1, 1)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        dates = self.orchestrator._generate_target_dates(1)

        # Should be ~4 Sundays in 1 month
        self.assertGreaterEqual(len(dates), 3)
        self.assertLessEqual(len(dates), 5)


class TestGetDefaultRoles(unittest.TestCase):
    """Test _get_default_roles method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_agent = Mock(spec=RosterDataAgent)
        self.mock_analyzer = Mock(spec=AIAnalyzer)
        self.orchestrator = RosterOrchestrator(
            self.mock_data_agent,
            self.mock_analyzer
        )

    def test_get_default_roles_chinese(self):
        """Test default roles for Chinese category"""
        roles = self.orchestrator._get_default_roles("chinese")

        self.assertIn("證道", roles)
        self.assertIn("司會", roles)
        self.assertGreater(len(roles), 0)

    def test_get_default_roles_english(self):
        """Test default roles for English category"""
        roles = self.orchestrator._get_default_roles("english")

        self.assertIn("Preacher", roles)
        self.assertIn("Host", roles)
        self.assertGreater(len(roles), 0)

    def test_get_default_roles_sundayschool(self):
        """Test default roles for Sunday School category"""
        roles = self.orchestrator._get_default_roles("sundayschool")

        self.assertIn("Teacher", roles)
        self.assertIn("Helper", roles)

    def test_get_default_roles_none(self):
        """Test default roles when no category specified"""
        roles = self.orchestrator._get_default_roles(None)

        # Should default to Chinese roles
        self.assertIn("證道", roles)


class TestAnalyzePatternsOnly(unittest.TestCase):
    """Test analyze_patterns_only method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_agent = Mock(spec=RosterDataAgent)
        self.mock_analyzer = Mock(spec=AIAnalyzer)
        self.orchestrator = RosterOrchestrator(
            self.mock_data_agent,
            self.mock_analyzer
        )

    def test_analyze_patterns_only(self):
        """Test pattern analysis without roster generation"""
        # Setup mocks
        mock_data = {
            "historical_events": [{"id": 1}],
            "availability": {"members": {}},
            "metadata": {"total_events": 1}
        }
        self.mock_data_agent.prepare_analysis_data.return_value = mock_data

        mock_patterns = {
            "total_events": 1,
            "member_frequency": {},
            "role_distribution": {},
            "member_roles": {},
            "workload_balance": {},
            "common_pairings": [],
            "insights": []
        }
        self.mock_analyzer.analyze_historical_patterns.return_value = mock_patterns

        # Execute
        result = self.orchestrator.analyze_patterns_only(months=6)

        # Verify data gathering was called
        self.mock_data_agent.prepare_analysis_data.assert_called_once_with(
            months=6,
            category=None
        )

        # Verify analysis was called
        self.mock_analyzer.analyze_historical_patterns.assert_called_once()

        # Verify result structure
        self.assertIn("patterns", result)
        self.assertIn("data_summary", result)
        self.assertEqual(result["patterns"]["total_events"], 1)


class TestValidateExistingRoster(unittest.TestCase):
    """Test validate_existing_roster method"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_data_agent = Mock(spec=RosterDataAgent)
        self.mock_analyzer = Mock(spec=AIAnalyzer)
        self.orchestrator = RosterOrchestrator(
            self.mock_data_agent,
            self.mock_analyzer
        )

    def test_validate_existing_roster(self):
        """Test validation of existing roster"""
        roster = {
            "date": "2024-01-15",
            "assignments": [{"role": "證道", "name": "張三"}]
        }

        mock_validation = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }
        self.mock_analyzer.validate_roster.return_value = mock_validation

        # Execute
        result = self.orchestrator.validate_existing_roster(roster)

        # Verify analyzer was called
        self.mock_analyzer.validate_roster.assert_called_once_with(roster)

        # Verify result
        self.assertEqual(result, mock_validation)


if __name__ == "__main__":
    unittest.main()
