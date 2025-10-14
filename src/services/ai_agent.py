"""
AI Agent for data gathering and preparation for roster generation.

This module collects historical roster data and member availability
to prepare payloads for AI-powered roster generation.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import logging
import uuid

from .roster_api_client import RosterAPIClient

logger = logging.getLogger(__name__)


class AIAgent:
    """
    AI Agent responsible for gathering and preparing data for roster generation.

    This agent:
    - Fetches historical roster/event data from the last 3 months
    - Evaluates member availability (placeholder for now)
    - Builds AI-ready payloads for roster generation
    """

    def __init__(self, api_client: RosterAPIClient):
        """
        Initialize the AI Agent with an API client.

        Args:
            api_client: RosterAPIClient instance for fetching roster data
        """
        self.api_client = api_client

    def fetch_last_three_months(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch events from the last three months (90 days).

        This method retrieves historical roster events from today minus 90 days
        up to today, optionally filtered by category.

        Args:
            category: Optional service category filter ('chinese', 'english', 'sundayschool')

        Returns:
            List of event dictionaries from the API

        Raises:
            InvalidCategoryError: If category is invalid
            APIError: If API request fails

        Example:
            >>> agent = AIAgent(api_client)
            >>> events = agent.fetch_last_three_months(category='chinese')
            >>> len(events)
            12
        """
        today = date.today()
        from_date = today - timedelta(days=90)
        to_date = today

        logger.info(
            f"Fetching events from last 3 months: {from_date} to {to_date}"
            f"{f' (category: {category})' if category else ''}"
        )

        events = self.api_client.get_events(
            category=category,
            from_date=from_date,
            to_date=to_date
        )

        logger.info(f"Retrieved {len(events)} events from the last 3 months")
        return events

    def evaluate_availability_placeholder(self, members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Placeholder for evaluating member availability.

        This method returns deterministic default availability for all members.
        In the future, this should be replaced with actual availability logic
        that considers:
        - Member preferences
        - Historical patterns
        - Conflict detection
        - Capacity constraints

        Args:
            members: List of member dictionaries to evaluate

        Returns:
            Dictionary containing availability information:
            {
                "status": "placeholder",
                "members": {
                    "member_name": {
                        "available": true,
                        "preferences": {},
                        "constraints": []
                    }
                }
            }

        Example:
            >>> agent = AIAgent(api_client)
            >>> members = [{"name": "張三", "role": "證道"}, {"name": "李四", "role": "司會"}]
            >>> availability = agent.evaluate_availability_placeholder(members)
            >>> availability["status"]
            'placeholder'

        Note:
            **IMPLEMENTATION POINT**: Replace this method with real availability logic.
            This is where you should implement:
            1. Member preference retrieval
            2. Historical availability analysis
            3. Conflict detection (e.g., vacations, other commitments)
            4. Role-specific availability checks
        """
        logger.info(f"Evaluating availability for {len(members)} members (using placeholder)")

        # Build deterministic default availability
        availability = {
            "status": "placeholder",
            "evaluation_date": date.today().isoformat(),
            "members": {}
        }

        # Extract unique member names from the list
        unique_members = set()
        for member in members:
            if "name" in member and member["name"]:
                unique_members.add(member["name"])

        # Assign default availability to each member
        for member_name in sorted(unique_members):
            availability["members"][member_name] = {
                "available": True,
                "preferences": {},
                "constraints": [],
                "note": "Default availability - replace with actual logic"
            }

        logger.info(
            f"Generated placeholder availability for {len(availability['members'])} unique members"
        )

        return availability

    def build_ai_payload(
        self,
        historical_events: List[Dict[str, Any]],
        availability: Dict[str, Any],
        months_ahead: int = 3,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build a JSON-serializable payload for AI roster generation.

        This method combines historical events, member availability, and
        generation parameters into a structured payload ready for AI consumption.

        Args:
            historical_events: List of historical event dictionaries
            availability: Member availability dictionary from evaluate_availability_placeholder
            months_ahead: Number of months to generate rosters for (default: 3)
            category: Optional category for the roster generation

        Returns:
            Dictionary containing:
            {
                "metadata": {
                    "generation_request_id": "uuid",
                    "category": "chinese",
                    "date_range": {
                        "from": "2024-01-01",
                        "to": "2024-03-31"
                    },
                    "generated_at": "2024-01-15"
                },
                "historical_events": [...],
                "availability": {...},
                "generation_params": {
                    "months_ahead": 3,
                    "strategy": "balanced"
                }
            }

        Raises:
            ValueError: If months_ahead is not positive

        Example:
            >>> agent = AIAgent(api_client)
            >>> events = agent.fetch_last_three_months('chinese')
            >>> members = [{"name": "張三"}, {"name": "李四"}]
            >>> availability = agent.evaluate_availability_placeholder(members)
            >>> payload = agent.build_ai_payload(events, availability, months_ahead=3, category='chinese')
            >>> payload["metadata"]["category"]
            'chinese'
        """
        if months_ahead <= 0:
            raise ValueError(f"months_ahead must be positive, got {months_ahead}")

        # Generate unique request ID
        generation_request_id = str(uuid.uuid4())

        # Calculate date range for generation
        today = date.today()
        # Rough approximation: 30 days per month
        end_date = today + timedelta(days=30 * months_ahead)

        logger.info(
            f"Building AI payload (request_id: {generation_request_id}): "
            f"{len(historical_events)} historical events, "
            f"{len(availability.get('members', {}))} members, "
            f"{months_ahead} months ahead"
        )

        # Build the payload
        payload = {
            "metadata": {
                "generation_request_id": generation_request_id,
                "category": category,
                "date_range": {
                    "from": today.isoformat(),
                    "to": end_date.isoformat()
                },
                "generated_at": today.isoformat()
            },
            "historical_events": historical_events,
            "availability": availability,
            "generation_params": {
                "months_ahead": months_ahead,
                "strategy": "balanced",  # Can be extended with different strategies
                "note": "Default strategy - can be customized based on requirements"
            }
        }

        logger.info(f"AI payload built successfully (request_id: {generation_request_id})")

        return payload
