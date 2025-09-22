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