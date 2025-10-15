"""
Roster Orchestrator for coordinating the complete roster generation workflow.

This module orchestrates the end-to-end process of roster generation by
coordinating between the RosterDataAgent and AIAnalyzer.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import logging

from .roster_data_agent import RosterDataAgent
from .ai_analyzer import AIAnalyzer

logger = logging.getLogger(__name__)


class RosterOrchestrator:
    """
    Orchestrates the complete roster generation workflow.

    This orchestrator coordinates:
    - Data gathering (via RosterDataAgent)
    - Pattern analysis (via AIAnalyzer)
    - Roster generation (via AIAnalyzer)
    - Validation (via AIAnalyzer)

    This provides a simple, high-level interface for the complete workflow.
    """

    def __init__(
        self,
        data_agent: RosterDataAgent,
        analyzer: AIAnalyzer
    ):
        """
        Initialize the orchestrator with required components.

        Args:
            data_agent: RosterDataAgent instance for data gathering
            analyzer: AIAnalyzer instance for analysis and generation
        """
        self.data_agent = data_agent
        self.analyzer = analyzer
        logger.info("RosterOrchestrator initialized")

    def generate_roster_for_upcoming_months(
        self,
        months_ahead: int = 3,
        category: Optional[str] = None,
        required_roles: Optional[List[str]] = None,
        historical_months: int = 3
    ) -> Dict[str, Any]:
        """
        Generate roster for upcoming months (complete workflow).

        This is the main entry point that executes the complete workflow:
        1. Gather historical data and availability
        2. Analyze historical patterns
        3. Generate roster recommendations
        4. Validate the generated roster

        Args:
            months_ahead: Number of months to generate rosters for (default: 3)
            category: Optional service category filter
            required_roles: List of roles that must be filled
                          If None, uses default roles
            historical_months: Number of months of historical data to analyze (default: 3)

        Returns:
            Dictionary containing:
            {
                "rosters": [...],
                "validation": {...},
                "patterns": {...},
                "metadata": {...}
            }

        Example:
            >>> orchestrator = RosterOrchestrator(data_agent, analyzer)
            >>> result = orchestrator.generate_roster_for_upcoming_months(
            ...     months_ahead=3,
            ...     category='chinese'
            ... )
            >>> len(result['rosters'])
            12  # ~12 weeks for 3 months
        """
        logger.info(
            f"Starting roster generation workflow: {months_ahead} months ahead, "
            f"category: {category or 'all'}"
        )

        try:
            # Step 1: Gather data
            logger.info("Step 1/4: Gathering historical data and availability")
            data = self.data_agent.prepare_analysis_data(
                months=historical_months,
                category=category
            )

            # Step 2: Analyze patterns
            logger.info("Step 2/4: Analyzing historical patterns")
            patterns = self.analyzer.analyze_historical_patterns(
                data['historical_events']
            )

            # Step 3: Generate target dates and roster
            logger.info("Step 3/4: Generating roster recommendations")
            target_dates = self._generate_target_dates(months_ahead, category)

            # Use default roles if not specified
            if required_roles is None:
                required_roles = self._get_default_roles(category)

            rosters = self.analyzer.generate_roster(
                target_dates=target_dates,
                available_members=data['availability'],
                historical_patterns=patterns,
                required_roles=required_roles,
                category=category
            )

            # Step 4: Validate
            logger.info("Step 4/4: Validating generated roster")
            validation = self.analyzer.validate_roster(rosters)

            # Package result
            result = {
                "rosters": rosters,
                "validation": validation,
                "patterns": patterns,
                "metadata": {
                    "months_ahead": months_ahead,
                    "category": category,
                    "historical_months": historical_months,
                    "target_dates_count": len(target_dates),
                    "required_roles": required_roles,
                    "generated_at": date.today().isoformat(),
                    "workflow_status": "success" if validation["is_valid"] else "completed_with_warnings"
                }
            }

            logger.info(
                f"Roster generation workflow complete: "
                f"{len(rosters)} rosters generated, "
                f"validation: {'PASS' if validation['is_valid'] else 'FAIL'}"
            )

            return result

        except Exception as e:
            logger.error(f"Roster generation workflow failed: {e}")
            raise

    def _generate_target_dates(
        self,
        months_ahead: int,
        category: Optional[str] = None
    ) -> List[date]:
        """
        Generate list of target dates for roster generation.

        Creates dates for Sundays (typical service day) over the specified
        number of months.

        Args:
            months_ahead: Number of months to generate dates for
            category: Optional category (may affect frequency)

        Returns:
            List of date objects

        Example:
            >>> dates = orchestrator._generate_target_dates(1)
            >>> len(dates)
            4  # ~4 Sundays in a month
        """
        target_dates = []
        today = date.today()

        # Find next Sunday
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7  # Skip today if it's Sunday
        next_sunday = today + timedelta(days=days_until_sunday)

        # Generate Sundays for the specified months
        end_date = today + timedelta(days=30 * months_ahead)
        current_date = next_sunday

        while current_date <= end_date:
            target_dates.append(current_date)
            current_date += timedelta(days=7)  # Next week

        logger.debug(f"Generated {len(target_dates)} target dates from {next_sunday} to {end_date}")
        return target_dates

    def _get_default_roles(self, category: Optional[str] = None) -> List[str]:
        """
        Get default required roles based on category.

        Args:
            category: Service category

        Returns:
            List of role names

        Example:
            >>> roles = orchestrator._get_default_roles('chinese')
            >>> '證道' in roles
            True
        """
        # Default roles for Chinese services
        chinese_roles = ['證道', '司會', '詩歌讚美', '招待', '音控']

        # Default roles for English services
        english_roles = ['Preacher', 'Host', 'Worship Leader', 'Usher', 'Sound']

        # Default roles for Sunday School
        sundayschool_roles = ['Teacher', 'Helper']

        if category:
            category_lower = category.lower().strip()
            if category_lower == 'chinese':
                return chinese_roles
            elif category_lower == 'english':
                return english_roles
            elif category_lower == 'sundayschool':
                return sundayschool_roles

        # Default: use Chinese roles
        return chinese_roles

    def analyze_patterns_only(
        self,
        months: int = 3,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze historical patterns without generating roster.

        Useful for:
        - Understanding current member distribution
        - Identifying workload imbalances
        - Reviewing historical patterns

        Args:
            months: Number of months of historical data to analyze
            category: Optional service category filter

        Returns:
            Dictionary containing:
            {
                "patterns": {...},
                "data_summary": {...}
            }

        Example:
            >>> result = orchestrator.analyze_patterns_only(months=6)
            >>> result['patterns']['total_events']
            24
        """
        logger.info(f"Analyzing patterns for last {months} months")

        # Gather data
        data = self.data_agent.prepare_analysis_data(
            months=months,
            category=category
        )

        # Analyze patterns
        patterns = self.analyzer.analyze_historical_patterns(
            data['historical_events']
        )

        result = {
            "patterns": patterns,
            "data_summary": data['metadata']
        }

        logger.info(
            f"Pattern analysis complete: {patterns['total_events']} events analyzed"
        )

        return result

    def validate_existing_roster(
        self,
        roster: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate an existing roster without generating a new one.

        Args:
            roster: Roster dictionary or list of rosters to validate

        Returns:
            Validation results from AIAnalyzer

        Example:
            >>> roster = {"date": "2024-01-15", "assignments": [...]}
            >>> result = orchestrator.validate_existing_roster(roster)
            >>> result['is_valid']
            True
        """
        logger.info("Validating existing roster")
        return self.analyzer.validate_roster(roster)
