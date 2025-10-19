"""
Unit tests for IRosterAnalyzer interface.

These tests define the contract that any implementation of IRosterAnalyzer
must satisfy. They use mocks to isolate the interface from AI provider dependencies.

Test-Driven Development approach:
1. Write tests based on interface contract (THIS FILE - tests will FAIL)
2. Implement concrete class to pass tests (src/services/roster_analyzer.py)
3. Refactor as needed while keeping tests green
"""

import pytest
from datetime import date, timedelta
from typing import Dict, List, Any, Set

from src.interfaces.roster_analyzer import IRosterAnalyzer, IAIProvider


# ==================== Mock AI Provider for Testing ====================

class MockAIProvider(IAIProvider):
    """
    Mock implementation of IAIProvider for testing.

    This is ONLY for testing purposes - not the real implementation.
    """

    def __init__(self):
        self.last_payload: Dict[str, Any] = {}
        self.mock_recommendations: List[Dict[str, Any]] = []

    def set_mock_recommendations(self, recommendations: List[Dict[str, Any]]) -> None:
        """Helper method to set mock AI responses."""
        self.mock_recommendations = recommendations

    def generate_roster_recommendations(
        self,
        payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return mock recommendations and store payload for inspection."""
        self.last_payload = payload
        return self.mock_recommendations.copy()


# ==================== Test Fixtures ====================

@pytest.fixture
def mock_ai_provider():
    """Provides a fresh MockAIProvider for each test."""
    return MockAIProvider()


@pytest.fixture
def roster_analyzer(mock_ai_provider):
    """
    Provides a RosterAnalyzer instance.

    THIS WILL FAIL until you implement RosterAnalyzer in:
    src/services/roster_analyzer.py
    """
    from src.services.roster_analyzer import RosterAnalyzer
    return RosterAnalyzer(ai_provider=mock_ai_provider)


@pytest.fixture
def sample_historical_events():
    """Sample historical event data."""
    return [
        {
            "date": "2024-01-07",  # Sunday
            "category": "chinese",
            "members": [
                {"name": "張三", "role": "證道"},
                {"name": "李四", "role": "司會"}
            ]
        },
        {
            "date": "2024-01-14",  # Sunday
            "category": "chinese",
            "members": [
                {"name": "張三", "role": "司會"},
                {"name": "王五", "role": "證道"}
            ]
        },
        {
            "date": "2024-01-21",  # Sunday
            "category": "chinese",
            "members": [
                {"name": "李四", "role": "證道"},
                {"name": "趙六", "role": "招待"}
            ]
        }
    ]


@pytest.fixture
def sample_availability_data():
    """Sample availability data."""
    return [
        {
            "date": "2024-12-01",
            "available_workers": ["張三", "李四", "王五"],
            "unavailable_workers": ["趙六"]
        },
        {
            "date": "2024-12-08",
            "available_workers": ["張三", "王五", "趙六"],
            "unavailable_workers": ["李四"]
        },
        {
            "date": "2024-12-15",
            "available_workers": ["李四", "王五", "趙六"],
            "unavailable_workers": ["張三"]
        }
    ]


@pytest.fixture
def sample_role_history():
    """Sample role history data."""
    return {
        "證道": {"張三", "李四", "王五"},
        "司會": {"張三", "李四", "趙六"},
        "招待": {"趙六", "王五"}
    }


@pytest.fixture
def sample_required_roles():
    """Sample required roles."""
    return ["證道", "司會"]


# ==================== Test: generate_roster ====================

class TestGenerateRoster:
    """Test suite for generate_roster method."""

    def test_returns_list_of_rosters(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should return a list of roster recommendations."""
        # Setup mock AI response
        mock_ai_provider.set_mock_recommendations([
            {
                "date": "2024-12-01",
                "category": "chinese",
                "assignments": [
                    {"role": "證道", "name": "張三"},
                    {"role": "司會", "name": "李四"}
                ]
            }
        ])

        rosters = roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1),
            category="chinese"
        )

        assert isinstance(rosters, list)
        assert len(rosters) == 1

    def test_only_generates_for_sundays(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should only generate rosters for Sundays."""
        # December 2024: Sundays are 1st, 8th, 15th, 22nd, 29th
        mock_ai_provider.set_mock_recommendations([
            {"date": "2024-12-01", "category": "chinese", "assignments": []},
            {"date": "2024-12-08", "category": "chinese", "assignments": []},
            {"date": "2024-12-15", "category": "chinese", "assignments": []},
            {"date": "2024-12-22", "category": "chinese", "assignments": []},
            {"date": "2024-12-29", "category": "chinese", "assignments": []}
        ])

        rosters = roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 31)
        )

        # Should have 5 Sundays
        assert len(rosters) == 5

        # Verify all dates are Sundays
        for roster in rosters:
            roster_date = date.fromisoformat(roster["date"])
            assert roster_date.weekday() == 6, f"{roster['date']} is not a Sunday"

    def test_uses_default_date_range_when_not_specified(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should default to today + 3 months when dates not specified."""
        # Mock AI to return rosters for all Sundays
        mock_ai_provider.set_mock_recommendations([])

        rosters = roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles
        )

        # Should have approximately 12-14 Sundays in 3 months
        assert 10 <= len(rosters) <= 15

    def test_calls_ai_provider_with_structured_payload(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should send structured JSON payload to AI provider."""
        mock_ai_provider.set_mock_recommendations([
            {"date": "2024-12-01", "category": "chinese", "assignments": []}
        ])

        roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1),
            category="chinese"
        )

        # Verify AI provider was called with correct payload structure
        payload = mock_ai_provider.last_payload
        assert "historical_patterns" in payload
        assert "availability" in payload
        assert "role_eligibility" in payload
        assert "target_dates" in payload
        assert "required_roles" in payload

    def test_analyzes_historical_patterns_in_payload(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should include analyzed patterns in AI payload."""
        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1)
        )

        patterns = mock_ai_provider.last_payload["historical_patterns"]
        assert "total_events" in patterns
        assert "member_frequency" in patterns
        assert "workload_balance" in patterns

        # Verify analysis correctness
        assert patterns["total_events"] == 3
        assert "張三" in patterns["member_frequency"]
        assert patterns["member_frequency"]["張三"] == 2  # Appeared in 2 events

    def test_includes_availability_in_payload(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should include availability data in AI payload."""
        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 8)
        )

        availability = mock_ai_provider.last_payload["availability"]
        assert isinstance(availability, list)
        # Should only include Sundays (Dec 1 and 8)
        assert len(availability) == 2

    def test_includes_role_eligibility_in_payload(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should include role history (eligibility) in AI payload."""
        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1)
        )

        eligibility = mock_ai_provider.last_payload["role_eligibility"]
        assert eligibility == sample_role_history

    def test_includes_target_dates_sundays_only(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should only include Sundays in target_dates."""
        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),  # Sunday
            end_date=date(2024, 12, 15)    # Sunday
        )

        target_dates = mock_ai_provider.last_payload["target_dates"]
        assert len(target_dates) == 3  # Dec 1, 8, 15 (all Sundays)

        # Verify all are Sundays
        for date_str in target_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() == 6

    def test_raises_error_for_invalid_date_range(
        self,
        roster_analyzer,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should raise ValueError if start_date > end_date."""
        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            roster_analyzer.generate_roster(
                historical_events=sample_historical_events,
                availability_data=sample_availability_data,
                role_history=sample_role_history,
                required_roles=sample_required_roles,
                start_date=date(2024, 12, 31),
                end_date=date(2024, 12, 1)
            )

    def test_handles_empty_historical_events(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should handle case with no historical events."""
        mock_ai_provider.set_mock_recommendations([
            {"date": "2024-12-01", "category": "chinese", "assignments": []}
        ])

        rosters = roster_analyzer.generate_roster(
            historical_events=[],
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1)
        )

        assert len(rosters) == 1

        # Patterns should reflect empty history
        patterns = mock_ai_provider.last_payload["historical_patterns"]
        assert patterns["total_events"] == 0


# ==================== Test: Historical Pattern Analysis ====================

class TestHistoricalPatternAnalysis:
    """Test suite for historical pattern analysis logic."""

    def test_calculates_member_frequency_correctly(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should correctly count member participation frequency."""
        events = [
            {"date": "2024-01-07", "members": [{"name": "張三", "role": "證道"}]},
            {"date": "2024-01-14", "members": [{"name": "張三", "role": "司會"}]},
            {"date": "2024-01-21", "members": [{"name": "李四", "role": "證道"}]}
        ]

        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1)
        )

        frequency = mock_ai_provider.last_payload["historical_patterns"]["member_frequency"]
        assert frequency["張三"] == 2
        assert frequency["李四"] == 1

    def test_calculates_workload_balance(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should calculate workload balance ratios."""
        events = [
            {"date": "2024-01-07", "members": [{"name": "張三", "role": "證道"}]},
            {"date": "2024-01-14", "members": [{"name": "張三", "role": "司會"}]},
            {"date": "2024-01-21", "members": [{"name": "李四", "role": "證道"}]},
            {"date": "2024-01-28", "members": [{"name": "王五", "role": "招待"}]}
        ]

        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1)
        )

        balance = mock_ai_provider.last_payload["historical_patterns"]["workload_balance"]
        assert balance["張三"] == 0.5  # 2 out of 4 events
        assert balance["李四"] == 0.25  # 1 out of 4 events
        assert balance["王五"] == 0.25


# ==================== Test: Edge Cases ====================

class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_handles_no_sundays_in_range(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should return empty list if no Sundays in date range."""
        mock_ai_provider.set_mock_recommendations([])

        # Dec 2, 2024 (Monday) to Dec 6, 2024 (Friday) - no Sundays
        rosters = roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 2),
            end_date=date(2024, 12, 6)
        )

        assert len(rosters) == 0

    def test_handles_single_sunday(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should handle single Sunday in range."""
        mock_ai_provider.set_mock_recommendations([
            {"date": "2024-12-01", "category": "chinese", "assignments": []}
        ])

        rosters = roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1)
        )

        assert len(rosters) == 1

    def test_filters_availability_to_sundays_only(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_role_history,
        sample_required_roles
    ):
        """Should only include Sunday availability in payload."""
        # Availability for entire week
        availability = [
            {"date": "2024-12-01", "available_workers": ["張三"], "unavailable_workers": []},  # Sunday
            {"date": "2024-12-02", "available_workers": ["李四"], "unavailable_workers": []},  # Monday
            {"date": "2024-12-03", "available_workers": ["王五"], "unavailable_workers": []},  # Tuesday
            {"date": "2024-12-08", "available_workers": ["趙六"], "unavailable_workers": []}   # Sunday
        ]

        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=availability,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 8)
        )

        # Should only include Dec 1 and Dec 8 (Sundays)
        payload_availability = mock_ai_provider.last_payload["availability"]
        assert len(payload_availability) == 2
        assert payload_availability[0]["date"] == "2024-12-01"
        assert payload_availability[1]["date"] == "2024-12-08"


# ==================== Test: AI Provider Integration ====================

class TestAIProviderIntegration:
    """Test suite for AI provider interactions."""

    def test_returns_ai_provider_recommendations(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should return recommendations from AI provider."""
        expected_rosters = [
            {
                "date": "2024-12-01",
                "category": "chinese",
                "assignments": [
                    {"role": "證道", "name": "張三"},
                    {"role": "司會", "name": "李四"}
                ]
            }
        ]
        mock_ai_provider.set_mock_recommendations(expected_rosters)

        rosters = roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1),
            category="chinese"
        )

        assert rosters == expected_rosters

    def test_includes_category_in_payload_when_provided(
        self,
        roster_analyzer,
        mock_ai_provider,
        sample_historical_events,
        sample_availability_data,
        sample_role_history,
        sample_required_roles
    ):
        """Should include category in payload if provided."""
        mock_ai_provider.set_mock_recommendations([])

        roster_analyzer.generate_roster(
            historical_events=sample_historical_events,
            availability_data=sample_availability_data,
            role_history=sample_role_history,
            required_roles=sample_required_roles,
            start_date=date(2024, 12, 1),
            end_date=date(2024, 12, 1),
            category="english"
        )

        assert mock_ai_provider.last_payload.get("category") == "english"
