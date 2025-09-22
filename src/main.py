"""
Main entry point for the Roster AI Agent
"""

import logging
from src.config.settings import Settings
from src.services.scheduler import SchedulerService

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the application"""
    # TODO: Initialize configuration
    settings = Settings()

    # TODO: Set up logging

    # TODO: Initialize services

    # TODO: Start scheduler
    scheduler = SchedulerService(settings)

    logger.info("Roster AI Agent started")

    # TODO: Run the scheduler


if __name__ == "__main__":
    main()