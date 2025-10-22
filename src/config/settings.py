"""
Application settings and configuration
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    """
    Application configuration settings

    Can be loaded from environment variables or configuration files
    """

    # API Configuration
    api_base_url: str = os.getenv("ROSTER_API_BASE_URL", "http://localhost:8000")
    api_key: Optional[str] = os.getenv("ROSTER_API_KEY")

    # Scheduler Configuration
    schedule_interval_hours: int = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "24"))
    schedule_enabled: bool = os.getenv("SCHEDULE_ENABLED", "true").lower() == "true"

    # AI Configuration
    ai_model: str = os.getenv("AI_MODEL", "gpt-3.5-turbo")
    ai_api_key: Optional[str] = os.getenv("AI_API_KEY")

    # Database Configuration (if needed)
    database_url: Optional[str] = os.getenv("DATABASE_URL")

    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: Optional[str] = os.getenv("LOG_FILE")

    # Feature Flags
    dry_run_mode: bool = os.getenv("DRY_RUN", "false").lower() == "true"
    auto_approve_rosters: bool = os.getenv("AUTO_APPROVE", "false").lower() == "true"

    # Roster Output Configuration
    write_roster_json: bool = os.getenv("WRITE_ROSTER_JSON", "true").lower() == "true"
    roster_output_dir: str = os.getenv("ROSTER_OUTPUT_DIR", "roster-json")

    @classmethod
    def from_yaml(cls, config_file: str):
        """
        Load settings from a YAML configuration file

        Args:
            config_file: Path to YAML configuration file

        Returns:
            Settings instance
        """
        # TODO: Implement YAML configuration loading
        return cls()

    def validate(self):
        """
        Validate settings

        Raises:
            ValueError: If required settings are missing or invalid
        """
        if not self.api_base_url:
            raise ValueError("API base URL is required")

        # Add more validation as needed