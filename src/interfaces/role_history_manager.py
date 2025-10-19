"""
Interface definitions for Role History Management.

This module defines the contracts for managing historical role assignments
and determining member eligibility for roles based on past performance.

The design uses the Adapter Pattern to allow different storage backends
(SQLite, PostgreSQL, Redis, in-memory, etc.) to be swapped without
changing the business logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Set, Optional, List, Any
from datetime import datetime


# ==================== Storage Adapter Interface ====================

class IStorageAdapter(ABC):
    """
    Interface for role history storage operations.

    This adapter abstracts the storage mechanism, allowing different
    implementations (SQLite, PostgreSQL, Redis, in-memory cache, etc.)
    to be used interchangeably.

    Implementations should handle:
    - Connection management
    - Transaction handling
    - Error handling and retries
    - Data serialization/deserialization
    """

    @abstractmethod
    def save_role_history(
        self,
        role_name: str,
        member_names: Set[str],
        last_updated: datetime
    ) -> None:
        """
        Save role history for a single role.

        Args:
            role_name: Normalized role name (lowercase, trimmed)
            member_names: Set of member names who have performed this role
            last_updated: Timestamp of when this data was computed

        Raises:
            StorageError: If save operation fails
        """
        pass

    @abstractmethod
    def get_role_history(
        self,
        role_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve role history for a single role.

        Args:
            role_name: Normalized role name to query

        Returns:
            Dictionary containing:
            {
                "role_name": str,
                "member_names": Set[str],
                "last_updated": datetime,
                "created_at": datetime
            }
            Returns None if role not found.

        Raises:
            StorageError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def get_all_role_history(self) -> Dict[str, Set[str]]:
        """
        Retrieve all role history mappings.

        Returns:
            Dictionary mapping role names to sets of member names:
            {
                "证道": {"張三", "李四"},
                "司會": {"王五"}
            }

        Raises:
            StorageError: If retrieval operation fails
        """
        pass

    @abstractmethod
    def delete_role_history(self, role_name: str) -> bool:
        """
        Delete role history for a specific role.

        Args:
            role_name: Normalized role name to delete

        Returns:
            True if role was deleted, False if role didn't exist

        Raises:
            StorageError: If delete operation fails
        """
        pass

    @abstractmethod
    def clear_all_history(self) -> None:
        """
        Clear all role history data.

        Useful for testing or complete recomputation scenarios.

        Raises:
            StorageError: If clear operation fails
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if storage backend is accessible and healthy.

        Returns:
            True if storage is accessible, False otherwise
        """
        pass


# ==================== Role History Manager Interface ====================

class IRoleHistoryManager(ABC):
    """
    Interface for managing historical role assignments and member eligibility.

    Responsibilities:
    1. Compute role history from historical event data
    2. Normalize role names for consistent lookups
    3. Persist and retrieve role-member mappings via storage adapter
    4. Determine member eligibility for specific roles

    This provides the "memory" of who has done what roles, enabling
    intelligent role assignment recommendations in roster generation.

    Design Principles:
    - Single Responsibility: Only manages role history, doesn't fetch events
    - Dependency Inversion: Depends on IStorageAdapter abstraction
    - Open/Closed: New storage backends via adapter implementation
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def persist_role_history(
        self,
        role_history: Dict[str, Set[str]]
    ) -> None:
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
        pass

    @abstractmethod
    def get_role_history_from_storage(
        self,
        role_name: str
    ) -> Optional[Set[str]]:
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
