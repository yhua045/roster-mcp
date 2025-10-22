"""
Unit tests for SchedulerService with JsonFileWriter integration
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
from datetime import datetime

from src.services.scheduler import SchedulerService
from src.services.roster_orchestrator import RosterOrchestrator
from src.services.json_file_writer import JsonFileWriter
from src.config.settings import Settings


class TestSchedulerServiceInit(unittest.TestCase):
    """Test SchedulerService initialization"""

    def test_init_with_defaults(self):
        """Test scheduler initialization with default settings"""
        settings = Settings()
        scheduler = SchedulerService(settings)

        self.assertEqual(scheduler.settings, settings)
        self.assertFalse(scheduler.is_running)
        self.assertIsNone(scheduler.json_writer)

    def test_init_with_custom_writer(self):
        """Test scheduler initialization with custom JsonFileWriter"""
        settings = Settings()
        mock_writer = Mock(spec=JsonFileWriter)

        scheduler = SchedulerService(settings, json_writer=mock_writer)

        self.assertEqual(scheduler.json_writer, mock_writer)

    def test_init_creates_default_writer_when_write_enabled(self):
        """Test scheduler creates default writer when write_roster_json is True"""
        settings = Settings()
        settings.write_roster_json = True

        with patch('src.services.scheduler.JsonFileWriter') as MockWriter:
            mock_writer_instance = Mock()
            MockWriter.return_value = mock_writer_instance

            scheduler = SchedulerService(settings)

            # Writer should not be created in __init__, only when needed
            self.assertIsNone(scheduler.json_writer)


class TestSchedulerServiceRosterGeneration(unittest.TestCase):
    """Test roster generation with JsonFileWriter integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.settings = Settings()
        self.settings.write_roster_json = True

        self.mock_orchestrator = Mock(spec=RosterOrchestrator)
        self.mock_writer = Mock(spec=JsonFileWriter)

        # Sample orchestrator output
        self.roster_output = {
            "rosters": [
                {"date": "2025-10-26", "assignments": [{"role": "證道", "name": "張三"}]}
            ],
            "validation": {"is_valid": True, "errors": [], "warnings": []},
            "patterns": {"total_events": 12},
            "metadata": {"months_ahead": 3, "category": "chinese"}
        }

        self.mock_orchestrator.generate_roster_for_upcoming_months.return_value = (
            self.roster_output
        )

        # Mock writer returns a path
        self.mock_path = Path("/test/roster-json/roster-2025-10-22-153015.json")
        self.mock_writer.write.return_value = self.mock_path

    def test_run_roster_generation_without_writer(self):
        """Test roster generation when write_roster_json is False"""
        self.settings.write_roster_json = False
        scheduler = SchedulerService(self.settings)

        scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

        # Should generate roster but not write
        self.mock_orchestrator.generate_roster_for_upcoming_months.assert_called_once()

    def test_run_roster_generation_with_writer(self):
        """Test roster generation writes to disk when write_roster_json is True"""
        scheduler = SchedulerService(self.settings, json_writer=self.mock_writer)

        scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

        # Should generate roster
        self.mock_orchestrator.generate_roster_for_upcoming_months.assert_called_once_with(
            months_ahead=3,
            category=None,
            historical_months=3
        )

        # Should write to disk
        self.mock_writer.write.assert_called_once_with(
            self.roster_output,
            timestamp=unittest.mock.ANY
        )

    def test_run_roster_generation_logs_file_path(self):
        """Test that scheduler logs the file path after writing"""
        scheduler = SchedulerService(self.settings, json_writer=self.mock_writer)

        with patch('src.services.scheduler.logger') as mock_logger:
            scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

            # Should log the file path
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            self.assertTrue(
                any("roster-2025-10-22-153015.json" in str(call) for call in log_calls),
                "Should log the written file path"
            )

    def test_run_roster_generation_handles_writer_error(self):
        """Test that scheduler handles JsonFileWriter errors gracefully"""
        # Make writer raise an exception
        self.mock_writer.write.side_effect = IOError("Disk full")

        scheduler = SchedulerService(self.settings, json_writer=self.mock_writer)

        with patch('src.services.scheduler.logger') as mock_logger:
            # Should not crash
            scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

            # Should log the error
            mock_logger.error.assert_called()
            error_calls = [str(call) for call in mock_logger.error.call_args_list]
            self.assertTrue(
                any("Disk full" in str(call) or "write" in str(call).lower()
                    for call in error_calls),
                "Should log writer error"
            )

    def test_run_roster_generation_continues_after_writer_error(self):
        """Test that scheduler continues despite writer errors"""
        self.mock_writer.write.side_effect = IOError("Disk full")

        scheduler = SchedulerService(self.settings, json_writer=self.mock_writer)

        # Should not raise exception
        try:
            scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)
            success = True
        except Exception:
            success = False

        self.assertTrue(success, "Scheduler should not crash on writer error")

    def test_run_roster_generation_without_orchestrator(self):
        """Test that scheduler handles missing orchestrator"""
        scheduler = SchedulerService(self.settings, json_writer=self.mock_writer)

        with patch('src.services.scheduler.logger') as mock_logger:
            scheduler.run_roster_generation(orchestrator=None)

            # Should log error
            mock_logger.error.assert_called()
            # Should not call writer
            self.mock_writer.write.assert_not_called()

    def test_run_roster_generation_with_validation_failure(self):
        """Test roster generation when validation fails"""
        # Validation fails
        invalid_output = self.roster_output.copy()
        invalid_output["validation"] = {
            "is_valid": False,
            "errors": ["Missing required role: 證道"],
            "warnings": []
        }
        self.mock_orchestrator.generate_roster_for_upcoming_months.return_value = (
            invalid_output
        )

        scheduler = SchedulerService(self.settings, json_writer=self.mock_writer)

        with patch('src.services.scheduler.logger') as mock_logger:
            scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

            # Should still write to disk (for audit)
            self.mock_writer.write.assert_called_once()

            # Should log validation errors
            mock_logger.warning.assert_called()

    def test_run_roster_generation_handles_orchestrator_error(self):
        """Test that scheduler handles orchestrator errors"""
        self.mock_orchestrator.generate_roster_for_upcoming_months.side_effect = (
            ValueError("Invalid category")
        )

        scheduler = SchedulerService(self.settings, json_writer=self.mock_writer)

        with patch('src.services.scheduler.logger') as mock_logger:
            scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

            # Should log error
            mock_logger.error.assert_called()

            # Should not call writer
            self.mock_writer.write.assert_not_called()

    def test_run_roster_generation_creates_writer_on_demand(self):
        """Test that scheduler creates writer on-demand if not provided"""
        scheduler = SchedulerService(self.settings)
        self.assertIsNone(scheduler.json_writer)

        with patch('src.services.scheduler.JsonFileWriter') as MockWriter:
            mock_writer_instance = Mock()
            mock_writer_instance.write.return_value = self.mock_path
            MockWriter.return_value = mock_writer_instance

            scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

            # Should create writer
            MockWriter.assert_called_once()

            # Should write to disk
            mock_writer_instance.write.assert_called_once()


class TestSchedulerServiceIntegration(unittest.TestCase):
    """Integration tests for scheduler with real components"""

    def setUp(self):
        """Set up test fixtures"""
        self.settings = Settings()
        self.settings.write_roster_json = True

        self.mock_orchestrator = Mock(spec=RosterOrchestrator)
        self.roster_output = {
            "rosters": [
                {"date": "2025-10-26", "assignments": [{"role": "證道", "name": "張三"}]}
            ],
            "validation": {"is_valid": True, "errors": []},
            "patterns": {"total_events": 12},
            "metadata": {"months_ahead": 3}
        }
        self.mock_orchestrator.generate_roster_for_upcoming_months.return_value = (
            self.roster_output
        )

    def tearDown(self):
        """Clean up test files"""
        import shutil
        roster_dir = Path("roster-json")
        if roster_dir.exists() and roster_dir.is_dir():
            shutil.rmtree(roster_dir)

    def test_end_to_end_roster_generation_with_real_writer(self):
        """Test complete flow with real JsonFileWriter"""
        # Use real writer
        from src.services.json_file_writer import JsonFileWriter
        writer = JsonFileWriter()

        scheduler = SchedulerService(self.settings, json_writer=writer)

        # Run generation
        scheduler.run_roster_generation(orchestrator=self.mock_orchestrator)

        # Verify file was created
        roster_dir = Path("roster-json")
        self.assertTrue(roster_dir.exists())

        # Find the created file
        files = list(roster_dir.glob("roster-*.json"))
        self.assertEqual(len(files), 1, "Should create exactly one file")

        # Verify file contains correct data
        import json
        with open(files[0], 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data, self.roster_output)


class TestSchedulerServiceStartStop(unittest.TestCase):
    """Test scheduler start/stop functionality"""

    def test_start(self):
        """Test starting the scheduler"""
        settings = Settings()
        scheduler = SchedulerService(settings)

        scheduler.start()

        self.assertTrue(scheduler.is_running)

    def test_stop(self):
        """Test stopping the scheduler"""
        settings = Settings()
        scheduler = SchedulerService(settings)

        scheduler.start()
        scheduler.stop()

        self.assertFalse(scheduler.is_running)

    def test_start_when_already_running(self):
        """Test starting scheduler when already running logs warning"""
        settings = Settings()
        scheduler = SchedulerService(settings)

        scheduler.start()

        with patch('src.services.scheduler.logger') as mock_logger:
            scheduler.start()
            mock_logger.warning.assert_called()

    def test_stop_when_not_running(self):
        """Test stopping scheduler when not running logs warning"""
        settings = Settings()
        scheduler = SchedulerService(settings)

        with patch('src.services.scheduler.logger') as mock_logger:
            scheduler.stop()
            mock_logger.warning.assert_called()


if __name__ == '__main__':
    unittest.main()
