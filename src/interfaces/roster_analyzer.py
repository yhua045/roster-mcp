"""
Interface definitions for Roster Analysis and Generation.

This module defines the contracts for analyzing roster data and generating
roster recommendations using AI. The analyzer receives prepared data and
focuses on analysis and AI payload generation, not data fetching.

The design separates data orchestration (RosterOrchestrator) from analysis
logic (RosterAnalyzer) following Single Responsibility Principle.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Optional, Any, Set
from datetime import date


# ==================== Output Data Structures ====================

class RosterRecommendation(Protocol):
    """
    Output data structure for a single roster recommendation.

    Represents the recommended assignments for one service date.
    """

    date: str
    """Date in ISO format (YYYY-MM-DD) - always a Sunday"""

    category: Optional[str]
    """Service category (e.g., 'chinese', 'english')"""

    assignments: List[Dict[str, str]]
    """
    List of role assignments for this date.

    Example:
        [
            {"role": "證道", "name": "張三"},
            {"role": "司會", "name": "李四"}
        ]
    """


# ==================== AI Provider Interface ====================

class IAIProvider(ABC):
    """
    Interface for AI service providers.

    Uses Adapter Pattern to support different AI services:
    - OpenAI (GPT-4, etc.)
    - Anthropic (Claude)
    - Custom models

    This is an INTERNAL dependency of IRosterAnalyzer - not exposed to orchestrator.
    The orchestrator doesn't need to know which AI provider is being used.
    """

    @abstractmethod
    def generate_roster_recommendations(
        self,
        payload: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Send roster generation request to AI service.

        Takes a structured JSON payload containing all context needed for
        roster generation and returns AI-generated recommendations.

        Args:
            payload: Structured JSON payload containing:
                - historical_patterns: Pattern analysis results
                  {
                      "total_events": int,
                      "member_frequency": {"name": count},
                      "workload_balance": {"name": ratio}
                  }
                - availability: Worker availability by date
                  [{"date": "YYYY-MM-DD", "available": [...], "unavailable": [...]}]
                - role_eligibility: Which workers can do which roles
                  {"role_name": ["worker1", "worker2"]}
                - target_dates: List of dates to generate rosters for
                  ["YYYY-MM-DD", ...]
                - required_roles: Roles that must be filled
                  ["role1", "role2"]
                - constraints: Optional generation constraints
                  {"max_consecutive": 2, "balance_workload": true}

        Returns:
            List of roster recommendations:
            [
                {
                    "date": "2024-12-01",
                    "category": "chinese",
                    "assignments": [
                        {"role": "證道", "name": "張三"},
                        {"role": "司會", "name": "李四"}
                    ]
                }
            ]

        Raises:
            AIProviderError: If AI service fails or returns invalid data
            ValueError: If payload is malformed

        Example:
            >>> provider = OpenAIProvider(api_key="...")
            >>> payload = {
            ...     "historical_patterns": {...},
            ...     "availability": [...],
            ...     "target_dates": ["2024-12-01"],
            ...     "required_roles": ["證道", "司會"]
            ... }
            >>> recommendations = provider.generate_roster_recommendations(payload)
            >>> len(recommendations)
            1
        """
        pass


# ==================== Main Interface ====================

class IRosterAnalyzer(ABC):
    """
    Interface for roster analysis and generation.

    Responsibilities:
    1. Receive prepared data from orchestrator (events, availability, role history)
    2. Analyze historical patterns (participation, workload, pairings)
    3. Prepare structured AI payload (JSON format)
    4. Send to AI provider for recommendations
    5. Return roster recommendations for Sundays only

    This analyzer does NOT:
    - Fetch data from external sources (orchestrator provides data)
    - Know about data source details (IRoleHistoryManager, IAvailabilityEvaluator)
    - Persist rosters (orchestrator handles persistence)
    - Generate rosters for non-Sunday dates

    Design Principles:
    - Single Responsibility: Analyze data and generate recommendations
    - Dependency Inversion: Depends on IAIProvider abstraction
    - Data flow: Orchestrator → Analyzer → AI Provider → Recommendations

    Usage:
        # Orchestrator prepares data
        events = fetch_historical_events()
        availability = availability_evaluator.evaluate_availability()
        role_history = role_history_manager.get_all_role_history()

        # Analyzer generates roster
        analyzer = RosterAnalyzer(ai_provider=openai_provider)
        rosters = analyzer.generate_roster(
            historical_events=events,
            availability_data=availability,
            role_history=role_history,
            required_roles=["證道", "司會", "招待"]
        )
    """

    @abstractmethod
    def generate_roster(
        self,
        historical_events: List[Dict[str, Any]],
        availability_data: List[Dict[str, Any]],
        role_history: Dict[str, Set[str]],
        required_roles: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate roster recommendations for Sundays in a date range.

        This method:
        1. Validates and filters input data
        2. Analyzes historical patterns (participation, workload, pairings)
        3. Identifies Sundays within the date range
        4. Prepares structured AI payload (JSON format)
        5. Sends payload to AI provider
        6. Returns AI-generated roster recommendations

        Args:
            historical_events: List of historical event dictionaries from orchestrator.
                Format:
                [
                    {
                        "date": "2024-01-15",
                        "category": "chinese",
                        "members": [
                            {"name": "張三", "role": "證道"},
                            {"name": "李四", "role": "司會"}
                        ]
                    }
                ]

            availability_data: Worker availability by date from IAvailabilityEvaluator.
                Format:
                [
                    {
                        "date": "2024-12-25",
                        "available_workers": ["王五", "趙六"],
                        "unavailable_workers": ["張三", "李四"]
                    }
                ]

            role_history: Role eligibility mapping from IRoleHistoryManager.
                Format:
                {
                    "證道": {"張三", "李四", "王五"},
                    "司會": {"李四", "趙六"}
                }

            required_roles: List of roles that must be filled for each service.
                Example: ["證道", "司會", "招待", "詩歌讚美"]
                Note: This typically comes from configuration based on category.

            start_date: Start of date range. If None, defaults to today.

            end_date: End of date range. If None, defaults to today + 3 months.

            category: Service category (e.g., "chinese", "english").
                     Used for context in AI payload.

        Returns:
            List of roster recommendations for Sundays only:
            [
                {
                    "date": "2024-12-01",  # Sunday
                    "category": "chinese",
                    "assignments": [
                        {"role": "證道", "name": "張三"},
                        {"role": "司會", "name": "李四"}
                    ]
                },
                {
                    "date": "2024-12-08",  # Sunday
                    "category": "chinese",
                    "assignments": [
                        {"role": "證道", "name": "王五"},
                        {"role": "司會", "name": "趙六"}
                    ]
                }
            ]

        Raises:
            ValueError: If required data is missing or malformed
            AIProviderError: If AI service fails

        Example:
            >>> # Orchestrator prepares data
            >>> events = [
            ...     {
            ...         "date": "2024-01-07",
            ...         "members": [{"name": "張三", "role": "證道"}]
            ...     }
            ... ]
            >>> availability = [
            ...     {
            ...         "date": "2024-12-01",
            ...         "available_workers": ["張三", "李四"],
            ...         "unavailable_workers": []
            ...     }
            ... ]
            >>> role_history = {"證道": {"張三", "李四"}}
            >>> required_roles = ["證道", "司會"]
            >>>
            >>> # Generate roster
            >>> analyzer = RosterAnalyzer(ai_provider=openai_provider)
            >>> rosters = analyzer.generate_roster(
            ...     historical_events=events,
            ...     availability_data=availability,
            ...     role_history=role_history,
            ...     required_roles=required_roles,
            ...     start_date=date(2024, 12, 1),
            ...     end_date=date(2024, 12, 31)
            ... )
            >>> len(rosters)  # 5 Sundays in December 2024
            5
            >>> rosters[0]["date"]
            "2024-12-01"

        Implementation Notes:
            - Default period: today to today + 3 months
            - Only generates rosters for Sundays (date.weekday() == 6)
            - Analyzes patterns internally: participation frequency, workload balance
            - Prepares AI payload as JSON object with all context
            - AI provider is injected dependency (constructor)
            - Validates all required roles are filled in recommendations
        """
        pass
