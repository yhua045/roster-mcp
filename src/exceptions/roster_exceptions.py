"""
Custom exception classes for the Roster MCP system
"""


class RosterException(Exception):
    """Base exception for all roster-related errors"""
    pass


class ValidationError(RosterException):
    """Raised when validation fails"""

    def __init__(self, message: str, errors: list = None):
        super().__init__(message)
        self.errors = errors or []


class APIError(RosterException):
    """Raised when API operations fail"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class SchedulerError(RosterException):
    """Raised when scheduler operations fail"""
    pass


class ConfigurationError(RosterException):
    """Raised when configuration is invalid or missing"""
    pass


class InvalidCategoryError(ValidationError):
    """Raised when an invalid category value is provided"""

    def __init__(self, category: str, valid_categories: set):
        message = f"Invalid category: '{category}'. Must be one of {sorted(valid_categories)}"
        super().__init__(message)
        self.category = category
        self.valid_categories = valid_categories


class InvalidDateRangeError(ValidationError):
    """Raised when date range validation fails"""

    def __init__(self, message: str, from_date: str = None, to_date: str = None):
        super().__init__(message)
        self.from_date = from_date
        self.to_date = to_date


class APIValidationError(APIError):
    """Raised when API request validation fails"""

    def __init__(self, message: str, validation_errors: dict = None):
        super().__init__(message, status_code=400)
        self.validation_errors = validation_errors or {}