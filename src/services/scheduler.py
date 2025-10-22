"""
Scheduling service for running roster generation at regular intervals
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from pathlib import Path

from .json_file_writer import JsonFileWriter

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Service for scheduling and executing roster generation tasks

    Handles:
    - Periodic roster generation
    - Task scheduling and execution
    - Error handling and retries
    """

    def __init__(self, settings, json_writer: Optional[JsonFileWriter] = None):
        """
        Initialize the scheduler service

        Args:
            settings: Application settings/configuration
            json_writer: Optional JsonFileWriter instance for dependency injection.
                        If None and write_roster_json is enabled, creates one on-demand.
        """
        self.settings = settings
        self.is_running = False
        self.json_writer = json_writer
        # TODO: Initialize scheduler (e.g., APScheduler, cron)

    def start(self):
        """Start the scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting scheduler service")
        self.is_running = True

        # TODO: Schedule roster generation tasks
        # - Set up periodic execution
        # - Configure retry logic

    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            logger.warning("Scheduler is not running")
            return

        logger.info("Stopping scheduler service")
        self.is_running = False

        # TODO: Gracefully shut down scheduler

    def run_roster_generation(self, orchestrator=None):
        """
        Execute roster generation task

        This is the main task that:
        1. Fetches historical data
        2. Analyzes patterns
        3. Generates recommendations
        4. Validates generated roster
        5. Writes roster to disk (if enabled)
        6. (Future) Submits new rosters

        Args:
            orchestrator: Optional RosterOrchestrator instance.
                         If None, must be configured in settings.
        """
        logger.info("Starting roster generation task")

        try:
            if orchestrator is None:
                logger.error("No orchestrator configured - cannot run roster generation")
                return

            # Run the complete workflow using orchestrator
            result = orchestrator.generate_roster_for_upcoming_months(
                months_ahead=3,  # TODO: Make configurable
                category=None,    # TODO: Make configurable or run for each category
                historical_months=3
            )

            # Log results
            logger.info(
                f"Roster generation completed successfully: "
                f"{len(result['rosters'])} rosters generated, "
                f"validation: {'PASS' if result['validation']['is_valid'] else 'FAIL'}"
            )

            if not result['validation']['is_valid']:
                logger.warning(
                    f"Validation errors: {result['validation']['errors']}"
                )

            # Write roster to disk if enabled
            if self.settings.write_roster_json:
                self._write_roster_to_disk(result)

            # TODO: Submit to API if validation passed
            # if result['validation']['is_valid']:
            #     self._submit_rosters(result['rosters'])

        except Exception as e:
            logger.error(f"Roster generation failed: {e}")
            # TODO: Handle errors and potentially retry

    def _write_roster_to_disk(self, roster_data: dict) -> Optional[Path]:
        """
        Write roster data to disk using JsonFileWriter.

        Args:
            roster_data: Dictionary containing roster generation output

        Returns:
            Path to written file, or None if write failed
        """
        try:
            # Create writer on-demand if not provided via dependency injection
            if self.json_writer is None:
                self.json_writer = JsonFileWriter()

            # Write roster data
            file_path = self.json_writer.write(
                roster_data,
                timestamp=datetime.now()
            )

            logger.info(f"Roster data written to: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to write roster to disk: {e}")
            # Don't crash scheduler - log error and continue
            return None

    def schedule_one_time_task(self, run_at: datetime, task_name: str):
        """
        Schedule a one-time task

        Args:
            run_at: When to run the task
            task_name: Name/identifier for the task
        """
        # TODO: Implement one-time task scheduling
        logger.info(f"Scheduling task '{task_name}' at {run_at}")