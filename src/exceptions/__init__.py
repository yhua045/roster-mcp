"""
Custom exceptions for the Roster MCP system
"""

from .roster_exceptions import (
    RosterException,
    ValidationError,
    APIError,
    SchedulerError,
    InvalidCategoryError,
    InvalidDateRangeError,
    APIValidationError,
    EventNotFoundError
)

__all__ = [
    'RosterException',
    'ValidationError',
    'APIError',
    'SchedulerError',
    'InvalidCategoryError',
    'InvalidDateRangeError',
    'APIValidationError',
    'EventNotFoundError'
]