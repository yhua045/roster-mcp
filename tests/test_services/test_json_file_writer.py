"""
Unit tests for JsonFileWriter

Following TDD approach - testing the implementation.
"""

import unittest
import tempfile
import shutil
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.services.json_file_writer import JsonFileWriterInterface, JsonFileWriter
from src.services.roster_orchestrator import RosterOrchestrator


class TestJsonFileWriterInit(unittest.TestCase):
    """Test JsonFileWriter initialization"""

    def setUp(self):
        """Set up test fixtures"""
        self.writer = JsonFileWriter()

    def test_init_creates_writer_instance(self):
        """Test writer can be instantiated"""
        self.assertIsNotNone(self.writer)
        self.assertIsInstance(self.writer, JsonFileWriterInterface)


class TestJsonFileWriterWrite(unittest.TestCase):
    """Test write() method - core functionality"""

    def setUp(self):
        """Set up test fixtures with temp directory"""
        self.test_dir = tempfile.mkdtemp()
        self.writer = JsonFileWriter()

        # Sample roster data matching orchestrator output
        self.sample_roster_data = {
            "rosters": [
                {
                    "date": "2025-10-26",
                    "assignments": [
                        {"role": "證道", "name": "張三"},
                        {"role": "司會", "name": "李四"}
                    ]
                }
            ],
            "validation": {
                "is_valid": True,
                "errors": [],
                "warnings": []
            },
            "patterns": {
                "total_events": 12,
                "member_frequency": {"張三": 3, "李四": 4}
            },
            "metadata": {
                "months_ahead": 3,
                "category": "chinese",
                "generated_at": "2025-10-22"
            }
        }

    def tearDown(self):
        """Clean up test directory"""
        if Path(self.test_dir).exists():
            shutil.rmtree(self.test_dir)

        roster_dir = Path("roster-json")
        if roster_dir.exists() and roster_dir.is_dir():
            shutil.rmtree(roster_dir)

    def test_write_creates_file_with_correct_data(self):
        """Test that write() creates a file with the correct JSON content"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)
        result_path = self.writer.write(self.sample_roster_data, timestamp=fixed_time)

        self.assertTrue(result_path.exists())
        self.assertTrue(result_path.is_file())

        with open(result_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, self.sample_roster_data)

    def test_write_creates_correct_filename_format(self):
        """Test that filename follows pattern: roster-YYYY-MM-DD-HHMMSS.json"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)
        result_path = self.writer.write(self.sample_roster_data, timestamp=fixed_time)

        expected_filename = "roster-2025-10-22-153015.json"
        self.assertEqual(result_path.name, expected_filename)

    def test_write_creates_correct_filename_with_zero_padding(self):
        """Test that filename has zero-padded date/time components"""
        fixed_time = datetime(2025, 1, 5, 9, 5, 3)
        result_path = self.writer.write(self.sample_roster_data, timestamp=fixed_time)

        expected_filename = "roster-2025-01-05-090503.json"
        self.assertEqual(result_path.name, expected_filename)

    def test_write_creates_roster_json_directory(self):
        """Test that write() creates roster-json directory if it doesn't exist"""
        roster_dir = Path("roster-json")
        if roster_dir.exists():
            shutil.rmtree(roster_dir)

        fixed_time = datetime(2025, 10, 22, 15, 30, 15)
        result_path = self.writer.write(self.sample_roster_data, timestamp=fixed_time)

        self.assertTrue(roster_dir.exists())
        self.assertTrue(roster_dir.is_dir())
        self.assertEqual(result_path.parent.name, "roster-json")

    def test_write_returns_absolute_path(self):
        """Test that write() returns absolute Path object"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)
        result_path = self.writer.write(self.sample_roster_data, timestamp=fixed_time)

        self.assertIsInstance(result_path, Path)
        self.assertTrue(result_path.is_absolute())

    def test_write_formats_json_with_indent(self):
        """Test that JSON is pretty-printed with indent=2"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)
        result_path = self.writer.write(self.sample_roster_data, timestamp=fixed_time)

        with open(result_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn('\n  "rosters":', content)
        self.assertIn('\n    {', content)

    def test_write_uses_utf8_encoding(self):
        """Test that file is written with UTF-8 encoding for Unicode support"""
        unicode_data = {
            "rosters": [{"date": "2025-10-26", "assignments": [{"role": "證道", "name": "張三"}]}]
        }

        fixed_time = datetime(2025, 10, 22, 15, 30, 15)
        result_path = self.writer.write(unicode_data, timestamp=fixed_time)

        with open(result_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["rosters"][0]["assignments"][0]["role"], "證道")
        self.assertEqual(saved_data["rosters"][0]["assignments"][0]["name"], "張三")

    def test_write_raises_value_error_for_none_data(self):
        """Test that write() raises ValueError when roster_data is None"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        with self.assertRaises(ValueError) as context:
            self.writer.write(None, timestamp=fixed_time)

        self.assertIn("roster_data", str(context.exception).lower())

    def test_write_raises_value_error_for_empty_data(self):
        """Test that write() raises ValueError when roster_data is empty dict"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        with self.assertRaises(ValueError) as context:
            self.writer.write({}, timestamp=fixed_time)

        self.assertIn("empty", str(context.exception).lower())

    def test_write_raises_type_error_for_non_serializable_data(self):
        """Test that write() raises TypeError for non-JSON-serializable data"""
        non_serializable = {
            "rosters": [{"date": datetime.now()}]
        }

        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        with self.assertRaises(TypeError):
            self.writer.write(non_serializable, timestamp=fixed_time)


class TestJsonFileWriterWriteFromOrchestrator(unittest.TestCase):
    """Test write_from_orchestrator() convenience method"""

    def setUp(self):
        """Set up test fixtures"""
        self.writer = JsonFileWriter()
        self.mock_orchestrator = Mock(spec=RosterOrchestrator)

        self.orchestrator_output = {
            "rosters": [
                {"date": "2025-10-26", "assignments": [{"role": "證道", "name": "張三"}]}
            ],
            "validation": {"is_valid": True, "errors": []},
            "patterns": {"total_events": 12},
            "metadata": {"months_ahead": 3, "category": "chinese"}
        }

        self.mock_orchestrator.generate_roster_for_upcoming_months.return_value = (
            self.orchestrator_output
        )

    def tearDown(self):
        """Clean up test directory"""
        roster_dir = Path("roster-json")
        if roster_dir.exists() and roster_dir.is_dir():
            shutil.rmtree(roster_dir)

    def test_write_from_orchestrator_calls_generate_method(self):
        """Test that write_from_orchestrator calls orchestrator.generate_roster_for_upcoming_months()"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        result_path = self.writer.write_from_orchestrator(
            self.mock_orchestrator,
            timestamp=fixed_time,
            months_ahead=3,
            category='chinese'
        )

        self.mock_orchestrator.generate_roster_for_upcoming_months.assert_called_once_with(
            months_ahead=3,
            category='chinese'
        )

    def test_write_from_orchestrator_creates_file(self):
        """Test that write_from_orchestrator creates file with orchestrator output"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        result_path = self.writer.write_from_orchestrator(
            self.mock_orchestrator,
            timestamp=fixed_time
        )

        self.assertTrue(result_path.exists())

        with open(result_path, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        self.assertEqual(saved_data, self.orchestrator_output)

    def test_write_from_orchestrator_returns_path(self):
        """Test that write_from_orchestrator returns Path object"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        result_path = self.writer.write_from_orchestrator(
            self.mock_orchestrator,
            timestamp=fixed_time
        )

        self.assertIsInstance(result_path, Path)
        self.assertTrue(result_path.is_absolute())

    def test_write_from_orchestrator_raises_type_error_for_none_orchestrator(self):
        """Test that write_from_orchestrator raises TypeError when orchestrator is None"""
        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        with self.assertRaises(TypeError) as context:
            self.writer.write_from_orchestrator(None, timestamp=fixed_time)

        self.assertIn("orchestrator", str(context.exception).lower())

    def test_write_from_orchestrator_propagates_orchestrator_exceptions(self):
        """Test that exceptions from orchestrator are propagated"""
        self.mock_orchestrator.generate_roster_for_upcoming_months.side_effect = (
            ValueError("Invalid category")
        )

        fixed_time = datetime(2025, 10, 22, 15, 30, 15)

        with self.assertRaises(ValueError) as context:
            self.writer.write_from_orchestrator(
                self.mock_orchestrator,
                timestamp=fixed_time
            )

        self.assertIn("Invalid category", str(context.exception))


class TestJsonFileWriterHelperMethods(unittest.TestCase):
    """Test private helper methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.writer = JsonFileWriter()

    def test_generate_filename_formats_correctly(self):
        """Test _generate_filename() produces correct format"""
        test_cases = [
            (datetime(2025, 10, 22, 15, 30, 15), "roster-2025-10-22-153015.json"),
            (datetime(2025, 1, 5, 9, 5, 3), "roster-2025-01-05-090503.json"),
            (datetime(2025, 12, 31, 23, 59, 59), "roster-2025-12-31-235959.json"),
        ]

        for dt, expected in test_cases:
            with self.subTest(dt=dt):
                result = self.writer._generate_filename(dt)
                self.assertEqual(result, expected)

    def test_ensure_output_directory_creates_directory(self):
        """Test _ensure_output_directory() creates directory if missing"""
        test_dir = Path("test-roster-output")

        if test_dir.exists():
            shutil.rmtree(test_dir)

        self.writer._ensure_output_directory(test_dir)

        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())

        shutil.rmtree(test_dir)

    def test_ensure_output_directory_idempotent(self):
        """Test _ensure_output_directory() is safe to call multiple times"""
        test_dir = Path("test-roster-output")

        test_dir.mkdir(exist_ok=True)

        try:
            self.writer._ensure_output_directory(test_dir)
            self.writer._ensure_output_directory(test_dir)
            success = True
        except Exception:
            success = False

        self.assertTrue(success)

        if test_dir.exists():
            shutil.rmtree(test_dir)

    def test_atomic_write_json_creates_file(self):
        """Test _atomic_write_json() creates file at target path"""
        test_data = {"test": "data", "number": 123}
        test_file = Path("test-output.json")

        # Ensure parent directory exists
        test_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            self.writer._atomic_write_json(test_data, test_file)

            self.assertTrue(test_file.exists())

            with open(test_file, 'r', encoding='utf-8') as f:
                saved = json.load(f)
            self.assertEqual(saved, test_data)
        finally:
            if test_file.exists():
                test_file.unlink()


class TestJsonFileWriterIntegration(unittest.TestCase):
    """Integration tests - closer to real-world usage"""

    def setUp(self):
        """Set up test fixtures"""
        self.writer = JsonFileWriter()

    def tearDown(self):
        """Clean up test directory"""
        roster_dir = Path("roster-json")
        if roster_dir.exists() and roster_dir.is_dir():
            shutil.rmtree(roster_dir)

    def test_multiple_writes_create_different_files(self):
        """Test that multiple writes with different timestamps create separate files"""
        data1 = {"rosters": [{"date": "2025-10-26"}]}
        data2 = {"rosters": [{"date": "2025-11-02"}]}

        time1 = datetime(2025, 10, 22, 15, 30, 15)
        time2 = datetime(2025, 10, 22, 16, 45, 30)

        path1 = self.writer.write(data1, timestamp=time1)
        path2 = self.writer.write(data2, timestamp=time2)

        self.assertTrue(path1.exists())
        self.assertTrue(path2.exists())
        self.assertNotEqual(path1, path2)

        with open(path1, 'r', encoding='utf-8') as f:
            saved1 = json.load(f)
        with open(path2, 'r', encoding='utf-8') as f:
            saved2 = json.load(f)

        self.assertEqual(saved1, data1)
        self.assertEqual(saved2, data2)

    def test_write_real_orchestrator_output_structure(self):
        """Test writing actual orchestrator output structure"""
        realistic_data = {
            "rosters": [
                {
                    "date": "2025-10-26",
                    "assignments": [
                        {"role": "證道", "name": "張三", "member_id": "M001"},
                        {"role": "司會", "name": "李四", "member_id": "M002"},
                        {"role": "詩歌讚美", "name": "王五", "member_id": "M003"}
                    ]
                }
            ],
            "validation": {
                "is_valid": True,
                "errors": [],
                "warnings": ["Member M001 has served 3 times recently"],
                "statistics": {
                    "total_assignments": 3,
                    "unique_members": 3
                }
            },
            "patterns": {
                "total_events": 12,
                "member_frequency": {"張三": 3, "李四": 4, "王五": 2},
                "role_distribution": {"證道": 12, "司會": 12}
            },
            "metadata": {
                "months_ahead": 3,
                "category": "chinese",
                "historical_months": 3,
                "generated_at": "2025-10-22"
            }
        }

        fixed_time = datetime(2025, 10, 22, 15, 30, 15)
        result_path = self.writer.write(realistic_data, timestamp=fixed_time)

        self.assertTrue(result_path.exists())

        with open(result_path, 'r', encoding='utf-8') as f:
            saved = json.load(f)

        self.assertEqual(saved, realistic_data)
        self.assertEqual(len(saved["rosters"]), 1)
        self.assertEqual(len(saved["rosters"][0]["assignments"]), 3)


if __name__ == '__main__':
    unittest.main()
