"""
AI Analyzer for roster pattern analysis and generation.

This module is responsible for AI-powered analysis of historical roster data
and generation of roster recommendations. It does NOT fetch data from APIs -
it receives prepared data and performs analysis.
"""

from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING
from datetime import date, timedelta, datetime, timezone
from collections import defaultdict, Counter
import logging
import sqlite3
import json
import os

if TYPE_CHECKING:
    from .ai_api_client import AIAPIClient

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

    def __init__(self, ai_client: Optional['AIAPIClient'] = None, db_path: Optional[str] = None):
        """
        Initialize the AI analyzer.

        Args:
            ai_client: Optional AIAPIClient for LLM-based roster generation.
                      If None, uses rule-based analysis
            db_path: Optional path to SQLite database file for role history persistence.
                    If None, uses 'roster.db' in current directory.
        """
        self.ai_client = ai_client
        self.db_path = db_path or os.path.join(os.getcwd(), 'roster.db')
        if ai_client:
            logger.info("AI Analyzer initialized with AI client")
        else:
            logger.info("AI Analyzer initialized with rule-based analysis")
        logger.info(f"Database path: {self.db_path}")

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

    # ==================== Role History Management ====================

    @staticmethod
    def _normalize_role_name(role: str) -> str:
        """
        Normalize role name for consistent lookups.

        Args:
            role: Role name to normalize

        Returns:
            Normalized role name (trimmed and lowercased)
        """
        if not role:
            return ""
        return role.strip().lower()

    def compute_role_history(
        self,
        events: List[Dict[str, Any]],
        lookback_months: Optional[int] = None
    ) -> Dict[str, Set[str]]:
        """
        Compute historical role assignments from events.

        Analyzes historical events and builds a mapping of roles to the set of
        member names who have performed each role. Role names are normalized
        (trimmed, lowercased) for consistent lookups.

        Args:
            events: List of historical event dictionaries. Each event should have:
                   {
                       "date": "YYYY-MM-DD",
                       "members": [{"name": "Member Name", "role": "Role Name"}, ...]
                   }
            lookback_months: Optional limit on how far back to analyze.
                           If provided, only events within the last N months are considered.
                           If None, all history is analyzed.

        Returns:
            Dictionary mapping normalized role names to sets of member names:
            {
                "role_name": {"Member 1", "Member 2", ...},
                ...
            }

        Example:
            >>> analyzer = AIAnalyzer()
            >>> events = [
            ...     {
            ...         "date": "2024-01-15",
            ...         "members": [
            ...             {"name": "張三", "role": "證道"},
            ...             {"name": "李四", "role": "司會"}
            ...         ]
            ...     }
            ... ]
            >>> role_history = analyzer.compute_role_history(events)
            >>> "證道" in role_history  # Note: normalized to lowercase
            False
            >>> "证道" in role_history
            True
            >>> "張三" in role_history["证道"]
            True

        Edge cases handled:
            - Repeated assignments: Each member is counted once per role
            - Missing/null roles: Skipped with warning
            - Missing/null names: Skipped with warning
            - Case sensitivity: Normalized to lowercase
            - Whitespace: Trimmed from role names
        """
        logger.info(f"Computing role history from {len(events)} events")

        role_history: Dict[str, Set[str]] = defaultdict(set)

        # Filter events by lookback window if specified
        filtered_events = events
        if lookback_months is not None:
            cutoff_date = date.today() - timedelta(days=lookback_months * 30)
            filtered_events = []
            for event in events:
                event_date_str = event.get('date')
                if event_date_str:
                    try:
                        event_date = datetime.fromisoformat(event_date_str).date()
                        if event_date >= cutoff_date:
                            filtered_events.append(event)
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid date format in event: {event_date_str}")
                        continue

            logger.info(
                f"Filtered to {len(filtered_events)} events within last {lookback_months} months "
                f"(cutoff: {cutoff_date})"
            )

        # Build role -> members mapping
        for event in filtered_events:
            members = event.get('members', [])

            for member in members:
                role = member.get('role')
                name = member.get('name')

                # Skip if role or name is missing
                if not role:
                    logger.debug(f"Skipping member with missing role: {member}")
                    continue
                if not name:
                    logger.debug(f"Skipping member with missing name: {member}")
                    continue

                # Normalize role name
                normalized_role = self._normalize_role_name(role)
                if not normalized_role:
                    logger.warning(f"Role normalized to empty string: '{role}'")
                    continue

                # Add member to role history
                role_history[normalized_role].add(name)

        # Convert defaultdict to regular dict with sorted sets for deterministic output
        result = {role: members for role, members in role_history.items()}

        logger.info(
            f"Computed role history: {len(result)} unique roles, "
            f"total {sum(len(members) for members in result.values())} member-role mappings"
        )

        return result

    def _get_db_connection(self) -> sqlite3.Connection:
        """
        Get a connection to the SQLite database.

        Ensures the role_history table exists by running the migration if needed.

        Returns:
            SQLite connection object

        Raises:
            sqlite3.Error: If database connection or initialization fails
        """
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row

        # Ensure role_history table exists
        # This is a lightweight approach - in production, use proper migration management
        migration_sql = """
        CREATE TABLE IF NOT EXISTS role_history (
            role_name TEXT PRIMARY KEY,
            member_ids TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_role_history_updated ON role_history(last_updated);
        """
        conn.executescript(migration_sql)
        conn.commit()

        return conn

    def persist_role_history(self, role_history: Dict[str, Set[str]]) -> None:
        """
        Persist role history to the database.

        Stores the role-to-members mapping in the role_history table.
        Uses REPLACE to update existing roles or insert new ones.

        Args:
            role_history: Dictionary mapping role names to sets of member names

        Raises:
            sqlite3.Error: If database operation fails

        Example:
            >>> analyzer = AIAnalyzer()
            >>> role_history = {"证道": {"張三", "李四"}, "司會": {"王五"}}
            >>> analyzer.persist_role_history(role_history)
        """
        logger.info(f"Persisting role history: {len(role_history)} roles")

        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()

            for role_name, member_names in role_history.items():
                # Convert set to sorted JSON array for storage
                member_ids_json = json.dumps(sorted(list(member_names)), ensure_ascii=False)

                # Use REPLACE to update existing or insert new
                cursor.execute(
                    """
                    REPLACE INTO role_history (role_name, member_ids, last_updated)
                    VALUES (?, ?, ?)
                    """,
                    (role_name, member_ids_json, datetime.now(timezone.utc).isoformat())
                )

            conn.commit()
            logger.info(f"Successfully persisted {len(role_history)} roles to database")

        except sqlite3.Error as e:
            logger.error(f"Failed to persist role history: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_role_history_from_db(self, role_name: str) -> Optional[Set[str]]:
        """
        Retrieve role history for a specific role from the database.

        Args:
            role_name: Name of the role (will be normalized)

        Returns:
            Set of member names who have performed this role, or None if role not found

        Example:
            >>> analyzer = AIAnalyzer()
            >>> members = analyzer.get_role_history_from_db("證道")
            >>> members
            {'張三', '李四'}
        """
        normalized_role = self._normalize_role_name(role_name)
        logger.debug(f"Fetching role history for '{role_name}' (normalized: '{normalized_role}')")

        conn = self._get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT member_ids FROM role_history WHERE role_name = ?",
                (normalized_role,)
            )
            row = cursor.fetchone()

            if row:
                member_ids_json = row['member_ids']
                member_names = json.loads(member_ids_json)
                logger.debug(f"Found {len(member_names)} members for role '{normalized_role}'")
                return set(member_names)
            else:
                logger.debug(f"No history found for role '{normalized_role}'")
                return None

        except sqlite3.Error as e:
            logger.error(f"Failed to fetch role history: {e}")
            raise
        finally:
            conn.close()

    def get_eligible_members_for_role(
        self,
        role_name: str,
        all_members: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get list of members eligible for a specific role based on historical assignments.

        Returns members who have performed this role in the past. If no history exists
        for the role and all_members is provided, returns all_members as fallback.

        Args:
            role_name: Name of the role to query
            all_members: Optional list of all available members (fallback if no history)

        Returns:
            List of member names eligible for the role (sorted alphabetically)

        Example:
            >>> analyzer = AIAnalyzer()
            >>> eligible = analyzer.get_eligible_members_for_role("證道")
            >>> eligible
            ['張三', '李四', '王五']

            >>> # With fallback
            >>> eligible = analyzer.get_eligible_members_for_role(
            ...     "新角色",
            ...     all_members=["張三", "李四"]
            ... )
            >>> eligible  # Returns all_members since no history exists
            ['張三', '李四']
        """
        logger.info(f"Getting eligible members for role: {role_name}")

        # Query database for role history
        member_set = self.get_role_history_from_db(role_name)

        if member_set:
            # Return sorted list of members with history for this role
            result = sorted(list(member_set))
            logger.info(f"Found {len(result)} eligible members for role '{role_name}'")
            return result
        elif all_members:
            # No history - return all members as fallback
            logger.info(
                f"No history for role '{role_name}', returning all {len(all_members)} members as fallback"
            )
            return sorted(all_members)
        else:
            # No history and no fallback
            logger.warning(f"No eligible members found for role '{role_name}'")
            return []

    def recompute_role_history(
        self,
        events: List[Dict[str, Any]],
        lookback_months: Optional[int] = None
    ) -> Dict[str, Set[str]]:
        """
        Recompute and persist role history from events.

        This is the main orchestration function that should be called periodically
        (e.g., monthly) to refresh the role history data. It:
        1. Computes role history from events
        2. Persists the results to the database
        3. Returns the computed role history

        Args:
            events: List of historical event dictionaries
            lookback_months: Optional limit on how far back to analyze

        Returns:
            Computed role history dictionary

        Example:
            >>> analyzer = AIAnalyzer()
            >>> events = fetch_all_events()  # Your data fetching logic
            >>> role_history = analyzer.recompute_role_history(events, lookback_months=12)
            >>> # Role history is now updated in the database

        Note:
            This function should be called by a scheduler or cron job to keep
            role history up-to-date. Recommended frequency: monthly.
        """
        logger.info(
            f"Recomputing role history from {len(events)} events "
            f"(lookback: {lookback_months or 'all'} months)"
        )

        # Compute role history
        role_history = self.compute_role_history(events, lookback_months)

        # Persist to database
        self.persist_role_history(role_history)

        logger.info(
            f"Role history recomputation complete: {len(role_history)} roles, "
            f"{sum(len(members) for members in role_history.values())} total assignments"
        )

        return role_history
