"""
Concrete implementation of IRoleHistoryManager.

This module provides the actual business logic for managing historical role
assignments and determining member eligibility for roles.
"""

from typing import Dict, Set, List, Any, Optional
from datetime import datetime, timedelta, date
from collections import defaultdict
import logging

from src.interfaces.role_history_manager import IRoleHistoryManager, IStorageAdapter

logger = logging.getLogger(__name__)


class RoleHistoryManager(IRoleHistoryManager):
    """
    Concrete implementation of IRoleHistoryManager.

    Manages historical role assignments and member eligibility based on
    past performance. Uses the Strategy pattern via IStorageAdapter to
    support different storage backends.

    Attributes:
        storage_adapter: The storage backend implementation
    """

    def __init__(self, storage_adapter: IStorageAdapter):
        """
        Initialize the role history manager.

        Args:
            storage_adapter: Implementation of IStorageAdapter for persistence
        """
        self.storage_adapter = storage_adapter
        logger.info("RoleHistoryManager initialized with storage adapter")

    def normalize_role_name(self, role: str) -> str:
        """
        Normalize role name for consistent lookups.

        Normalization rules:
        - Convert to lowercase
        - Trim leading/trailing whitespace
        - Handle empty/null inputs

        Args:
            role: Raw role name from event data

        Returns:
            Normalized role name (lowercase, trimmed)
            Empty string if input is None or empty

        Example:
            >>> manager.normalize_role_name("  證道  ")
            "證道"
            >>> manager.normalize_role_name("PREACHER")
            "preacher"
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

        Analyzes event data to build a mapping of roles to the members
        who have performed them. Role names are normalized for consistency.

        Args:
            events: List of event dictionaries, each containing:
                {
                    "date": "YYYY-MM-DD",
                    "members": [
                        {"name": "張三", "role": "證道"},
                        {"name": "李四", "role": "司會"}
                    ]
                }
            lookback_months: Optional limit - only analyze events from last N months.
                           If None, analyzes all history.
                           If provided, filters events where date >= (today - N months)

        Returns:
            Dictionary mapping normalized role names to sets of member names:
            {
                "證道": {"張三", "李四", "王五"},
                "司會": {"李四", "趙六"}
            }

        Raises:
            ValueError: If events is None or has invalid structure

        Example:
            >>> events = [
            ...     {
            ...         "date": "2024-01-15",
            ...         "members": [
            ...             {"name": "張三", "role": "證道"}
            ...         ]
            ...     }
            ... ]
            >>> history = manager.compute_role_history(events)
            >>> history["證道"]
            {"張三"}

        Edge Cases:
            - Missing "members" key: Skipped with warning
            - Missing "role" or "name": Skipped with warning
            - Duplicate member-role pairs: Counted once (using Set)
            - Invalid date format: Skipped with warning if lookback_months specified
        """
        if events is None:
            raise ValueError("events cannot be None")

        logger.info(f"Computing role history from {len(events)} events")

        role_history: Dict[str, Set[str]] = defaultdict(set)

        # Filter by lookback window if specified
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
                normalized_role = self.normalize_role_name(role)
                if not normalized_role:
                    logger.warning(f"Role normalized to empty string: '{role}'")
                    continue

                # Add member to role history
                role_history[normalized_role].add(name)

        # Convert defaultdict to regular dict
        result = {role: members for role, members in role_history.items()}

        logger.info(
            f"Computed role history: {len(result)} unique roles, "
            f"total {sum(len(members) for members in result.values())} member-role mappings"
        )

        return result

    def persist_role_history(self, role_history: Dict[str, Set[str]]) -> None:
        """
        Persist role history to storage via adapter.

        Saves the role-to-members mapping using the configured storage adapter.
        This operation should be idempotent - calling multiple times with same
        data should produce same result.

        Args:
            role_history: Dictionary from compute_role_history()
                         Maps normalized role names to sets of member names

        Raises:
            ValueError: If role_history is None or malformed
            StorageError: If storage operation fails

        Example:
            >>> role_history = {"證道": {"張三", "李四"}}
            >>> manager.persist_role_history(role_history)

        Implementation Notes:
            - Should use UPSERT semantics (update if exists, insert if not)
            - Should handle transactions for atomicity
            - Should update last_updated timestamp
        """
        if role_history is None:
            raise ValueError("role_history cannot be None")

        logger.info(f"Persisting role history: {len(role_history)} roles")

        timestamp = datetime.now()
        for role_name, member_names in role_history.items():
            self.storage_adapter.save_role_history(role_name, member_names, timestamp)

        logger.info(f"Successfully persisted {len(role_history)} roles to storage")

    def get_role_history_from_storage(self, role_name: str) -> Optional[Set[str]]:
        """
        Retrieve role history for a specific role from storage.

        Args:
            role_name: Name of the role (will be normalized before lookup)

        Returns:
            Set of member names who have performed this role,
            or None if role not found in storage

        Raises:
            StorageError: If storage retrieval fails

        Example:
            >>> members = manager.get_role_history_from_storage("證道")
            >>> members
            {"張三", "李四", "王五"}

            >>> members = manager.get_role_history_from_storage("未知角色")
            >>> members is None
            True
        """
        normalized_role = self.normalize_role_name(role_name)
        logger.debug(f"Fetching role history for '{role_name}' (normalized: '{normalized_role}')")

        role_data = self.storage_adapter.get_role_history(normalized_role)

        if role_data:
            # Return a copy to prevent external modification
            logger.debug(f"Found {len(role_data['member_names'])} members for role '{normalized_role}'")
            return role_data["member_names"].copy()
        else:
            logger.debug(f"No history found for role '{normalized_role}'")
            return None

    def get_all_role_history(self) -> Dict[str, Set[str]]:
        """
        Retrieve all role history from storage.

        Returns:
            Complete mapping of all roles to their member sets

        Raises:
            StorageError: If storage retrieval fails

        Example:
            >>> all_history = manager.get_all_role_history()
            >>> all_history
            {
                "證道": {"張三", "李四"},
                "司會": {"王五", "趙六"}
            }
        """
        logger.debug("Fetching all role history from storage")
        return self.storage_adapter.get_all_role_history()

    def get_eligible_members_for_role(
        self,
        role_name: str,
        all_members: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get members eligible for a specific role based on historical assignments.

        Returns members who have performed this role in the past (from storage).
        If no history exists for the role and all_members is provided, returns
        all_members as fallback (allows anyone to try new roles).

        Args:
            role_name: Name of the role to query (will be normalized)
            all_members: Optional list of all available members.
                        Used as fallback when no history exists for this role.
                        If None and no history exists, returns empty list.

        Returns:
            Sorted list of member names eligible for the role

        Raises:
            StorageError: If storage access fails

        Example:
            >>> # Role with history
            >>> eligible = manager.get_eligible_members_for_role("證道")
            >>> eligible
            ["張三", "李四", "王五"]

            >>> # New role with fallback
            >>> eligible = manager.get_eligible_members_for_role(
            ...     "新角色",
            ...     all_members=["張三", "李四"]
            ... )
            >>> eligible  # Returns all_members since no history
            ["張三", "李四"]

            >>> # New role without fallback
            >>> eligible = manager.get_eligible_members_for_role("新角色")
            >>> eligible
            []
        """
        logger.info(f"Getting eligible members for role: {role_name}")

        # Query storage for role history
        member_set = self.get_role_history_from_storage(role_name)

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

        This is the main orchestration method that should be called periodically
        (e.g., monthly via cron job or API endpoint) to refresh role history.

        Workflow:
        1. Compute role history from events (with optional lookback window)
        2. Persist computed history to storage via adapter
        3. Return computed history for immediate use

        Args:
            events: List of historical event dictionaries
            lookback_months: Optional limit on how far back to analyze

        Returns:
            Computed and persisted role history dictionary

        Raises:
            ValueError: If events data is malformed
            StorageError: If persistence fails

        Example:
            >>> events = fetch_all_events()  # Your data source
            >>> history = manager.recompute_role_history(
            ...     events,
            ...     lookback_months=12  # Only last 12 months
            ... )
            >>> # Role history now updated in storage
            >>> history
            {"證道": {"張三", "李四"}, "司會": {"王五"}}

        Usage Notes:
            - Should be called periodically to keep data fresh
            - Recommended frequency: monthly or after significant roster changes
            - Consider using lookback_months to focus on recent patterns
            - Can be triggered by scheduler, webhook, or manual API call
        """
        logger.info(
            f"Recomputing role history from {len(events)} events "
            f"(lookback: {lookback_months or 'all'} months)"
        )

        # Compute role history
        role_history = self.compute_role_history(events, lookback_months)

        # Persist to storage
        self.persist_role_history(role_history)

        logger.info(
            f"Role history recomputation complete: {len(role_history)} roles, "
            f"{sum(len(members) for members in role_history.values())} total assignments"
        )

        return role_history
