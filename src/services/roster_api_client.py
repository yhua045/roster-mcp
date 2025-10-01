"""
REST API client for interacting with the roster system
"""

from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import logging
import requests
from urllib.parse import urljoin

from ..exceptions import (
    APIError,
    InvalidCategoryError,
    InvalidDateRangeError,
    APIValidationError,
    EventNotFoundError
)

logger = logging.getLogger(__name__)


class RosterAPIClient:
    """
    Client for interacting with the roster REST API

    Handles:
    - Fetching historical roster data
    - Retrieving member information
    - Submitting new rosters
    - Updating existing rosters
    """

    # Valid category values (case-insensitive)
    VALID_CATEGORIES = {'chinese', 'english', 'sundayschool'}

    @staticmethod
    def parse_date(date_string: str) -> date:
        """
        Parse an ISO date string to a date object

        Args:
            date_string: Date string in ISO format (YYYY-MM-DD)

        Returns:
            Parsed date object

        Raises:
            InvalidDateRangeError: If date string is malformed
        """
        if not date_string:
            raise InvalidDateRangeError(f"Invalid date format: '{date_string}'. Expected YYYY-MM-DD")
        try:
            return datetime.fromisoformat(date_string).date()
        except (ValueError, AttributeError, TypeError) as e:
            raise InvalidDateRangeError(f"Invalid date format: '{date_string}'. Expected YYYY-MM-DD")

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the API client

        Args:
            base_url: Base URL of the roster API
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'

    def get_events(
        self,
        category: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events within a date range and optional category filter

        Args:
            category: Service category filter (case-insensitive).
                     Valid values: 'chinese', 'english', 'sundayschool'
            from_date: Start date for filtering (inclusive). Defaults to today.
            to_date: End date for filtering (inclusive). Defaults to today + 7 days.

        Returns:
            List of event dictionaries

        Raises:
            InvalidCategoryError: If category is invalid
            InvalidDateRangeError: If date range is invalid
            APIValidationError: If API returns 400 for validation errors
            APIError: For other API errors
        """
        # Validate category if provided
        if category is not None:
            category_lower = category.lower().strip()
            if category_lower not in self.VALID_CATEGORIES:
                raise InvalidCategoryError(category, self.VALID_CATEGORIES)
            category = category_lower

        # Set default dates if not provided
        if from_date is None:
            from_date = date.today()
        if to_date is None:
            to_date = date.today() + timedelta(days=7)

        # Validate date range
        if from_date > to_date:
            raise InvalidDateRangeError(
                f"Invalid date range: 'from' date ({from_date}) must be before or equal to 'to' date ({to_date})",
                from_date=from_date.isoformat(),
                to_date=to_date.isoformat()
            )

        # Build query parameters
        params = {
            'from': from_date.isoformat(),
            'to': to_date.isoformat()
        }
        if category:
            params['category'] = category

        # Make API request
        endpoint = f"{self.base_url}/api/events"
        logger.info(f"Fetching events from {endpoint} with params: {params}")

        try:
            response = self.session.get(endpoint, params=params)

            # Handle validation errors
            if response.status_code == 400:
                error_data = response.json() if response.text else {}
                raise APIValidationError(
                    message=error_data.get('message', 'Validation error'),
                    validation_errors=error_data.get('errors', {})
                )

            # Raise for other HTTP errors
            response.raise_for_status()

            # Return the JSON response
            return response.json()

        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                raise APIError(
                    message=f"API request failed: {str(e)}",
                    status_code=e.response.status_code if e.response else None,
                    response_data=e.response.json() if e.response and e.response.text else None
                )
            raise APIError(f"API request failed: {str(e)}")

    def get_event(self, event_id: int) -> Dict[str, Any]:
        """
        Retrieve a specific event by ID

        Args:
            event_id: Event identifier

        Returns:
            Event dictionary
        """
        # TODO: Implement API call
        endpoint = f"{self.base_url}/api/events/{event_id}"
        return {}

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new event

        Args:
            event_data: Event data to create

        Returns:
            Created event dictionary
        """
        # TODO: Implement API call
        endpoint = f"{self.base_url}/api/events"
        return {}

    def update_event(self, event_id: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing event

        Args:
            event_id: Event identifier
            event_data: Updated event data

        Returns:
            Updated event dictionary
        """
        # TODO: Implement API call
        endpoint = f"{self.base_url}/api/events/{event_id}"
        return {}

    def add_member_to_event(self, event_id: int, member_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add or update a member assignment for an event

        Args:
            event_id: Event identifier
            member_data: Member assignment data

        Returns:
            Updated member assignment
        """
        # TODO: Implement API call (PUT /api/events/{id})
        endpoint = f"{self.base_url}/api/events/{event_id}"
        return {}

    def update_roster_assignment(
        self,
        service_info_id: int,
        date: str,
        role: str,
        name: str,
        service_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update a roster assignment for a specific service

        This method implements the PUT /api/events endpoint to update or create
        a roster assignment for a worker in a specific role on a specific date.

        Args:
            service_info_id: ID of the service/event record
            date: Date of the event in ISO format (YYYY-MM-DD)
            role: Role the worker will be responsible for (e.g., '證道', '司會', '詩歌讚美')
            name: Name of the co-worker assigned to that role
            service_info: Optional complete ServiceInfo dictionary. If not provided,
                         will be constructed from service_info_id and date.

        Returns:
            Dictionary containing the updated roster assignment

        Raises:
            ValidationError: If input validation fails
            EventNotFoundError: If the service_info_id doesn't reference an existing event (404)
            APIValidationError: If API returns 400 for validation errors
            APIError: For other API errors

        Example:
            >>> client.update_roster_assignment(
            ...     service_info_id=601,
            ...     date="2022-10-02",
            ...     role="禱告會",
            ...     name="孟妍"
            ... )
        """
        from ..utils.validators import validate_iso_date, normalize_category, sanitize_name
        from ..exceptions import ValidationError

        # Validate inputs
        validation_errors = []

        # Validate service_info_id
        if not service_info_id or not isinstance(service_info_id, int):
            validation_errors.append("service_info_id must be a valid integer")

        # Validate date format
        if not date or not isinstance(date, str):
            validation_errors.append("date must be a non-empty string")
        elif not validate_iso_date(date):
            validation_errors.append(f"date must be in ISO format (YYYY-MM-DD), got: {date}")

        # Validate role
        if not role or not isinstance(role, str):
            validation_errors.append("role must be a non-empty string")
        else:
            role = role.strip()
            if not role:
                validation_errors.append("role cannot be empty or whitespace only")

        # Validate name
        if not name or not isinstance(name, str):
            validation_errors.append("name must be a non-empty string")
        else:
            name = sanitize_name(name)
            if not name:
                validation_errors.append("name cannot be empty or whitespace only")

        # If validation errors, raise exception
        if validation_errors:
            raise ValidationError("Request validation failed", errors=validation_errors)

        # Construct serviceInfo object
        if service_info is None:
            # Minimal serviceInfo with required fields
            service_info = {
                "id": service_info_id,
                "date": date
            }
        else:
            # Validate that provided serviceInfo matches the parameters
            if service_info.get("id") != service_info_id:
                raise ValidationError(
                    f"service_info.id ({service_info.get('id')}) must match service_info_id parameter ({service_info_id})"
                )
            if service_info.get("date") != date:
                raise ValidationError(
                    f"service_info.date ({service_info.get('date')}) must match date parameter ({date})"
                )

            # Validate category if provided
            if "category" in service_info and service_info["category"]:
                category_lower = normalize_category(service_info["category"])
                if category_lower not in self.VALID_CATEGORIES:
                    raise InvalidCategoryError(service_info["category"], self.VALID_CATEGORIES)
                # Normalize category to lowercase
                service_info["category"] = category_lower

        # Construct request payload
        payload = {
            "date": date,
            "role": role,
            "name": name,
            "serviceInfo": service_info
        }

        # Make API request
        endpoint = f"{self.base_url}/api/events"
        logger.info(f"Updating roster assignment at {endpoint}: role={role}, name={name}, date={date}")

        try:
            response = self.session.put(endpoint, json=payload)

            # Handle 404 - service not found
            if response.status_code == 404:
                error_data = response.json() if response.text else {}
                raise EventNotFoundError(
                    event_id=service_info_id,
                    message=error_data.get('message', f"Service with ID {service_info_id} not found")
                )

            # Handle validation errors
            if response.status_code == 400:
                error_data = response.json() if response.text else {}
                raise APIValidationError(
                    message=error_data.get('message', 'Validation error'),
                    validation_errors=error_data.get('errors', {})
                )

            # Raise for other HTTP errors
            response.raise_for_status()

            # Return the JSON response
            result = response.json()
            logger.info(f"Successfully updated roster assignment for {name} as {role}")
            return result

        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                # Already handled above, but catch any remaining HTTP errors
                raise APIError(
                    message=f"API request failed: {str(e)}",
                    status_code=e.response.status_code if e.response else None,
                    response_data=e.response.json() if e.response and e.response.text else None
                )
            raise APIError(f"API request failed: {str(e)}")