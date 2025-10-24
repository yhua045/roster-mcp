"""
Tests for AIAPIClient
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import requests

from src.services.ai_api_client import AIAPIClient
from src.exceptions import APIError


class TestAIAPIClientInit(unittest.TestCase):
    """Test AIAPIClient initialization"""

    def test_init_with_api_key(self):
        """Test initialization with API key"""
        client = AIAPIClient(
            base_url="https://api.openai.com/v1",
            api_key="test-key-123"
        )

        self.assertEqual(client.base_url, "https://api.openai.com/v1")
        self.assertEqual(client.api_key, "test-key-123")
        self.assertIn("Authorization", client.session.headers)
        self.assertEqual(client.session.headers["Authorization"], "Bearer test-key-123")

    def test_init_without_api_key(self):
        """Test initialization without API key"""
        client = AIAPIClient(base_url="https://api.openai.com/v1")

        self.assertEqual(client.base_url, "https://api.openai.com/v1")
        self.assertIsNone(client.api_key)
        self.assertNotIn("Authorization", client.session.headers)

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base URL"""
        client = AIAPIClient(base_url="https://api.openai.com/v1/")

        self.assertEqual(client.base_url, "https://api.openai.com/v1")


class TestAIAPIClientChatCompletion(unittest.TestCase):
    """Test AIAPIClient chat completion functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = AIAPIClient(
            base_url="https://api.openai.com/v1",
            api_key="test-key-123"
        )

    @patch('requests.Session.post')
    def test_chat_completion_success(self, mock_post):
        """Test successful chat completion request"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        # Make request
        result = self.client.chat_completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}]
        )

        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(call_args[1]["json"]["model"], "gpt-3.5-turbo")
        self.assertEqual(call_args[1]["json"]["messages"], [{"role": "user", "content": "Hello"}])

        # Verify response
        self.assertEqual(result["choices"][0]["message"]["content"], "Test response")

    @patch('requests.Session.post')
    def test_chat_completion_with_optional_params(self, mock_post):
        """Test chat completion with optional parameters"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": []}
        mock_post.return_value = mock_response

        self.client.chat_completion(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=100
        )

        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["json"]["temperature"], 0.7)
        self.assertEqual(call_args[1]["json"]["max_tokens"], 100)

    @patch('requests.Session.post')
    def test_chat_completion_api_error(self, mock_post):
        """Test chat completion with API error"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"error": "Bad request"}'
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        mock_post.return_value = mock_response

        with self.assertRaises(APIError) as cm:
            self.client.chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            )

        self.assertIn("API request failed", str(cm.exception))

    @patch('requests.Session.post')
    def test_chat_completion_network_error(self, mock_post):
        """Test chat completion with network error"""
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        with self.assertRaises(APIError) as cm:
            self.client.chat_completion(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}]
            )

        self.assertIn("API request failed", str(cm.exception))


if __name__ == '__main__':
    unittest.main()
