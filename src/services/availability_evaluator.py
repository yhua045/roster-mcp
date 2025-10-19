"""
Concrete implementation of IAvailabilityEvaluator.

This module provides the actual business logic for evaluating worker
availability for roster planning. It fetches data from configured sources,
transforms it into structured records, and caches results for performance.
"""

from typing import Dict, List, Any, Optional
from datetime import date, timedelta
from collections import defaultdict
import logging

from src.interfaces.availability_evaluator import (
    IAvailabilityEvaluator,
    IAvailabilityDataSource
)

logger = logging.getLogger(__name__)


class AvailabilityEvaluator(IAvailabilityEvaluator):
    """
    Concrete implementation of IAvailabilityEvaluator.

    Evaluates worker availability for roster planning by fetching data
    from configured sources and transforming it into structured records.

    Features:
    - Fetches availability from data source (API, DB, file)
    - Groups availability by date
    - Default period: today → today + 3 months
    - Caches results for performance
    - Assumes all workers available if no unavailability data

    Attributes:
        data_source: The data source adapter for fetching availability
        _cache: Internal cache for storing availability data
    """

    def __init__(self, data_source: Optional[IAvailabilityDataSource] = None):
        """
        Initialize the availability evaluator.

        Args:
            data_source: Optional data source adapter. If None, uses default.
                        This allows dependency injection for testing.
        """
        self.data_source = data_source or self._create_default_data_source()
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        logger.info("AvailabilityEvaluator initialized")

    def _create_default_data_source(self) -> IAvailabilityDataSource:
        """
        Create default data source (internal implementation detail).

        In production, this would create the appropriate data source
        based on configuration (API, database, etc.).

        For now, this is a placeholder that would be implemented later.
        """
        # TODO: Implement default data source creation based on config
        # For now, this will be injected during testing
        raise NotImplementedError(
            "Default data source not configured. "
            "Please provide data_source in constructor."
        )

    def _get_cache_key(
        self,
        start_date: date,
        end_date: date
    ) -> str:
        """
        Generate cache key for a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Cache key string
        """
        return f"{start_date.isoformat()}:{end_date.isoformat()}"

    def _get_default_date_range(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> tuple[date, date]:
        """
        Get default date range if not specified.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Tuple of (start_date, end_date) with defaults applied
        """
        today = date.today()

        # Default start_date to today if not provided
        if start_date is None:
            start_date = today

        # Default end_date to start_date + 3 months if not provided
        if end_date is None:
            # Approximate 3 months as 90 days
            end_date = start_date + timedelta(days=90)

        return start_date, end_date

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

        Results are cached internally for performance.

        Args:
            start_date: Start of date range. If None, defaults to today.
            end_date: End of date range. If None, defaults to today + 3 months.

        Returns:
            List of availability records, one per date in range

        Raises:
            ValueError: If date range is invalid (start_date > end_date)
        """
        # Apply defaults
        start_date, end_date = self._get_default_date_range(start_date, end_date)

        # Validate date range
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        logger.info(
            f"Evaluating availability for {start_date} to {end_date} "
            f"({(end_date - start_date).days + 1} days)"
        )

        # Check cache
        cache_key = self._get_cache_key(start_date, end_date)
        if cache_key in self._cache:
            logger.debug(f"Returning cached availability for {cache_key}")
            return self._cache[cache_key]

        # Fetch data from source
        logger.debug("Cache miss - fetching from data source")
        all_workers = self.data_source.fetch_all_workers()
        unavailability_records = self.data_source.fetch_unavailability_records(
            start_date,
            end_date
        )

        # Build unavailability lookup: date -> set of unavailable workers
        unavailability_by_date: Dict[str, set] = defaultdict(set)
        for record in unavailability_records:
            worker_name = record["worker_name"]
            unavailable_dates = record["unavailable_dates"]

            for date_str in unavailable_dates:
                unavailability_by_date[date_str].add(worker_name)

        # Generate availability records for each date in range
        availability_records = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.isoformat()

            # Get unavailable workers for this date
            unavailable_workers = list(unavailability_by_date.get(date_str, set()))
            unavailable_workers.sort()  # Sort alphabetically

            # Calculate available workers (all workers - unavailable)
            unavailable_set = set(unavailable_workers)
            available_workers = [
                worker for worker in all_workers
                if worker not in unavailable_set
            ]
            available_workers.sort()  # Sort alphabetically

            # Create record for this date
            record = {
                "date": date_str,
                "available_workers": available_workers,
                "unavailable_workers": unavailable_workers
            }
            availability_records.append(record)

            # Move to next date
            current_date += timedelta(days=1)

        # Cache the results
        self._cache[cache_key] = availability_records

        logger.info(
            f"Evaluated availability for {len(availability_records)} dates "
            f"({len(all_workers)} total workers)"
        )

        return availability_records

    def clear_cache(self) -> None:
        """
        Clear the internal availability cache.

        Call this method when you know availability data has changed.
        The next call to evaluate_availability() will fetch fresh data.
        """
        logger.info("Clearing availability cache")
        self._cache.clear()
