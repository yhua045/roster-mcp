"""
Unit tests for IAvailabilityEvaluator interface.

These tests define the contract that any implementation of IAvailabilityEvaluator
must satisfy. They use mocks to isolate the interface from data source dependencies.

Test-Driven Development approach:
1. Write tests based on interface contract (THIS FILE - tests will FAIL)
2. Implement concrete class to pass tests (src/services/availability_evaluator.py)
3. Refactor as needed while keeping tests green
"""

import pytest
from datetime import date, timedelta
from typing import Dict, List, Any, Optional

from src.interfaces.availability_evaluator import (
    IAvailabilityEvaluator,
    IAvailabilityDataSource
)


# ==================== Mock Data Source for Testing ====================

class MockAvailabilityDataSource(IAvailabilityDataSource):
    """
    In-memory mock implementation of IAvailabilityDataSource for testing.

    This is ONLY for testing purposes - not the real implementation.
    """

    def __init__(self):
        # Simulate data storage
        self.unavailability_data: List[Dict[str, Any]] = []
        self.all_workers: List[str] = []
        self.is_healthy = True

    def set_unavailability_data(self, data: List[Dict[str, Any]]) -> None:
        """Helper method to set up test data."""
        self.unavailability_data = data

    def set_all_workers(self, workers: List[str]) -> None:
        """Helper method to set up worker list."""
        self.all_workers = workers

    def fetch_unavailability_records(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Fetch unavailability records (filtered by date range)."""
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        # Filter records to only include dates within range
        filtered_records = []
        for record in self.unavailability_data:
            worker_name = record["worker_name"]
            unavailable_dates = record["unavailable_dates"]

            # Filter dates within range
            filtered_dates = [
                d for d in unavailable_dates
                if start_date <= date.fromisoformat(d) <= end_date
            ]

            if filtered_dates:
                filtered_records.append({
                    "worker_name": worker_name,
                    "unavailable_dates": filtered_dates
                })

        return filtered_records

    def fetch_all_workers(self) -> List[str]:
        """Fetch all workers."""
        return self.all_workers.copy()


# ==================== Test Fixtures ====================

@pytest.fixture
def mock_data_source():
    """Provides a fresh MockAvailabilityDataSource for each test."""
    return MockAvailabilityDataSource()


@pytest.fixture
def availability_evaluator(mock_data_source):
    """
    Provides an AvailabilityEvaluator instance.

    THIS WILL FAIL until you implement AvailabilityEvaluator in:
    src/services/availability_evaluator.py
    """
    from src.services.availability_evaluator import AvailabilityEvaluator
    return AvailabilityEvaluator(data_source=mock_data_source)


@pytest.fixture
def sample_workers():
    """Sample worker list."""
    return ["張三", "李四", "王五", "趙六"]


@pytest.fixture
def sample_unavailability_data():
    """Sample unavailability data."""
    return [
        {
            "worker_name": "張三",
            "unavailable_dates": ["2024-12-25", "2024-12-26"]
        },
        {
            "worker_name": "李四",
            "unavailable_dates": ["2024-12-25", "2024-12-31"]
        }
    ]


# ==================== Test: evaluate_availability ====================

class TestEvaluateAvailability:
    """Test suite for evaluate_availability method."""

    def test_returns_list_of_availability_records(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should return a list with one record per date."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        start = date(2024, 12, 25)
        end = date(2024, 12, 27)

        availability = availability_evaluator.evaluate_availability(start, end)

        # Should have 3 days of data
        assert len(availability) == 3
        assert isinstance(availability, list)
        assert all(isinstance(record, dict) for record in availability)

    def test_each_record_has_required_fields(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should include date, available_workers, unavailable_workers."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        assert "date" in record
        assert "available_workers" in record
        assert "unavailable_workers" in record
        assert record["date"] == "2024-12-25"

    def test_correctly_identifies_unavailable_workers(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should correctly mark workers as unavailable."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        assert "張三" in record["unavailable_workers"]
        assert "李四" in record["unavailable_workers"]

    def test_correctly_identifies_available_workers(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should correctly mark workers as available."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        assert "王五" in record["available_workers"]
        assert "趙六" in record["available_workers"]

    def test_all_workers_available_when_no_unavailability(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should mark all workers as available if no unavailability data."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([])  # No unavailability

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        assert len(record["available_workers"]) == 4
        assert len(record["unavailable_workers"]) == 0
        assert set(record["available_workers"]) == set(sample_workers)

    def test_handles_date_range_correctly(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should return one record per date in range."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        start = date(2024, 12, 25)
        end = date(2024, 12, 31)  # 7 days

        availability = availability_evaluator.evaluate_availability(start, end)

        assert len(availability) == 7
        # Verify dates are sequential
        for i, record in enumerate(availability):
            expected_date = (start + timedelta(days=i)).isoformat()
            assert record["date"] == expected_date

    def test_uses_default_date_range_when_not_specified(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should default to today + 3 months when dates not specified."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([])

        availability = availability_evaluator.evaluate_availability()

        # Should be approximately 90-92 days (3 months)
        assert 88 <= len(availability) <= 92

        # First date should be today
        today = date.today()
        assert availability[0]["date"] == today.isoformat()

        # Last date should be around 3 months from now
        last_date = date.fromisoformat(availability[-1]["date"])
        days_diff = (last_date - today).days
        assert 88 <= days_diff <= 92

    def test_uses_default_start_date_when_only_end_specified(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should use today as start_date if only end_date provided."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([])

        today = date.today()
        end = today + timedelta(days=7)

        availability = availability_evaluator.evaluate_availability(end_date=end)

        assert len(availability) == 8  # Including today
        assert availability[0]["date"] == today.isoformat()

    def test_uses_default_end_date_when_only_start_specified(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should use today + 3 months as end_date if only start_date provided."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([])

        start = date.today()

        availability = availability_evaluator.evaluate_availability(start_date=start)

        # Should be approximately 90-92 days
        assert 88 <= len(availability) <= 92

    def test_raises_error_for_invalid_date_range(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should raise ValueError if start_date > end_date."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([])

        start = date(2024, 12, 31)
        end = date(2024, 12, 25)  # End before start

        with pytest.raises(ValueError, match="start_date must be <= end_date"):
            availability_evaluator.evaluate_availability(start, end)

    def test_returns_sorted_worker_lists(
        self,
        availability_evaluator,
        mock_data_source
    ):
        """Should return alphabetically sorted worker lists."""
        # Set workers in random order
        mock_data_source.set_all_workers(["趙六", "張三", "王五", "李四"])
        mock_data_source.set_unavailability_data([
            {"worker_name": "張三", "unavailable_dates": ["2024-12-25"]}
        ])

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        # Check if sorted
        assert record["available_workers"] == sorted(record["available_workers"])
        assert record["unavailable_workers"] == sorted(record["unavailable_workers"])


# ==================== Test: Caching Behavior ====================

class TestCachingBehavior:
    """Test suite for caching functionality."""

    def test_caches_results_on_second_call(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should return cached results on second call."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        start = date(2024, 12, 25)
        end = date(2024, 12, 27)

        # First call - fetches from data source
        availability1 = availability_evaluator.evaluate_availability(start, end)

        # Modify data source (shouldn't affect cached results)
        mock_data_source.set_unavailability_data([])

        # Second call - should return cached data (with unavailability)
        availability2 = availability_evaluator.evaluate_availability(start, end)

        # Results should be the same (cached)
        assert availability1 == availability2
        # Should still have unavailable workers from cache
        assert len(availability2[0]["unavailable_workers"]) > 0

    def test_clear_cache_refreshes_data(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should fetch fresh data after clear_cache()."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        start = date(2024, 12, 25)
        end = date(2024, 12, 27)

        # First call - fetches from data source
        availability1 = availability_evaluator.evaluate_availability(start, end)
        assert len(availability1[0]["unavailable_workers"]) == 2  # 張三, 李四

        # Modify data source
        mock_data_source.set_unavailability_data([])

        # Clear cache
        availability_evaluator.clear_cache()

        # Next call should fetch fresh data (no unavailability)
        availability2 = availability_evaluator.evaluate_availability(start, end)
        assert len(availability2[0]["unavailable_workers"]) == 0

    def test_different_date_ranges_cached_separately(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers,
        sample_unavailability_data
    ):
        """Should cache different date ranges separately."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data(sample_unavailability_data)

        # Query range 1
        start1 = date(2024, 12, 25)
        end1 = date(2024, 12, 27)
        availability1 = availability_evaluator.evaluate_availability(start1, end1)

        # Query range 2
        start2 = date(2024, 12, 28)
        end2 = date(2024, 12, 30)
        availability2 = availability_evaluator.evaluate_availability(start2, end2)

        # Should have different data
        assert availability1[0]["date"] == "2024-12-25"
        assert availability2[0]["date"] == "2024-12-28"


# ==================== Test: Edge Cases ====================

class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_handles_empty_worker_list(
        self,
        availability_evaluator,
        mock_data_source
    ):
        """Should handle case where no workers exist."""
        mock_data_source.set_all_workers([])
        mock_data_source.set_unavailability_data([])

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        assert len(record["available_workers"]) == 0
        assert len(record["unavailable_workers"]) == 0

    def test_handles_single_day_range(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should handle single day range (start == end)."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([])

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        assert len(availability) == 1
        assert availability[0]["date"] == "2024-12-25"

    def test_handles_worker_unavailable_entire_range(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should handle worker unavailable for entire range."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([
            {
                "worker_name": "張三",
                "unavailable_dates": ["2024-12-25", "2024-12-26", "2024-12-27"]
            }
        ])

        start = date(2024, 12, 25)
        end = date(2024, 12, 27)

        availability = availability_evaluator.evaluate_availability(start, end)

        # 張三 should be unavailable on all dates
        for record in availability:
            assert "張三" in record["unavailable_workers"]
            assert "張三" not in record["available_workers"]

    def test_handles_all_workers_unavailable_on_date(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should handle case where all workers unavailable on a date."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([
            {"worker_name": "張三", "unavailable_dates": ["2024-12-25"]},
            {"worker_name": "李四", "unavailable_dates": ["2024-12-25"]},
            {"worker_name": "王五", "unavailable_dates": ["2024-12-25"]},
            {"worker_name": "趙六", "unavailable_dates": ["2024-12-25"]}
        ])

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        assert len(record["available_workers"]) == 0
        assert len(record["unavailable_workers"]) == 4

    def test_handles_worker_not_in_unavailability_data(
        self,
        availability_evaluator,
        mock_data_source
    ):
        """Should assume worker is available if not in unavailability data."""
        mock_data_source.set_all_workers(["張三", "李四", "王五"])
        # Only 張三 has unavailability data
        mock_data_source.set_unavailability_data([
            {"worker_name": "張三", "unavailable_dates": ["2024-12-25"]}
        ])

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        record = availability[0]
        # 李四 and 王五 should be available (not in unavailability data)
        assert "李四" in record["available_workers"]
        assert "王五" in record["available_workers"]
        assert "張三" in record["unavailable_workers"]


# ==================== Test: Data Source Integration ====================

class TestDataSourceIntegration:
    """Test suite for data source adapter interactions."""

    def test_calls_fetch_all_workers(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should call data source to fetch all workers."""
        mock_data_source.set_all_workers(sample_workers)
        mock_data_source.set_unavailability_data([])

        start = date(2024, 12, 25)
        end = date(2024, 12, 25)

        availability = availability_evaluator.evaluate_availability(start, end)

        # Should have all workers in available list
        assert set(availability[0]["available_workers"]) == set(sample_workers)

    def test_calls_fetch_unavailability_records_with_date_range(
        self,
        availability_evaluator,
        mock_data_source,
        sample_workers
    ):
        """Should pass date range to data source."""
        mock_data_source.set_all_workers(sample_workers)
        # Set unavailability outside the query range
        mock_data_source.set_unavailability_data([
            {"worker_name": "張三", "unavailable_dates": ["2024-11-01"]},  # Outside range
            {"worker_name": "李四", "unavailable_dates": ["2024-12-25"]}   # Inside range
        ])

        start = date(2024, 12, 25)
        end = date(2024, 12, 27)

        availability = availability_evaluator.evaluate_availability(start, end)

        # Only 李四 should be unavailable (張三's date is outside range)
        assert "李四" in availability[0]["unavailable_workers"]
        assert "張三" not in availability[0]["unavailable_workers"]
