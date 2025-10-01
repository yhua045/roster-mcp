"""
Tests for the AI Agent service
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, MagicMock, patch

from src.services.ai_agent import AIAgent, RosterGenerationRules
from src.services.roster_api_client import RosterAPIClient
from src.services.ai_analyzer import AIAnalyzer


class TestRosterGenerationRules:
    """Tests for RosterGenerationRules configuration"""

    def test_default_rules(self):
        """Test that default rules are created correctly"""
        rules = RosterGenerationRules()

        assert rules.max_assignments_per_person_per_month == 4
        assert rules.min_rest_days_between_assignments == 7
        assert rules.prefer_role_rotation is True
        assert rules.require_minimum_team_size == 3

    def test_custom_rules(self):
        """Test creating rules with custom values"""
        rules = RosterGenerationRules(
            max_assignments_per_person_per_month=5,
            min_rest_days_between_assignments=10,
            prefer_role_rotation=False,
        )

        assert rules.max_assignments_per_person_per_month == 5
        assert rules.min_rest_days_between_assignments == 10
        assert rules.prefer_role_rotation is False

    def test_validate_rules_success(self):
        """Test validation passes for valid rules"""
        rules = RosterGenerationRules()
        rules.validate()  # Should not raise

    def test_validate_rules_invalid_max_assignments(self):
        """Test validation fails for invalid max assignments"""
        rules = RosterGenerationRules(max_assignments_per_person_per_month=0)

        with pytest.raises(
            ValueError, match="max_assignments_per_person_per_month must be at least 1"
        ):
            rules.validate()

    def test_validate_rules_negative_rest_days(self):
        """Test validation fails for negative rest days"""
        rules = RosterGenerationRules(min_rest_days_between_assignments=-1)

        with pytest.raises(
            ValueError, match="min_rest_days_between_assignments cannot be negative"
        ):
            rules.validate()

    def test_validate_rules_invalid_weights(self):
        """Test validation fails when weights don't sum to 1.0"""
        rules = RosterGenerationRules(
            workload_balance_weight=0.5,
            role_coverage_weight=0.5,
            team_chemistry_weight=0.5,
            availability_weight=0.5,
        )

        with pytest.raises(ValueError, match="Priority weights must sum to 1.0"):
            rules.validate()


class TestAIAgent:
    """Tests for the AI Agent"""

    @pytest.fixture
    def mock_api_client(self):
        """Create a mock API client"""
        client = Mock(spec=RosterAPIClient)
        return client

    @pytest.fixture
    def mock_ai_analyzer(self):
        """Create a mock AI analyzer"""
        analyzer = Mock(spec=AIAnalyzer)
        return analyzer

    @pytest.fixture
    def ai_agent(self, mock_api_client, mock_ai_analyzer):
        """Create an AI Agent instance for testing"""
        return AIAgent(
            api_client=mock_api_client,
            ai_analyzer=mock_ai_analyzer,
            rules=RosterGenerationRules(),
        )

    def test_init(self, mock_api_client, mock_ai_analyzer):
        """Test AI Agent initialization"""
        agent = AIAgent(api_client=mock_api_client, ai_analyzer=mock_ai_analyzer)

        assert agent.api_client == mock_api_client
        assert agent.ai_analyzer == mock_ai_analyzer
        assert isinstance(agent.rules, RosterGenerationRules)

    def test_init_with_custom_rules(self, mock_api_client, mock_ai_analyzer):
        """Test AI Agent initialization with custom rules"""
        custom_rules = RosterGenerationRules(max_assignments_per_person_per_month=5)

        agent = AIAgent(
            api_client=mock_api_client, ai_analyzer=mock_ai_analyzer, rules=custom_rules
        )

        assert agent.rules.max_assignments_per_person_per_month == 5

    def test_init_validates_rules(self, mock_api_client, mock_ai_analyzer):
        """Test that invalid rules are caught during initialization"""
        invalid_rules = RosterGenerationRules(max_assignments_per_person_per_month=0)

        with pytest.raises(ValueError):
            AIAgent(
                api_client=mock_api_client,
                ai_analyzer=mock_ai_analyzer,
                rules=invalid_rules,
            )

    def test_fetch_historical_data(self, ai_agent, mock_api_client):
        """Test fetching historical roster data"""
        # Mock the API response
        mock_events = [{"id": 1, "date": "2024-01-01"}, {"id": 2, "date": "2024-01-08"}]
        mock_api_client.get_events.return_value = mock_events

        # Fetch historical data
        result = ai_agent.fetch_historical_data(months_back=3)

        # Verify API was called with correct date range
        assert mock_api_client.get_events.called
        call_args = mock_api_client.get_events.call_args

        assert call_args[1]["category"] is None
        assert isinstance(call_args[1]["from_date"], date)
        assert isinstance(call_args[1]["to_date"], date)

        # Verify date range is approximately 3 months
        date_diff = call_args[1]["to_date"] - call_args[1]["from_date"]
        assert 80 <= date_diff.days <= 100  # ~3 months

        # Verify result
        assert result == mock_events

    def test_fetch_historical_data_with_category(self, ai_agent, mock_api_client):
        """Test fetching historical data with category filter"""
        mock_events = [{"id": 1, "date": "2024-01-01"}]
        mock_api_client.get_events.return_value = mock_events

        result = ai_agent.fetch_historical_data(months_back=2, category="chinese")

        # Verify category was passed
        call_args = mock_api_client.get_events.call_args
        assert call_args[1]["category"] == "chinese"

    def test_fetch_historical_data_api_error(self, ai_agent, mock_api_client):
        """Test handling of API errors when fetching historical data"""
        mock_api_client.get_events.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            ai_agent.fetch_historical_data()

    def test_validate_generated_roster(self, ai_agent, mock_ai_analyzer):
        """Test roster validation"""
        roster = {
            "date": "2024-03-01",
            "recommendations": [
                {"name": "John", "role": "Host"},
                {"name": "Jane", "role": "Worship"},
            ],
        }

        mock_ai_analyzer.validate_roster.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
        }

        result = ai_agent.validate_generated_roster(roster)

        assert result["is_valid"] is True
        assert mock_ai_analyzer.validate_roster.called

    def test_validate_generated_roster_minimum_team_size(
        self, ai_agent, mock_ai_analyzer
    ):
        """Test validation adds warning for undersized teams"""
        roster = {
            "date": "2024-03-01",
            "recommendations": [{"name": "John", "role": "Host"}],
        }

        mock_ai_analyzer.validate_roster.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
        }

        result = ai_agent.validate_generated_roster(roster)

        # Should add warning about team size
        assert len(result["warnings"]) > 0
        assert "minimum team size" in result["warnings"][0]

    def test_generate_future_rosters(self, ai_agent, mock_api_client, mock_ai_analyzer):
        """Test generating future rosters"""
        # Mock historical data
        mock_api_client.get_events.return_value = [{"id": 1, "date": "2024-01-01"}]

        # Mock analysis
        mock_ai_analyzer.analyze_historical_patterns.return_value = {
            "total_events": 1,
            "member_frequency": {},
        }

        # Mock recommendations
        mock_ai_analyzer.generate_roster_recommendations.return_value = [
            {"name": "John", "role": "Host"}
        ]

        # Generate rosters
        result = ai_agent.generate_future_rosters(months_ahead=1)

        # Verify process
        assert mock_api_client.get_events.called
        assert mock_ai_analyzer.analyze_historical_patterns.called
        assert isinstance(result, list)

    def test_execute_roster_generation_success(
        self, ai_agent, mock_api_client, mock_ai_analyzer
    ):
        """Test successful execution of roster generation workflow"""
        # Mock all dependencies
        mock_api_client.get_events.return_value = []
        mock_ai_analyzer.analyze_historical_patterns.return_value = {}
        mock_ai_analyzer.generate_roster_recommendations.return_value = []
        mock_ai_analyzer.validate_roster.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
        }

        result = ai_agent.execute_roster_generation(months_ahead=1, dry_run=True)

        assert result["status"] == "success"
        assert "generated_count" in result
        assert "validated_count" in result
        assert "submitted_count" in result

    def test_execute_roster_generation_dry_run(
        self, ai_agent, mock_api_client, mock_ai_analyzer
    ):
        """Test that dry run mode doesn't submit rosters"""
        # Mock dependencies
        mock_api_client.get_events.return_value = []
        mock_ai_analyzer.analyze_historical_patterns.return_value = {}
        mock_ai_analyzer.generate_roster_recommendations.return_value = []
        mock_ai_analyzer.validate_roster.return_value = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
        }

        result = ai_agent.execute_roster_generation(months_ahead=1, dry_run=True)

        # Verify no submission in dry run mode
        assert result["submitted_count"] == 0

    def test_execute_roster_generation_error_handling(self, ai_agent, mock_api_client):
        """Test error handling in roster generation workflow"""
        # Simulate an error
        mock_api_client.get_events.side_effect = Exception("Test error")

        result = ai_agent.execute_roster_generation(months_ahead=1)

        assert result["status"] == "failed"
        assert len(result["errors"]) > 0
        assert "Test error" in result["errors"][0]
