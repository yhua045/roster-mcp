"""
Interface definitions for Availability Evaluation.

This module defines the contracts for evaluating worker availability
for roster planning. The evaluator fetches availability data from
configured sources and returns structured availability records.

The design encapsulates data source details - callers don't need to
know where availability data comes from (API, database, file, etc.).
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Optional, Any
from datetime import date


# ==================== Output Data Structure ====================

class AvailabilityRecord(Protocol):
    """
    Output data structure for availability on a specific date.

    Contains all workers grouped by availability status for a single date.
    """

    date: str
    """Date in ISO format (YYYY-MM-DD)"""

    available_workers: List[str]
    """List of worker names who are available on this date"""

    unavailable_workers: List[str]
    """List of worker names who are unavailable on this date"""


# ==================== Data Source Adapter Interface (Internal) ====================

class IAvailabilityDataSource(ABC):
    """
    Internal interface for availability data sources.

    This is an INTERNAL abstraction - not exposed to callers.
    Concrete implementations of IAvailabilityEvaluator will use this
    internally to fetch data from different sources.

    Supports:
    - External API (current)
    - Database (future)
    - File/Configuration (future)
    """

    @abstractmethod
    def fetch_unavailability_records(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw unavailability data from the source.

        Returns data in the format:
        [
            {
                "worker_name": "張三",
                "unavailable_dates": ["2024-12-25", "2024-12-26"]
            },
            {
                "worker_name": "李四",
                "unavailable_dates": ["2024-12-31"]
            }
        ]

        Args:
            start_date: Start of the date range to query
            end_date: End of the date range to query

        Returns:
            List of worker unavailability records

        Raises:
            DataSourceError: If data fetching fails
            ValueError: If date range is invalid
        """
        pass

    @abstractmethod
    def fetch_all_workers(self) -> List[str]:
        """
        Fetch list of all workers in the system.

        Returns:
            List of all worker names

        Raises:
            DataSourceError: If data fetching fails
        """
        pass


# ==================== Main Interface ====================

class IAvailabilityEvaluator(ABC):
    """
    Interface for evaluating worker availability for roster planning.

    Responsibilities:
    1. Fetch availability data from configured sources (encapsulated internally)
    2. Transform raw data into structured availability records
    3. Group availability by date for roster generation
    4. Cache results for performance

    This evaluator does NOT:
    - Expose data source details to callers (internal implementation)
    - Filter workers (that's IRosterAnalyzer's job)
    - Make roster assignments (that's IRosterAnalyzer's job)

    Design Principles:
    - Single Responsibility: Only evaluates and returns availability
    - Encapsulation: Data source is internal implementation detail
    - Open/Closed: Can swap data sources without changing interface

    Usage:
        # Caller doesn't know about data sources
        evaluator = AvailabilityEvaluator()
        availability = evaluator.evaluate_availability()
    """

    @abstractmethod
    def evaluate_availability(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate and return worker availability for a date range.

        Returns availability grouped by date, showing which workers
        are available/unavailable for each date in the range.

        If no unavailability data exists for a date, assumes all workers
        are available.

        Results are cached internally for performance since availability
        data doesn't change frequently.

        Args:
            start_date: Start of date range. If None, defaults to today.
            end_date: End of date range. If None, defaults to today + 3 months.

        Returns:
            List of availability records, one per date in range:
            [
                {
                    "date": "2024-12-25",
                    "available_workers": ["王五", "趙六"],
                    "unavailable_workers": ["張三", "李四"]
                },
                {
                    "date": "2024-12-26",
                    "available_workers": ["張三", "王五", "趙六"],
                    "unavailable_workers": ["李四"]
                },
                {
                    "date": "2024-12-27",
                    "available_workers": ["張三", "李四", "王五", "趙六"],
                    "unavailable_workers": []  # All available
                }
            ]

        Raises:
            DataSourceError: If unable to fetch availability data
            ValueError: If date range is invalid (start_date > end_date)

        Example:
            >>> evaluator = AvailabilityEvaluator()
            >>>
            >>> # Get availability for next 3 months (default)
            >>> availability = evaluator.evaluate_availability()
            >>> len(availability)
            90  # Approximately 3 months of dates
            >>>
            >>> # Get availability for specific range
            >>> from datetime import date
            >>> start = date(2024, 12, 1)
            >>> end = date(2024, 12, 31)
            >>> availability = evaluator.evaluate_availability(start, end)
            >>> len(availability)
            31  # December only

        Implementation Notes:
            - Default period: today to today + 3 months (90 days)
            - Each date in range gets an entry, even if all workers available
            - Workers not in unavailability list are considered available
            - Results are cached internally (data doesn't change often)
            - Data source (API/DB/File) is determined internally by implementation
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """
        Clear the internal availability cache.

        Call this method when you know availability data has changed
        (e.g., after workers update their availability in the system).

        The next call to evaluate_availability() will fetch fresh data.

        Example:
            >>> evaluator = AvailabilityEvaluator()
            >>>
            >>> # First call - fetches from data source
            >>> availability = evaluator.evaluate_availability()
            >>>
            >>> # Second call - returns cached data (fast)
            >>> availability = evaluator.evaluate_availability()
            >>>
            >>> # Worker updates their availability externally
            >>> evaluator.clear_cache()
            >>>
            >>> # Next call fetches fresh data
            >>> availability = evaluator.evaluate_availability()
        """
        pass
