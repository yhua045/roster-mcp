"""
Unit tests for RosterAPIClient
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta
import requests
import json

from src.services.roster_api_client import RosterAPIClient
from src.exceptions import (
    InvalidCategoryError,
    InvalidDateRangeError,
    APIValidationError,
    APIError
)


class TestRosterAPIClient(unittest.TestCase):
    """Test RosterAPIClient class"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "https://api.example.com"
        self.api_key = "test-api-key"
        self.client = RosterAPIClient(self.base_url, self.api_key)

    def test_init(self):
        """Test client initialization"""
        client = RosterAPIClient(self.base_url, self.api_key)
        self.assertEqual(client.base_url, self.base_url)
        self.assertEqual(client.api_key, self.api_key)
        self.assertIsInstance(client.session, requests.Session)
        self.assertEqual(
            client.session.headers.get('Authorization'),
            f'Bearer {self.api_key}'
        )

    def test_init_without_api_key(self):
        """Test client initialization without API key"""
        client = RosterAPIClient(self.base_url)
        self.assertEqual(client.base_url, self.base_url)
        self.assertIsNone(client.api_key)
        self.assertNotIn('Authorization', client.session.headers)

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base URL"""
        client = RosterAPIClient("https://api.example.com/", self.api_key)
        self.assertEqual(client.base_url, "https://api.example.com")


class TestGetEvents(unittest.TestCase):
    """Test get_events method"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "https://api.example.com"
        self.client = RosterAPIClient(self.base_url)
        self.mock_response = Mock()

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_default_parameters(self, mock_get):
        """Test get_events with default parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "date": "2024-01-14"}]
        mock_get.return_value = mock_response

        result = self.client.get_events()

        # Check that defaults are used
        today = date.today()
        expected_params = {
            'from': today.isoformat(),
            'to': (today + timedelta(days=7)).isoformat()
        }
        mock_get.assert_called_once_with(
            f"{self.base_url}/api/events",
            params=expected_params
        )
        self.assertEqual(result, [{"id": 1, "date": "2024-01-14"}])

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_with_valid_category(self, mock_get):
        """Test get_events with valid category values"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        for category in ['chinese', 'English', 'SundaySchool', 'CHINESE']:
            with self.subTest(category=category):
                result = self.client.get_events(category=category)

                # Check that category is normalized to lowercase
                expected_params = {
                    'from': date.today().isoformat(),
                    'to': (date.today() + timedelta(days=7)).isoformat(),
                    'category': category.lower()
                }
                mock_get.assert_called_with(
                    f"{self.base_url}/api/events",
                    params=expected_params
                )

    def test_get_events_with_invalid_category(self):
        """Test get_events with invalid category raises error"""
        with self.assertRaises(InvalidCategoryError) as context:
            self.client.get_events(category="invalid")

        error = context.exception
        self.assertIn("invalid", str(error))
        self.assertEqual(error.category, "invalid")
        self.assertEqual(error.valid_categories, {'chinese', 'english', 'sundayschool'})

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_with_date_range(self, mock_get):
        """Test get_events with custom date range"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        from_date = date(2024, 1, 1)
        to_date = date(2024, 1, 31)

        result = self.client.get_events(from_date=from_date, to_date=to_date)

        expected_params = {
            'from': '2024-01-01',
            'to': '2024-01-31'
        }
        mock_get.assert_called_once_with(
            f"{self.base_url}/api/events",
            params=expected_params
        )

    def test_get_events_invalid_date_range(self):
        """Test get_events with from_date > to_date raises error"""
        from_date = date(2024, 2, 1)
        to_date = date(2024, 1, 1)

        with self.assertRaises(InvalidDateRangeError) as context:
            self.client.get_events(from_date=from_date, to_date=to_date)

        error = context.exception
        self.assertIn("must be before or equal to", str(error))
        self.assertEqual(error.from_date, '2024-02-01')
        self.assertEqual(error.to_date, '2024-01-01')

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_with_all_parameters(self, mock_get):
        """Test get_events with all parameters specified"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1}]
        mock_get.return_value = mock_response

        from_date = date(2024, 1, 1)
        to_date = date(2024, 1, 7)

        result = self.client.get_events(
            category="English",
            from_date=from_date,
            to_date=to_date
        )

        expected_params = {
            'from': '2024-01-01',
            'to': '2024-01-07',
            'category': 'english'
        }
        mock_get.assert_called_once_with(
            f"{self.base_url}/api/events",
            params=expected_params
        )

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_handles_400_error(self, mock_get):
        """Test get_events handles 400 validation errors"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"message": "Invalid request", "errors": {"category": "Invalid value"}}'
        mock_response.json.return_value = {
            "message": "Invalid request",
            "errors": {"category": "Invalid value"}
        }
        mock_get.return_value = mock_response

        with self.assertRaises(APIValidationError) as context:
            self.client.get_events()

        error = context.exception
        self.assertEqual(error.status_code, 400)
        self.assertEqual(error.validation_errors, {"category": "Invalid value"})
        self.assertIn("Invalid request", str(error))

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_handles_500_error(self, mock_get):
        """Test get_events handles 500 server errors"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = '{"error": "Internal server error"}'
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_get.return_value = mock_response

        with self.assertRaises(APIError) as context:
            self.client.get_events()

        error = context.exception
        self.assertEqual(error.status_code, 500)

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_handles_network_error(self, mock_get):
        """Test get_events handles network errors"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")

        with self.assertRaises(APIError) as context:
            self.client.get_events()

        error = context.exception
        self.assertIn("Network error", str(error))

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_empty_result(self, mock_get):
        """Test get_events with empty result"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = self.client.get_events()
        self.assertEqual(result, [])

    @patch('src.services.roster_api_client.requests.Session.get')
    def test_get_events_whitespace_in_category(self, mock_get):
        """Test get_events handles whitespace in category parameter"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        result = self.client.get_events(category="  Chinese  ")

        # Check that category is trimmed and normalized
        expected_params = {
            'from': date.today().isoformat(),
            'to': (date.today() + timedelta(days=7)).isoformat(),
            'category': 'chinese'
        }
        mock_get.assert_called_once_with(
            f"{self.base_url}/api/events",
            params=expected_params
        )


class TestDateParsing(unittest.TestCase):
    """Test date parsing functionality"""

    def test_parse_valid_date(self):
        """Test parsing valid ISO date string"""
        result = RosterAPIClient.parse_date("2024-01-14")
        self.assertEqual(result, date(2024, 1, 14))

    def test_parse_invalid_date_format(self):
        """Test parsing invalid date format raises error"""
        invalid_formats = [
            "2024/01/14",
            "14-01-2024",
            "2024-1-14",
            "2024-13-01",
            "2024-01-32",
            "not-a-date",
            "",
            None
        ]

        for invalid_date in invalid_formats:
            with self.subTest(date_string=invalid_date):
                with self.assertRaises(InvalidDateRangeError) as context:
                    RosterAPIClient.parse_date(invalid_date)
                self.assertIn("Invalid date format", str(context.exception))


if __name__ == "__main__":
    unittest.main()