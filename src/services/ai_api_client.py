"""
AI API client for interacting with LLM providers (OpenAI, Claude, etc.)
"""

from typing import Dict, Any, Optional, List
import logging
import requests

from ..exceptions import APIError

logger = logging.getLogger(__name__)


class AIAPIClient:
    """
    Client for interacting with AI/LLM APIs (OpenAI, Claude, etc.)

    Handles:
    - Chat completion requests
    - Authentication with API providers
    - Error handling for AI API requests
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the AI API client

        Args:
            base_url: Base URL of the AI API (e.g., https://api.openai.com/v1)
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'

    def chat_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to the AI API

        Args:
            model: Model identifier (e.g., "gpt-3.5-turbo", "gpt-4")
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Optional sampling temperature (0-2)
            max_tokens: Optional maximum tokens to generate
            **kwargs: Additional optional parameters

        Returns:
            API response dictionary

        Raises:
            APIError: If the API request fails

        Example:
            >>> client = AIAPIClient("https://api.openai.com/v1", "key")
            >>> response = client.chat_completion(
            ...     model="gpt-3.5-turbo",
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )
        """
        endpoint = f"{self.base_url}/chat/completions"

        # Build request payload
        payload = {
            "model": model,
            "messages": messages
        }

        # Add optional parameters
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        payload.update(kwargs)

        logger.info(f"Sending chat completion request to {endpoint}")
        logger.debug(f"Model: {model}, Messages: {len(messages)}")

        try:
            response = self.session.post(endpoint, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info("Chat completion request successful")
            return result

        except requests.exceptions.RequestException as e:
            if isinstance(e, requests.exceptions.HTTPError):
                error_data = e.response.json() if e.response and e.response.text else None
                raise APIError(
                    message=f"API request failed: {str(e)}",
                    status_code=e.response.status_code if e.response else None,
                    response_data=error_data
                )
            raise APIError(f"API request failed: {str(e)}")
