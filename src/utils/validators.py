"""
Validation utilities
"""

from datetime import datetime, date
from typing import Optional, List


def validate_date(date_string: str, date_format: str = "%Y-%m-%d") -> Optional[date]:
    """
    Validate and parse a date string

    Args:
        date_string: Date string to validate
        date_format: Expected date format

    Returns:
        Parsed date object or None if invalid
    """
    try:
        return datetime.strptime(date_string, date_format).date()
    except (ValueError, TypeError):
        return None


def validate_role(role: str, allowed_roles: Optional[List[str]] = None) -> bool:
    """
    Validate a role against allowed values

    Args:
        role: Role to validate
        allowed_roles: Optional list of allowed roles

    Returns:
        True if role is valid, False otherwise
    """
    if not role:
        return False

    if allowed_roles:
        return role in allowed_roles

    # If no specific roles provided, accept any non-empty string
    return True


def validate_iso_date(date_string: str) -> bool:
    """
    Validate if a string is in ISO date format (YYYY-MM-DD)

    Args:
        date_string: Date string to validate

    Returns:
        True if valid ISO date, False otherwise
    """
    return validate_date(date_string, "%Y-%m-%d") is not None


def normalize_category(category: str) -> str:
    """
    Normalize category values to lowercase

    Args:
        category: Category string to normalize

    Returns:
        Normalized category
    """
    return category.lower().strip() if category else ""


def sanitize_name(name: str) -> str:
    """
    Sanitize and normalize a person's name

    Args:
        name: Name string to sanitize

    Returns:
        Sanitized name with normalized whitespace
    """
    if not name:
        return ""

    # Normalize whitespace: strip leading/trailing and collapse internal whitespace
    import re
    normalized = re.sub(r'\s+', ' ', name.strip())
    return normalized