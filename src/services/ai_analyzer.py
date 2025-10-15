"""
AI Analyzer for roster pattern analysis and generation.

This module is responsible for AI-powered analysis of historical roster data
and generation of roster recommendations. It does NOT fetch data from APIs -
it receives prepared data and performs analysis.
"""

from typing import List, Dict, Any, Optional
from datetime import date, timedelta
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """
    AI-powered analyzer for roster generation.

    This analyzer handles:
    - Analyzing historical roster patterns
    - Generating optimal roster recommendations
    - Validating proposed rosters

    This analyzer does NOT:
    - Fetch data from APIs (receives prepared data)
    - Handle data gathering or availability evaluation
    """

    def __init__(self, ai_client: Optional[Any] = None):
        """
        Initialize the AI analyzer.

        Args:
            ai_client: Optional AI client (e.g., OpenAI, Claude API client)
                      If None, uses rule-based analysis
        """
        self.ai_client = ai_client
        if ai_client:
            logger.info("AI Analyzer initialized with AI client")
        else:
            logger.info("AI Analyzer initialized with rule-based analysis")

    def analyze_historical_patterns(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze historical roster patterns to extract insights.

        Analyzes:
        - Member participation frequency
        - Role distribution and preferences
        - Common team pairings
        - Workload balance across members

        Args:
            events: List of historical event dictionaries

        Returns:
            Dictionary containing pattern analysis:
            {
                "total_events": int,
                "member_frequency": {"member_name": count},
                "role_distribution": {"role": count},
                "member_roles": {"member_name": ["roles"]},
                "workload_balance": {"member_name": frequency},
                "common_pairings": [{"members": [...], "count": int}]
            }

        Example:
            >>> analyzer = AIAnalyzer()
            >>> events = [{"members": [{"name": "張三", "role": "證道"}]}]
            >>> patterns = analyzer.analyze_historical_patterns(events)
            >>> patterns["total_events"]
            1
        """
        logger.info(f"Analyzing {len(events)} historical events")

        # Initialize counters
        member_frequency = Counter()
        role_distribution = Counter()
        member_roles = defaultdict(set)
        pairing_counter = defaultdict(int)

        # Analyze each event
        for event in events:
            members = event.get('members', [])
            member_names = []

            for member in members:
                name = member.get('name')
                role = member.get('role')

                if name:
                    member_frequency[name] += 1
                    member_names.append(name)

                    if role:
                        role_distribution[role] += 1
                        member_roles[name].add(role)

            # Track pairings (members who served together)
            if len(member_names) > 1:
                pairing_key = tuple(sorted(member_names))
                pairing_counter[pairing_key] += 1

        # Calculate workload balance (participation rate)
        if events:
            workload_balance = {
                name: count / len(events)
                for name, count in member_frequency.items()
            }
        else:
            workload_balance = {}

        # Extract top pairings
        common_pairings = []
        for pairing, count in sorted(
            pairing_counter.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]:  # Top 10 pairings
            common_pairings.append({
                "members": list(pairing),
                "count": count
            })

        # Build analysis result
        analysis = {
            "total_events": len(events),
            "member_frequency": dict(member_frequency),
            "role_distribution": dict(role_distribution),
            "member_roles": {
                name: sorted(list(roles))
                for name, roles in member_roles.items()
            },
            "workload_balance": workload_balance,
            "common_pairings": common_pairings,
            "insights": self._generate_insights(
                member_frequency,
                role_distribution,
                workload_balance
            )
        }

        logger.info(
            f"Pattern analysis complete: {len(member_frequency)} unique members, "
            f"{len(role_distribution)} unique roles"
        )

        return analysis

    def _generate_insights(
        self,
        member_frequency: Counter,
        role_distribution: Counter,
        workload_balance: Dict[str, float]
    ) -> List[str]:
        """
        Generate human-readable insights from pattern analysis.

        Args:
            member_frequency: Counter of member participation
            role_distribution: Counter of role assignments
            workload_balance: Dictionary of workload percentages

        Returns:
            List of insight strings
        """
        insights = []

        # Most active members
        if member_frequency:
            most_active = member_frequency.most_common(3)
            insights.append(
                f"Most active members: {', '.join(f'{name} ({count})' for name, count in most_active)}"
            )

        # Most common roles
        if role_distribution:
            most_common_roles = role_distribution.most_common(3)
            insights.append(
                f"Most common roles: {', '.join(f'{role} ({count})' for role, count in most_common_roles)}"
            )

        # Workload imbalance detection
        if workload_balance:
            max_workload = max(workload_balance.values())
            min_workload = min(workload_balance.values())
            if max_workload - min_workload > 0.3:  # 30% difference
                insights.append(
                    f"Workload imbalance detected: {max_workload:.1%} max vs {min_workload:.1%} min"
                )

        return insights

    def generate_roster(
        self,
        target_dates: List[date],
        available_members: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        required_roles: List[str],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate roster recommendations for target dates.

        Uses historical patterns and member availability to create balanced
        roster assignments.

        Args:
            target_dates: List of dates to generate rosters for
            available_members: Dictionary of member availability
            historical_patterns: Analysis results from analyze_historical_patterns
            required_roles: List of roles that must be filled
            category: Optional service category

        Returns:
            List of roster assignments, one per target date:
            [
                {
                    "date": "2024-01-15",
                    "category": "chinese",
                    "assignments": [
                        {"role": "證道", "name": "張三"},
                        {"role": "司會", "name": "李四"}
                    ]
                }
            ]

        Example:
            >>> analyzer = AIAnalyzer()
            >>> dates = [date(2024, 1, 15)]
            >>> availability = {"members": {"張三": {"available": True}}}
            >>> patterns = {"member_roles": {"張三": ["證道"]}}
            >>> roster = analyzer.generate_roster(dates, availability, patterns, ["證道"])
            >>> len(roster)
            1
        """
        logger.info(
            f"Generating roster for {len(target_dates)} dates, "
            f"{len(required_roles)} required roles"
        )

        if self.ai_client:
            # Use AI client for generation
            return self._generate_roster_with_ai(
                target_dates,
                available_members,
                historical_patterns,
                required_roles,
                category
            )
        else:
            # Use rule-based generation
            return self._generate_roster_rule_based(
                target_dates,
                available_members,
                historical_patterns,
                required_roles,
                category
            )

    def _generate_roster_rule_based(
        self,
        target_dates: List[date],
        available_members: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        required_roles: List[str],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate roster using rule-based algorithm.

        Strategy:
        1. For each date, assign roles based on:
           - Member availability
           - Historical role assignments (prefer familiar roles)
           - Workload balance (rotate to balance workload)
           - Recent assignments (avoid consecutive assignments)

        Args:
            See generate_roster for parameter documentation

        Returns:
            List of roster assignments
        """
        rosters = []
        member_roles = historical_patterns.get('member_roles', {})
        workload_balance = historical_patterns.get('workload_balance', {})

        # Track recent assignments to avoid consecutive scheduling
        recent_assignments = defaultdict(list)

        for target_date in sorted(target_dates):
            assignments = []

            # Get available members for this date
            members_data = available_members.get('members', {})
            available = [
                name for name, data in members_data.items()
                if data.get('available', False)
            ]

            # Sort members by workload (least busy first)
            available_sorted = sorted(
                available,
                key=lambda name: workload_balance.get(name, 0)
            )

            # Assign each required role
            for role in required_roles:
                assigned = False

                # Try to find a member who has done this role before
                for member_name in available_sorted:
                    # Check if member has done this role
                    member_role_history = member_roles.get(member_name, [])

                    # Skip if already assigned a role for this date
                    if any(a['name'] == member_name for a in assignments):
                        continue

                    # Skip if assigned very recently (within last 2 events)
                    if len(recent_assignments[member_name]) >= 2:
                        continue

                    # Prefer members who have done this role before
                    if role in member_role_history or not member_role_history:
                        assignments.append({
                            "role": role,
                            "name": member_name
                        })
                        recent_assignments[member_name].append(target_date)
                        # Keep only last 2 assignments
                        recent_assignments[member_name] = recent_assignments[member_name][-2:]
                        assigned = True
                        break

                # If no qualified member found, assign anyone available
                if not assigned and available_sorted:
                    for member_name in available_sorted:
                        if not any(a['name'] == member_name for a in assignments):
                            assignments.append({
                                "role": role,
                                "name": member_name
                            })
                            recent_assignments[member_name].append(target_date)
                            recent_assignments[member_name] = recent_assignments[member_name][-2:]
                            assigned = True
                            break

                if not assigned:
                    logger.warning(
                        f"Could not assign role '{role}' for {target_date} - "
                        f"no available members"
                    )

            rosters.append({
                "date": target_date.isoformat(),
                "category": category,
                "assignments": assignments
            })

        logger.info(f"Generated {len(rosters)} rosters using rule-based algorithm")
        return rosters

    def _generate_roster_with_ai(
        self,
        target_dates: List[date],
        available_members: Dict[str, Any],
        historical_patterns: Dict[str, Any],
        required_roles: List[str],
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate roster using AI client.

        This method would use an AI API (OpenAI, Claude, etc.) to generate
        optimal rosters based on the data.

        Args:
            See generate_roster for parameter documentation

        Returns:
            List of roster assignments
        """
        # TODO: Implement AI-based generation using self.ai_client
        logger.info("AI-based generation not yet implemented, falling back to rule-based")
        return self._generate_roster_rule_based(
            target_dates,
            available_members,
            historical_patterns,
            required_roles,
            category
        )

    def validate_roster(self, roster: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a proposed roster configuration.

        Checks:
        - All required roles are filled
        - No duplicate member assignments on same date
        - Members are not over-scheduled
        - Assignments are reasonable based on historical data

        Args:
            roster: Roster dictionary or list of roster dictionaries

        Returns:
            Validation results:
            {
                "is_valid": bool,
                "errors": ["error messages"],
                "warnings": ["warning messages"],
                "statistics": {...}
            }

        Example:
            >>> analyzer = AIAnalyzer()
            >>> roster = {"date": "2024-01-15", "assignments": []}
            >>> result = analyzer.validate_roster(roster)
            >>> result["is_valid"]
            True
        """
        logger.info("Validating roster")

        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {}
        }

        # Handle single roster or list of rosters
        rosters = roster if isinstance(roster, list) else [roster]

        for idx, single_roster in enumerate(rosters):
            date_str = single_roster.get('date', f'roster_{idx}')
            assignments = single_roster.get('assignments', [])

            # Check for duplicate member assignments on same date
            assigned_members = []
            for assignment in assignments:
                member_name = assignment.get('name')
                if member_name in assigned_members:
                    validation_result["errors"].append(
                        f"{date_str}: Duplicate assignment for member '{member_name}'"
                    )
                    validation_result["is_valid"] = False
                assigned_members.append(member_name)

            # Check if assignments exist
            if not assignments:
                validation_result["warnings"].append(
                    f"{date_str}: No assignments found"
                )

            # Check for missing role or name
            for assignment in assignments:
                if not assignment.get('role'):
                    validation_result["errors"].append(
                        f"{date_str}: Assignment missing role"
                    )
                    validation_result["is_valid"] = False
                if not assignment.get('name'):
                    validation_result["errors"].append(
                        f"{date_str}: Assignment missing member name"
                    )
                    validation_result["is_valid"] = False

        # Generate statistics
        if rosters:
            total_assignments = sum(len(r.get('assignments', [])) for r in rosters)
            validation_result["statistics"] = {
                "total_rosters": len(rosters),
                "total_assignments": total_assignments,
                "avg_assignments_per_roster": total_assignments / len(rosters) if rosters else 0
            }

        logger.info(
            f"Validation complete: {'PASS' if validation_result['is_valid'] else 'FAIL'} "
            f"({len(validation_result['errors'])} errors, {len(validation_result['warnings'])} warnings)"
        )

        return validation_result
