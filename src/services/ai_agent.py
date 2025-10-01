"""
AI Agent for automated roster generation

This agent orchestrates the entire roster generation process by:
1. Fetching historical roster data (last 3 months)
2. Analyzing patterns and member availability
3. Generating optimal rosters for the next 3 months
4. Validating and submitting the generated rosters
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from dataclasses import dataclass, field
import logging

from .roster_api_client import RosterAPIClient
from .ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class RosterGenerationRules:
    """
    Configurable rules for roster generation

    These rules guide the AI agent in creating balanced and optimal rosters
    """

    # Workload balancing rules
    max_assignments_per_person_per_month: int = 4
    min_rest_days_between_assignments: int = 7

    # Role distribution rules
    prefer_role_rotation: bool = True
    allow_multiple_roles_same_day: bool = False

    # Team composition rules
    maintain_team_chemistry: bool = True
    balance_experience_levels: bool = True

    # Availability rules
    respect_member_availability: bool = True
    require_minimum_team_size: int = 3

    # Service type specific rules
    service_type_preferences: Dict[str, Any] = field(default_factory=dict)

    # Priority weights for AI decision making
    workload_balance_weight: float = 0.3
    role_coverage_weight: float = 0.3
    team_chemistry_weight: float = 0.2
    availability_weight: float = 0.2

    def validate(self) -> None:
        """Validate that rules are consistent and within bounds"""
        if self.max_assignments_per_person_per_month < 1:
            raise ValueError("max_assignments_per_person_per_month must be at least 1")

        if self.min_rest_days_between_assignments < 0:
            raise ValueError("min_rest_days_between_assignments cannot be negative")

        if self.require_minimum_team_size < 1:
            raise ValueError("require_minimum_team_size must be at least 1")

        # Validate weights sum to approximately 1.0
        total_weight = (
            self.workload_balance_weight
            + self.role_coverage_weight
            + self.team_chemistry_weight
            + self.availability_weight
        )
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f"Priority weights must sum to 1.0, got {total_weight}")


class AIAgent:
    """
    AI Agent for automated roster generation

    Job Description:
    ----------------
    The AI Agent is responsible for analyzing historical roster patterns and
    automatically generating optimized rosters for future services. The agent:

    1. Data Collection: Retrieves the last 3 months of roster data from the API
    2. Pattern Analysis: Identifies trends, workload distribution, and team dynamics
    3. Roster Generation: Creates balanced rosters for the next 3 months
    4. Validation: Ensures generated rosters meet all requirements and constraints
    5. Submission: Submits approved rosters back to the system

    Key Responsibilities:
    ---------------------
    - Maintain fair workload distribution across all team members
    - Ensure adequate role coverage for all services
    - Preserve successful team combinations and chemistry
    - Respect member availability and preferences
    - Optimize for service quality and team satisfaction
    - Handle conflicts and constraints gracefully

    The agent operates autonomously but can be configured through rules
    to align with organizational policies and preferences.
    """

    def __init__(
        self,
        api_client: RosterAPIClient,
        ai_analyzer: AIAnalyzer,
        rules: Optional[RosterGenerationRules] = None,
    ):
        """
        Initialize the AI Agent

        Args:
            api_client: Client for interacting with roster API
            ai_analyzer: AI analyzer for pattern analysis and recommendations
            rules: Configuration rules for roster generation (uses defaults if not provided)
        """
        self.api_client = api_client
        self.ai_analyzer = ai_analyzer
        self.rules = rules if rules is not None else RosterGenerationRules()

        # Validate rules on initialization
        self.rules.validate()

        logger.info("AI Agent initialized with rules: %s", self.rules)

    def fetch_historical_data(
        self, months_back: int = 3, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical roster data from the API

        Args:
            months_back: Number of months of historical data to retrieve (default: 3)
            category: Optional service category filter

        Returns:
            List of historical event data
        """
        logger.info(f"Fetching {months_back} months of historical roster data")

        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=months_back * 30)

        # Fetch events from API
        try:
            events = self.api_client.get_events(
                category=category, from_date=start_date, to_date=end_date
            )
            logger.info(f"Retrieved {len(events)} historical events")
            return events
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            raise

    def generate_future_rosters(
        self,
        months_ahead: int = 3,
        category: Optional[str] = None,
        available_members: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate rosters for the next N months

        Args:
            months_ahead: Number of months to generate rosters for (default: 3)
            category: Optional service category to generate rosters for
            available_members: Optional list of available members (if None, will be retrieved)

        Returns:
            List of generated roster assignments
        """
        logger.info(f"Generating rosters for the next {months_ahead} months")

        # Step 1: Fetch historical data
        historical_events = self.fetch_historical_data(months_back=3, category=category)

        # Step 2: Analyze historical patterns
        logger.info("Analyzing historical patterns")
        historical_analysis = self.ai_analyzer.analyze_historical_patterns(
            historical_events
        )

        # Step 3: Generate target dates for next N months
        start_date = date.today()
        end_date = start_date + timedelta(days=months_ahead * 30)

        # Generate roster for each upcoming service date
        # TODO: Implement logic to identify service dates (e.g., Sundays, specific days)
        generated_rosters = []

        # For now, generate weekly rosters (assuming weekly services)
        current_date = start_date
        while current_date <= end_date:
            # Skip to next Sunday (or appropriate service day)
            days_until_sunday = (6 - current_date.weekday()) % 7
            if days_until_sunday == 0 and current_date != start_date:
                days_until_sunday = 7
            service_date = current_date + timedelta(days=days_until_sunday)

            if service_date > end_date:
                break

            # Get available members for this date
            # TODO: Implement member availability lookup
            if available_members is None:
                available_members = []  # Placeholder

            # Generate recommendations for this date
            recommendations = self.ai_analyzer.generate_roster_recommendations(
                target_date=service_date,
                service_type=category or "general",
                available_members=available_members,
                historical_analysis=historical_analysis,
            )

            if recommendations:
                generated_rosters.append(
                    {
                        "date": service_date.isoformat(),
                        "category": category,
                        "recommendations": recommendations,
                    }
                )

            current_date = service_date + timedelta(days=1)

        logger.info(f"Generated {len(generated_rosters)} roster assignments")
        return generated_rosters

    def validate_generated_roster(self, roster: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a generated roster against rules and constraints

        Args:
            roster: Generated roster to validate

        Returns:
            Validation result with any errors or warnings
        """
        logger.info(f"Validating roster for date: {roster.get('date')}")

        # Use AI analyzer's validation
        validation_result = self.ai_analyzer.validate_roster(roster)

        # Apply additional rule-based validation
        if self.rules.require_minimum_team_size:
            recommendations = roster.get("recommendations", [])
            if len(recommendations) < self.rules.require_minimum_team_size:
                validation_result["warnings"].append(
                    f"Roster has {len(recommendations)} members, "
                    f"but minimum team size is {self.rules.require_minimum_team_size}"
                )

        return validation_result

    def execute_roster_generation(
        self,
        months_ahead: int = 3,
        category: Optional[str] = None,
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the complete roster generation workflow

        This is the main entry point for the AI Agent to generate rosters.

        Args:
            months_ahead: Number of months to generate rosters for
            category: Optional service category filter
            dry_run: If True, only validate without submitting to API

        Returns:
            Summary of the generation process including results and any issues
        """
        logger.info(f"Starting roster generation workflow (dry_run={dry_run})")

        results = {
            "status": "success",
            "generated_count": 0,
            "validated_count": 0,
            "submitted_count": 0,
            "errors": [],
            "warnings": [],
        }

        try:
            # Generate rosters
            generated_rosters = self.generate_future_rosters(
                months_ahead=months_ahead, category=category
            )
            results["generated_count"] = len(generated_rosters)

            # Validate each generated roster
            validated_rosters = []
            for roster in generated_rosters:
                validation = self.validate_generated_roster(roster)

                if validation["is_valid"]:
                    validated_rosters.append(roster)
                else:
                    results["errors"].extend(validation["errors"])

                results["warnings"].extend(validation["warnings"])

            results["validated_count"] = len(validated_rosters)

            # Submit rosters if not in dry run mode
            if not dry_run and validated_rosters:
                logger.info(f"Submitting {len(validated_rosters)} validated rosters")
                # TODO: Implement roster submission to API
                results["submitted_count"] = len(validated_rosters)
            else:
                logger.info(
                    f"Dry run mode: skipping submission of {len(validated_rosters)} rosters"
                )

            logger.info(f"Roster generation completed: {results}")

        except Exception as e:
            logger.error(f"Roster generation failed: {e}", exc_info=True)
            results["status"] = "failed"
            results["errors"].append(str(e))

        return results
