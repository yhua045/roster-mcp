"""
JSON File Writer for persisting roster generation outputs.

This module provides functionality to write roster data to JSON files
with proper formatting, atomic writes, and predictable file naming.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json
import tempfile
import logging

logger = logging.getLogger(__name__)


class JsonFileWriterInterface(ABC):
    """
    Abstract interface for writing roster data to JSON files.

    This interface defines the contract for persisting roster generation
    outputs to disk in JSON format with atomic write guarantees and
    structured file naming.

    Design Principles:
    - Single Responsibility: Only handles JSON file I/O
    - Dependency Injection: Accepts datetime for testability
    - Atomic Writes: Ensures no partial files on disk
    - Type Safety: Uses type hints extensively
    """

    @abstractmethod
    def write(
        self,
        roster_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Path:
        """
        Write roster data to a JSON file with timestamped filename.

        Creates the output directory if it doesn't exist, generates a
        timestamped filename, and writes the data using an atomic write
        strategy (write to temp file, then rename).

        Args:
            roster_data: Dictionary containing roster generation output.
                        Must be JSON-serializable. Typically contains:
                        - rosters: List of roster assignments
                        - validation: Validation results
                        - patterns: Historical pattern analysis
                        - metadata: Generation metadata
            timestamp: Optional datetime for filename generation.
                      If None, uses current datetime.
                      Allows deterministic testing.

        Returns:
            Path: Absolute path to the created JSON file.
                 Format: roster-json/roster-YYYY-MM-DD-HHMMSS.json
                 Example: roster-json/roster-2025-10-22-153015.json

        Raises:
            TypeError: If roster_data is not JSON-serializable
            OSError: If directory creation fails
            IOError: If file write operation fails
            ValueError: If roster_data is None or empty

        Example:
            >>> writer = JsonFileWriter()
            >>> data = {"rosters": [...], "validation": {...}}
            >>> path = writer.write(data)
            >>> path.exists()
            True
            >>> path.name
            'roster-2025-10-22-153015.json'
        """
        pass

    @abstractmethod
    def write_from_orchestrator(
        self,
        orchestrator: 'RosterOrchestrator',  # Forward reference
        timestamp: Optional[datetime] = None,
        **kwargs
    ) -> Path:
        """
        Convenience method to generate and write roster from orchestrator.

        Calls orchestrator.generate_roster_for_upcoming_months() with
        provided kwargs and writes the result to disk.

        Args:
            orchestrator: RosterOrchestrator instance to generate roster from
            timestamp: Optional datetime for filename generation.
                      If None, uses current datetime.
            **kwargs: Additional arguments passed to
                     generate_roster_for_upcoming_months()
                     (e.g., months_ahead, category, required_roles)

        Returns:
            Path: Absolute path to the created JSON file

        Raises:
            TypeError: If orchestrator is None or invalid
            ValueError: If orchestrator generation fails
            OSError: If directory creation fails
            IOError: If file write operation fails

        Example:
            >>> writer = JsonFileWriter()
            >>> orchestrator = RosterOrchestrator(data_agent, analyzer)
            >>> path = writer.write_from_orchestrator(
            ...     orchestrator,
            ...     months_ahead=3,
            ...     category='chinese'
            ... )
            >>> path.exists()
            True
        """
        pass

    @abstractmethod
    def _generate_filename(self, timestamp: datetime) -> str:
        """
        Generate timestamped filename for roster JSON file.

        Args:
            timestamp: Datetime to use for filename generation

        Returns:
            str: Filename in format 'roster-YYYY-MM-DD-HHMMSS.json'
                Zero-padded date and time components.

        Example:
            >>> dt = datetime(2025, 10, 22, 15, 30, 15)
            >>> writer._generate_filename(dt)
            'roster-2025-10-22-153015.json'
            >>> dt = datetime(2025, 1, 5, 9, 5, 3)
            >>> writer._generate_filename(dt)
            'roster-2025-01-05-090503.json'
        """
        pass

    @abstractmethod
    def _ensure_output_directory(self, directory: Path) -> None:
        """
        Ensure output directory exists, creating it if necessary.

        Creates directory with parents if it doesn't exist.
        Idempotent - safe to call multiple times.

        Args:
            directory: Path to directory to create

        Raises:
            OSError: If directory creation fails due to permissions
                    or other filesystem errors
            ValueError: If directory path is invalid

        Example:
            >>> writer._ensure_output_directory(Path('roster-json'))
            >>> Path('roster-json').exists()
            True
            >>> Path('roster-json').is_dir()
            True
        """
        pass

    @abstractmethod
    def _atomic_write_json(
        self,
        data: Dict[str, Any],
        target_path: Path
    ) -> None:
        """
        Write JSON data to file using atomic write strategy.

        Writes to a temporary file first, then renames to target path.
        This ensures no partial files exist on disk if write fails.

        The JSON is formatted with:
        - indent=2 for human readability
        - UTF-8 encoding
        - ensure_ascii=False to support Unicode characters

        Args:
            data: Dictionary to serialize to JSON
            target_path: Final destination path for the JSON file

        Raises:
            TypeError: If data is not JSON-serializable
            IOError: If write or rename operation fails
            OSError: If filesystem operation fails

        Example:
            >>> data = {"rosters": [...]}
            >>> target = Path('roster-json/roster-2025-10-22-153015.json')
            >>> writer._atomic_write_json(data, target)
            >>> target.exists()
            True
        """
        pass


class JsonFileWriter(JsonFileWriterInterface):
    """
    Concrete implementation of JsonFileWriterInterface.

    Writes roster data to JSON files in the roster-json directory
    with timestamped filenames and atomic write guarantees.
    """

    # Hardcoded output directory (as per requirements)
    OUTPUT_DIR = Path("roster-json")

    def write(
        self,
        roster_data: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Path:
        """
        Write roster data to a JSON file with timestamped filename.

        See JsonFileWriterInterface.write() for full documentation.
        """
        # Validate input
        if roster_data is None:
            raise ValueError("roster_data cannot be None")

        if not roster_data:
            raise ValueError("roster_data cannot be empty")

        # Use current time if timestamp not provided
        if timestamp is None:
            timestamp = datetime.now()

        logger.info(f"Writing roster data to file with timestamp {timestamp}")

        # Ensure output directory exists
        self._ensure_output_directory(self.OUTPUT_DIR)

        # Generate filename and full path
        filename = self._generate_filename(timestamp)
        target_path = (self.OUTPUT_DIR / filename).resolve()

        # Atomic write
        try:
            self._atomic_write_json(roster_data, target_path)
            logger.info(f"Successfully wrote roster data to {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"Failed to write roster data: {e}")
            raise

    def write_from_orchestrator(
        self,
        orchestrator: 'RosterOrchestrator',
        timestamp: Optional[datetime] = None,
        **kwargs
    ) -> Path:
        """
        Convenience method to generate and write roster from orchestrator.

        See JsonFileWriterInterface.write_from_orchestrator() for full documentation.
        """
        # Validate orchestrator
        if orchestrator is None:
            raise TypeError("orchestrator cannot be None")

        logger.info(
            f"Generating roster from orchestrator with kwargs: {kwargs}"
        )

        # Generate roster using orchestrator
        try:
            roster_data = orchestrator.generate_roster_for_upcoming_months(**kwargs)
        except Exception as e:
            logger.error(f"Orchestrator generation failed: {e}")
            raise

        # Write the generated data
        return self.write(roster_data, timestamp=timestamp)

    def _generate_filename(self, timestamp: datetime) -> str:
        """
        Generate timestamped filename for roster JSON file.

        See JsonFileWriterInterface._generate_filename() for full documentation.
        """
        # Format: roster-YYYY-MM-DD-HHMMSS.json
        # Using strftime to ensure zero-padding
        date_part = timestamp.strftime("%Y-%m-%d")
        time_part = timestamp.strftime("%H%M%S")
        filename = f"roster-{date_part}-{time_part}.json"

        logger.debug(f"Generated filename: {filename}")
        return filename

    def _ensure_output_directory(self, directory: Path) -> None:
        """
        Ensure output directory exists, creating it if necessary.

        See JsonFileWriterInterface._ensure_output_directory() for full documentation.
        """
        if not directory:
            raise ValueError("directory path cannot be empty")

        try:
            # Create directory with parents, exist_ok=True makes it idempotent
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise

    def _atomic_write_json(
        self,
        data: Dict[str, Any],
        target_path: Path
    ) -> None:
        """
        Write JSON data to file using atomic write strategy.

        See JsonFileWriterInterface._atomic_write_json() for full documentation.
        """
        # Create a temporary file in the same directory as target
        # This ensures the rename operation is atomic (same filesystem)
        temp_fd = None
        temp_path = None

        try:
            # Create temp file in same directory as target
            temp_fd, temp_name = tempfile.mkstemp(
                dir=target_path.parent,
                prefix=".roster-tmp-",
                suffix=".json"
            )
            temp_path = Path(temp_name)

            # Write JSON to temp file
            # Using file descriptor for proper handling
            with open(temp_fd, 'w', encoding='utf-8', closefd=True) as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            # Atomic rename (on same filesystem, this is atomic)
            temp_path.replace(target_path)
            logger.debug(f"Atomic write completed: {target_path}")

        except (TypeError, ValueError) as e:
            # JSON serialization errors
            logger.error(f"JSON serialization failed: {e}")
            # Clean up temp file if it exists
            if temp_path and temp_path.exists():
                temp_path.unlink()
            raise TypeError(f"Data is not JSON-serializable: {e}")

        except (IOError, OSError) as e:
            # File I/O errors
            logger.error(f"File write failed: {e}")
            # Clean up temp file if it exists
            if temp_path and temp_path.exists():
                temp_path.unlink()
            raise

        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error during write: {e}")
            # Clean up temp file if it exists
            if temp_path and temp_path.exists():
                temp_path.unlink()
            raise
