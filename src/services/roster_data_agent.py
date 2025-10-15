"""
Roster Data Agent for gathering and preparing roster data.

This module is responsible for collecting historical roster data and member
availability to prepare structured data for analysis and roster generation.
This agent does NOT perform AI analysis - it only gathers and prepares data.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import logging

from .roster_api_client import RosterAPIClient

logger = logging.getLogger(__name__)


class RosterDataAgent:
    """
    Data agent responsible for gathering and preparing roster data.

    This agent handles:
    - Fetching historical roster/event data
    - Evaluating member availability
    - Preparing structured data for analysis

    This agent does NOT:
    - Perform AI analysis
    - Generate roster recommendations
    - Validate rosters
    """

    def __init__(self, api_client: RosterAPIClient):
        """
        Initialize the Roster Data Agent with an API client.

        Args:
            api_client: RosterAPIClient instance for fetching roster data
        """
        self.api_client = api_client

    def fetch_historical_events(
        self,
        months: int = 3,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical events from the specified number of months back.

        This method retrieves historical roster events from today minus
        the specified months up to today, optionally filtered by category.

        Args:
            months: Number of months to look back (default: 3)
            category: Optional service category filter ('chinese', 'english', 'sundayschool')

        Returns:
            List of event dictionaries from the API

        Raises:
            ValueError: If months is not positive
            InvalidCategoryError: If category is invalid
            APIError: If API request fails

        Example:
            >>> agent = RosterDataAgent(api_client)
            >>> events = agent.fetch_historical_events(months=3, category='chinese')
            >>> len(events)
            12
        """
        if months <= 0:
            raise ValueError(f"months must be positive, got {months}")

        today = date.today()
        from_date = today - timedelta(days=30 * months)
        to_date = today

        logger.info(
            f"Fetching events from last {months} months: {from_date} to {to_date}"
            f"{f' (category: {category})' if category else ''}"
        )

        events = self.api_client.get_events(
            category=category,
            from_date=from_date,
            to_date=to_date
        )

        logger.info(f"Retrieved {len(events)} events from the last {months} months")
        return events

    def evaluate_member_availability(
        self,
        members: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate member availability for roster assignments.

        Currently returns deterministic default availability for all members.

        **FUTURE IMPLEMENTATION**: This method should be enhanced to:
        - Query member preference database
        - Analyze historical availability patterns
        - Detect scheduling conflicts (vacations, holidays)
        - Apply role-specific availability rules
        - Consider capacity constraints

        Args:
            members: List of member dictionaries to evaluate

        Returns:
            Dictionary containing availability information:
            {
                "status": "placeholder",
                "evaluation_date": "2024-01-15",
                "members": {
                    "member_name": {
                        "available": true,
                        "preferences": {},
                        "constraints": [],
                        "note": "..."
                    }
                }
            }

        Example:
            >>> agent = RosterDataAgent(api_client)
            >>> members = [{"name": "張三", "role": "證道"}, {"name": "李四", "role": "司會"}]
            >>> availability = agent.evaluate_member_availability(members)
            >>> availability["status"]
            'placeholder'
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

    def prepare_analysis_data(
        self,
        months: int = 3,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare complete data package for roster analysis.

        This is a convenience method that:
        1. Fetches historical events
        2. Extracts members from events
        3. Evaluates member availability
        4. Packages everything into a structured format

        Args:
            months: Number of months of historical data to fetch (default: 3)
            category: Optional service category filter

        Returns:
            Dictionary containing:
            {
                "historical_events": [...],
                "availability": {...},
                "metadata": {
                    "category": "chinese",
                    "months_analyzed": 3,
                    "total_events": 12,
                    "unique_members": 8,
                    "prepared_at": "2024-01-15"
                }
            }

        Example:
            >>> agent = RosterDataAgent(api_client)
            >>> data = agent.prepare_analysis_data(months=3, category='chinese')
            >>> print(data['metadata']['total_events'])
            12
        """
        logger.info(
            f"Preparing analysis data: {months} months"
            f"{f', category: {category}' if category else ''}"
        )

        # Fetch historical events
        events = self.fetch_historical_events(months=months, category=category)

        # Extract members from events
        members = []
        for event in events:
            event_members = event.get('members', [])
            members.extend(event_members)

        # Evaluate availability
        availability = self.evaluate_member_availability(members)

        # Build metadata
        metadata = {
            "category": category,
            "months_analyzed": months,
            "total_events": len(events),
            "unique_members": len(availability.get('members', {})),
            "prepared_at": date.today().isoformat()
        }

        # Package everything
        data = {
            "historical_events": events,
            "availability": availability,
            "metadata": metadata
        }

        logger.info(
            f"Data preparation complete: {metadata['total_events']} events, "
            f"{metadata['unique_members']} unique members"
        )

        return data

    def extract_members_from_events(
        self,
        events: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract all member assignments from a list of events.

        Args:
            events: List of event dictionaries

        Returns:
            List of member dictionaries (may contain duplicates)

        Example:
            >>> events = [{"members": [{"name": "張三"}, {"name": "李四"}]}]
            >>> members = agent.extract_members_from_events(events)
            >>> len(members)
            2
        """
        members = []
        for event in events:
            event_members = event.get('members', [])
            members.extend(event_members)

        logger.debug(f"Extracted {len(members)} member assignments from {len(events)} events")
        return members
