"""
Unit tests for IRoleHistoryManager interface.

These tests define the contract that any implementation of IRoleHistoryManager
must satisfy. They use mocks to isolate the interface from storage dependencies.

Test-Driven Development approach:
1. Write tests based on interface contract (THIS FILE - tests will FAIL)
2. Implement concrete class to pass tests (src/services/role_history_manager.py)
3. Refactor as needed while keeping tests green
"""

import pytest
from datetime import datetime, timedelta, date
from typing import Dict, Set, List, Any, Optional

from src.interfaces.role_history_manager import IRoleHistoryManager, IStorageAdapter


# ==================== Mock Storage Adapter for Testing ====================

class MockStorageAdapter(IStorageAdapter):
    """
    In-memory mock implementation of IStorageAdapter for testing.

    This is ONLY for testing purposes - not the real implementation.
    """

    def __init__(self):
        self.storage: Dict[str, Dict[str, Any]] = {}
        self.is_healthy = True

    def save_role_history(
        self,
        role_name: str,
        member_names: Set[str],
        last_updated: datetime
    ) -> None:
        self.storage[role_name] = {
            "role_name": role_name,
            "member_names": member_names.copy(),
            "last_updated": last_updated,
            "created_at": self.storage.get(role_name, {}).get("created_at", datetime.now())
        }

    def get_role_history(self, role_name: str) -> Optional[Dict[str, Any]]:
        return self.storage.get(role_name)

    def get_all_role_history(self) -> Dict[str, Set[str]]:
        return {
            role: data["member_names"]
            for role, data in self.storage.items()
        }

    def delete_role_history(self, role_name: str) -> bool:
        if role_name in self.storage:
            del self.storage[role_name]
            return True
        return False

    def clear_all_history(self) -> None:
        self.storage.clear()

    def health_check(self) -> bool:
        return self.is_healthy


# ==================== Test Fixtures ====================

@pytest.fixture
def mock_storage_adapter():
    """Provides a fresh MockStorageAdapter for each test."""
    return MockStorageAdapter()


@pytest.fixture
def role_history_manager(mock_storage_adapter):
    """
    Provides a RoleHistoryManager instance.

    THIS WILL FAIL until you implement RoleHistoryManager in:
    src/services/role_history_manager.py
    """
    # Import the implementation (this will fail initially)
    from src.services.role_history_manager import RoleHistoryManager
    return RoleHistoryManager(mock_storage_adapter)


@pytest.fixture
def sample_events():
    """Provides sample event data for testing."""
    return [
        {
            "date": "2024-01-15",
            "members": [
                {"name": "張三", "role": "證道"},
                {"name": "李四", "role": "司會"}
            ]
        },
        {
            "date": "2024-01-22",
            "members": [
                {"name": "張三", "role": "證道"},
                {"name": "王五", "role": "司會"}
            ]
        },
        {
            "date": "2024-02-05",
            "members": [
                {"name": "李四", "role": "證道"},
                {"name": "趙六", "role": "招待"}
            ]
        }
    ]


@pytest.fixture
def sample_events_with_variations():
    """Provides event data with edge cases."""
    return [
        {
            "date": "2024-01-15",
            "members": [
                {"name": "張三", "role": "  證道  "},  # Whitespace
                {"name": "李四", "role": "PREACHER"}   # Uppercase
            ]
        },
        {
            "date": "2024-01-22",
            "members": [
                {"name": "王五", "role": "證道"},
                {"name": "", "role": "司會"},          # Empty name
                {"name": "趙六", "role": ""}           # Empty role
            ]
        },
        {
            "date": "invalid-date",
            "members": [
                {"name": "孫七", "role": "招待"}
            ]
        }
    ]


# ==================== Test: normalize_role_name ====================

class TestNormalizeRoleName:
    """Test suite for normalize_role_name method."""

    def test_normalizes_to_lowercase(self, role_history_manager):
        """Should convert role name to lowercase."""
        assert role_history_manager.normalize_role_name("PREACHER") == "preacher"
        assert role_history_manager.normalize_role_name("Preacher") == "preacher"

    def test_trims_whitespace(self, role_history_manager):
        """Should remove leading and trailing whitespace."""
        assert role_history_manager.normalize_role_name("  證道  ") == "證道"
        assert role_history_manager.normalize_role_name("\t司會\n") == "司會"

    def test_handles_chinese_characters(self, role_history_manager):
        """Should preserve Chinese characters while normalizing."""
        assert role_history_manager.normalize_role_name("證道") == "證道"
        assert role_history_manager.normalize_role_name("  司會  ") == "司會"

    def test_returns_empty_for_none(self, role_history_manager):
        """Should return empty string for None input."""
        assert role_history_manager.normalize_role_name(None) == ""

    def test_returns_empty_for_empty_string(self, role_history_manager):
        """Should return empty string for empty input."""
        assert role_history_manager.normalize_role_name("") == ""
        assert role_history_manager.normalize_role_name("   ") == ""


# ==================== Test: compute_role_history ====================

class TestComputeRoleHistory:
    """Test suite for compute_role_history method."""

    def test_computes_basic_role_history(self, role_history_manager, sample_events):
        """Should correctly compute role-to-members mapping."""
        history = role_history_manager.compute_role_history(sample_events)

        assert "證道" in history
        assert "司會" in history
        assert "招待" in history

        assert "張三" in history["證道"]
        assert "李四" in history["證道"]
        assert len(history["證道"]) == 2

    def test_uses_sets_for_unique_members(self, role_history_manager):
        """Should deduplicate members using sets."""
        events = [
            {
                "date": "2024-01-15",
                "members": [{"name": "張三", "role": "證道"}]
            },
            {
                "date": "2024-01-22",
                "members": [{"name": "張三", "role": "證道"}]  # Duplicate
            }
        ]

        history = role_history_manager.compute_role_history(events)

        assert len(history["證道"]) == 1
        assert "張三" in history["證道"]

    def test_normalizes_role_names(self, role_history_manager):
        """Should normalize role names during computation."""
        events = [
            {
                "date": "2024-01-15",
                "members": [
                    {"name": "張三", "role": "  證道  "},
                    {"name": "李四", "role": "PREACHER"}
                ]
            }
        ]

        history = role_history_manager.compute_role_history(events)

        assert "證道" in history
        assert "preacher" in history

    def test_skips_members_with_missing_role(self, role_history_manager):
        """Should skip members without role."""
        events = [
            {
                "date": "2024-01-15",
                "members": [
                    {"name": "張三", "role": "證道"},
                    {"name": "李四", "role": ""},      # Empty role
                    {"name": "王五"}                   # Missing role key
                ]
            }
        ]

        history = role_history_manager.compute_role_history(events)

        assert "張三" in history["證道"]
        assert len(history["證道"]) == 1

    def test_skips_members_with_missing_name(self, role_history_manager):
        """Should skip members without name."""
        events = [
            {
                "date": "2024-01-15",
                "members": [
                    {"name": "張三", "role": "證道"},
                    {"name": "", "role": "司會"},      # Empty name
                    {"role": "招待"}                   # Missing name key
                ]
            }
        ]

        history = role_history_manager.compute_role_history(events)

        assert "證道" in history
        assert "司會" not in history or len(history["司會"]) == 0

    def test_handles_empty_events_list(self, role_history_manager):
        """Should return empty dict for empty events list."""
        history = role_history_manager.compute_role_history([])

        assert history == {}

    def test_raises_error_for_none_events(self, role_history_manager):
        """Should raise ValueError if events is None."""
        with pytest.raises(ValueError, match="events cannot be None"):
            role_history_manager.compute_role_history(None)

    def test_filters_by_lookback_months(self, role_history_manager):
        """Should only include events within lookback window."""
        today = date.today()
        old_date = (today - timedelta(days=400)).isoformat()
        recent_date = (today - timedelta(days=30)).isoformat()

        events = [
            {
                "date": old_date,
                "members": [{"name": "張三", "role": "證道"}]
            },
            {
                "date": recent_date,
                "members": [{"name": "李四", "role": "證道"}]
            }
        ]

        # With 12-month lookback, should only get recent event
        history = role_history_manager.compute_role_history(events, lookback_months=12)

        assert "李四" in history["證道"]
        assert "張三" not in history["證道"]

    def test_handles_invalid_dates_gracefully(self, role_history_manager):
        """Should skip events with invalid date format."""
        events = [
            {
                "date": "invalid-date",
                "members": [{"name": "張三", "role": "證道"}]
            },
            {
                "date": "2024-01-15",
                "members": [{"name": "李四", "role": "證道"}]
            }
        ]

        # Should process valid date event even if some dates are invalid
        history = role_history_manager.compute_role_history(events)

        # Without lookback, invalid dates are still processed
        assert "證道" in history


# ==================== Test: persist_role_history ====================

class TestPersistRoleHistory:
    """Test suite for persist_role_history method."""

    def test_persists_to_storage_adapter(self, role_history_manager, mock_storage_adapter):
        """Should call storage adapter to save role history."""
        role_history = {
            "證道": {"張三", "李四"},
            "司會": {"王五"}
        }

        role_history_manager.persist_role_history(role_history)

        # Verify data was saved
        saved_data = mock_storage_adapter.get_all_role_history()
        assert saved_data["證道"] == {"張三", "李四"}
        assert saved_data["司會"] == {"王五"}

    def test_handles_empty_role_history(self, role_history_manager):
        """Should handle empty role history gracefully."""
        role_history_manager.persist_role_history({})

        # Should not raise error

    def test_raises_error_for_none_role_history(self, role_history_manager):
        """Should raise ValueError if role_history is None."""
        with pytest.raises(ValueError, match="role_history cannot be None"):
            role_history_manager.persist_role_history(None)

    def test_updates_timestamp(self, role_history_manager, mock_storage_adapter):
        """Should update timestamp when persisting."""
        role_history = {"證道": {"張三"}}

        before = datetime.now()
        role_history_manager.persist_role_history(role_history)
        after = datetime.now()

        saved = mock_storage_adapter.get_role_history("證道")
        assert before <= saved["last_updated"] <= after


# ==================== Test: get_role_history_from_storage ====================

class TestGetRoleHistoryFromStorage:
    """Test suite for get_role_history_from_storage method."""

    def test_retrieves_existing_role(self, role_history_manager, mock_storage_adapter):
        """Should retrieve role history for existing role."""
        # Setup storage
        mock_storage_adapter.save_role_history(
            "證道",
            {"張三", "李四"},
            datetime.now()
        )

        members = role_history_manager.get_role_history_from_storage("證道")

        assert members == {"張三", "李四"}

    def test_normalizes_role_name_before_lookup(self, role_history_manager, mock_storage_adapter):
        """Should normalize role name before querying storage."""
        # Save with normalized name
        mock_storage_adapter.save_role_history(
            "證道",
            {"張三"},
            datetime.now()
        )

        # Query with whitespace
        members = role_history_manager.get_role_history_from_storage("  證道  ")

        assert members == {"張三"}

    def test_returns_none_for_nonexistent_role(self, role_history_manager):
        """Should return None if role not found."""
        members = role_history_manager.get_role_history_from_storage("不存在的角色")

        assert members is None


# ==================== Test: get_all_role_history ====================

class TestGetAllRoleHistory:
    """Test suite for get_all_role_history method."""

    def test_retrieves_all_roles(self, role_history_manager, mock_storage_adapter):
        """Should retrieve all role history from storage."""
        # Setup storage
        mock_storage_adapter.save_role_history("證道", {"張三"}, datetime.now())
        mock_storage_adapter.save_role_history("司會", {"李四"}, datetime.now())

        all_history = role_history_manager.get_all_role_history()

        assert len(all_history) == 2
        assert all_history["證道"] == {"張三"}
        assert all_history["司會"] == {"李四"}

    def test_returns_empty_dict_when_no_history(self, role_history_manager):
        """Should return empty dict if no history in storage."""
        all_history = role_history_manager.get_all_role_history()

        assert all_history == {}


# ==================== Test: get_eligible_members_for_role ====================

class TestGetEligibleMembersForRole:
    """Test suite for get_eligible_members_for_role method."""

    def test_returns_members_with_history(self, role_history_manager, mock_storage_adapter):
        """Should return members who have performed the role."""
        mock_storage_adapter.save_role_history(
            "證道",
            {"張三", "李四", "王五"},
            datetime.now()
        )

        eligible = role_history_manager.get_eligible_members_for_role("證道")

        assert eligible == ["張三", "李四", "王五"]  # Sorted

    def test_returns_sorted_list(self, role_history_manager, mock_storage_adapter):
        """Should return alphabetically sorted list."""
        mock_storage_adapter.save_role_history(
            "證道",
            {"王五", "張三", "李四"},  # Unsorted
            datetime.now()
        )

        eligible = role_history_manager.get_eligible_members_for_role("證道")

        assert eligible == sorted(eligible)

    def test_returns_fallback_for_new_role(self, role_history_manager):
        """Should return all_members as fallback if no history exists."""
        all_members = ["張三", "李四", "王五"]

        eligible = role_history_manager.get_eligible_members_for_role(
            "新角色",
            all_members=all_members
        )

        assert eligible == ["張三", "李四", "王五"]

    def test_returns_empty_list_for_new_role_without_fallback(self, role_history_manager):
        """Should return empty list if no history and no fallback."""
        eligible = role_history_manager.get_eligible_members_for_role("新角色")

        assert eligible == []

    def test_normalizes_role_name(self, role_history_manager, mock_storage_adapter):
        """Should normalize role name before lookup."""
        mock_storage_adapter.save_role_history(
            "證道",
            {"張三"},
            datetime.now()
        )

        eligible = role_history_manager.get_eligible_members_for_role("  證道  ")

        assert "張三" in eligible


# ==================== Test: recompute_role_history ====================

class TestRecomputeRoleHistory:
    """Test suite for recompute_role_history method."""

    def test_computes_and_persists_history(
        self,
        role_history_manager,
        mock_storage_adapter,
        sample_events
    ):
        """Should compute role history and persist to storage."""
        history = role_history_manager.recompute_role_history(sample_events)

        # Should return computed history
        assert "證道" in history
        assert "張三" in history["證道"]

        # Should persist to storage
        saved = mock_storage_adapter.get_all_role_history()
        assert saved["證道"] == history["證道"]

    def test_handles_lookback_months(self, role_history_manager, mock_storage_adapter):
        """Should respect lookback_months parameter."""
        today = date.today()
        old_date = (today - timedelta(days=400)).isoformat()
        recent_date = (today - timedelta(days=30)).isoformat()

        events = [
            {
                "date": old_date,
                "members": [{"name": "張三", "role": "證道"}]
            },
            {
                "date": recent_date,
                "members": [{"name": "李四", "role": "證道"}]
            }
        ]

        history = role_history_manager.recompute_role_history(
            events,
            lookback_months=12
        )

        # Should only include recent event
        assert "李四" in history["證道"]
        assert "張三" not in history["證道"]

        # Should persist filtered results
        saved = mock_storage_adapter.get_role_history("證道")
        assert "李四" in saved["member_names"]

    def test_returns_computed_history(self, role_history_manager, sample_events):
        """Should return the computed role history."""
        history = role_history_manager.recompute_role_history(sample_events)

        assert isinstance(history, dict)
        assert all(isinstance(v, set) for v in history.values())


# ==================== Test: Edge Cases ====================

class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_handles_events_without_members_key(self, role_history_manager):
        """Should handle events missing 'members' key."""
        events = [
            {"date": "2024-01-15"},  # No members key
            {
                "date": "2024-01-22",
                "members": [{"name": "張三", "role": "證道"}]
            }
        ]

        history = role_history_manager.compute_role_history(events)

        assert "證道" in history
        assert "張三" in history["證道"]

    def test_handles_multiple_roles_same_member(self, role_history_manager):
        """Should track member across different roles."""
        events = [
            {
                "date": "2024-01-15",
                "members": [{"name": "張三", "role": "證道"}]
            },
            {
                "date": "2024-01-22",
                "members": [{"name": "張三", "role": "司會"}]
            }
        ]

        history = role_history_manager.compute_role_history(events)

        assert "張三" in history["證道"]
        assert "張三" in history["司會"]

    def test_preserves_set_immutability(self, role_history_manager, mock_storage_adapter):
        """Should not allow external modification of stored sets."""
        original = {"張三", "李四"}
        mock_storage_adapter.save_role_history("證道", original, datetime.now())

        retrieved = role_history_manager.get_role_history_from_storage("證道")
        retrieved.add("王五")  # Attempt to modify

        # Original in storage should be unchanged
        stored = mock_storage_adapter.get_role_history("證道")
        assert "王五" not in stored["member_names"]
