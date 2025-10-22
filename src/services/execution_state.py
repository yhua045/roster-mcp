"""
Execution state machine and storage layer for AI Agent runs.

This module provides a state machine to track AI Agent executions,
ensuring idempotency and preventing duplicate or overlapping automation runs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
import sqlite3
import json
import uuid
import logging
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of an execution run"""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class ExecutionState:
    """
    Represents a single AI Agent execution run.

    Attributes:
        id: Unique identifier for the execution
        generation_request_id: Optional ID correlating with AI payloads
        started_at: When the execution started (UTC)
        finished_at: When the execution finished (UTC), optional
        status: Current status of the execution
        result: Small payload describing outcome or failure message
        created_by: Actor/service that started the run
        notes: Optional notes about the execution
        version: Version number for retries and idempotency
        run_attempt: Attempt number for this execution
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generation_request_id: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    created_by: str = "ai_agent"
    notes: Optional[str] = None
    version: int = 1
    run_attempt: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "generation_request_id": self.generation_request_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status.value,
            "result": self.result,
            "created_by": self.created_by,
            "notes": self.notes,
            "version": self.version,
            "run_attempt": self.run_attempt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionState":
        """Create from dictionary representation"""
        return cls(
            id=data["id"],
            generation_request_id=data.get("generation_request_id"),
            started_at=datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else datetime.utcnow(),
            finished_at=datetime.fromisoformat(data["finished_at"])
            if data.get("finished_at")
            else None,
            status=ExecutionStatus(data["status"]),
            result=data.get("result"),
            created_by=data.get("created_by", "ai_agent"),
            notes=data.get("notes"),
            version=data.get("version", 1),
            run_attempt=data.get("run_attempt", 1),
        )


class ExecutionStore(ABC):
    """
    Abstract interface for storing and retrieving execution records.
    """

    @abstractmethod
    def create(self, record: ExecutionState) -> ExecutionState:
        """
        Create a new execution record.

        Args:
            record: ExecutionState to create

        Returns:
            The created ExecutionState with any auto-generated fields
        """
        pass

    @abstractmethod
    def update(self, record_id: str, **fields) -> Optional[ExecutionState]:
        """
        Update an existing execution record.

        Args:
            record_id: ID of the record to update
            **fields: Fields to update

        Returns:
            Updated ExecutionState or None if not found
        """
        pass

    @abstractmethod
    def list(self, start: datetime, end: datetime, limit: int = 100) -> List[ExecutionState]:
        """
        List execution records within a date range.

        Args:
            start: Start datetime (inclusive)
            end: End datetime (inclusive)
            limit: Maximum number of records to return

        Returns:
            List of ExecutionState records
        """
        pass

    @abstractmethod
    def get_latest(self) -> Optional[ExecutionState]:
        """
        Get the most recent execution record.

        Returns:
            Latest ExecutionState or None if no records exist
        """
        pass

    @abstractmethod
    def get_by_id(self, record_id: str) -> Optional[ExecutionState]:
        """
        Get a specific execution record by ID.

        Args:
            record_id: ID of the record to retrieve

        Returns:
            ExecutionState or None if not found
        """
        pass

    @abstractmethod
    def acquire_run_lock(self, key: str, timeout_seconds: int = 300) -> bool:
        """
        Try to acquire a lock to prevent parallel runs.

        Args:
            key: Lock key identifier
            timeout_seconds: How long the lock should be valid

        Returns:
            True if lock acquired, False otherwise
        """
        pass

    @abstractmethod
    def release_run_lock(self, key: str) -> bool:
        """
        Release a previously acquired lock.

        Args:
            key: Lock key identifier

        Returns:
            True if lock released, False if lock didn't exist
        """
        pass


class SqliteExecutionStore(ExecutionStore):
    """
    SQLite implementation of ExecutionStore.

    Stores execution records in a SQLite database with basic concurrency
    support using transactions and locks.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the SQLite store.

        Args:
            db_path: Path to SQLite database file. If None, uses var/execution_state.db
        """
        if db_path is None:
            # Default to var/execution_state.db
            base_dir = Path(__file__).parent.parent.parent
            var_dir = base_dir / "var"
            var_dir.mkdir(exist_ok=True)
            db_path = str(var_dir / "execution_state.db")

        self.db_path = db_path
        self._local = threading.local()
        self._init_db()
        logger.info(f"Initialized SqliteExecutionStore at {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection"""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(
                self.db_path, check_same_thread=False, timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
        return self._local.connection

    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create executions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS executions (
                id TEXT PRIMARY KEY,
                generation_request_id TEXT,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                result TEXT,
                created_by TEXT NOT NULL,
                notes TEXT,
                version INTEGER NOT NULL DEFAULT 1,
                run_attempt INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_executions_started_at
            ON executions(started_at)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_executions_status
            ON executions(status)
        """
        )

        # Create locks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS execution_locks (
                lock_key TEXT PRIMARY KEY,
                acquired_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """
        )

        conn.commit()

    def create(self, record: ExecutionState) -> ExecutionState:
        """Create a new execution record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO executions (
                    id, generation_request_id, started_at, finished_at,
                    status, result, created_by, notes, version, run_attempt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.id,
                    record.generation_request_id,
                    record.started_at.isoformat(),
                    record.finished_at.isoformat() if record.finished_at else None,
                    record.status.value,
                    json.dumps(record.result) if record.result else None,
                    record.created_by,
                    record.notes,
                    record.version,
                    record.run_attempt,
                ),
            )
            conn.commit()
            logger.info(f"Created execution record: {record.id}")
            return record
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create execution record: {e}")
            raise

    def update(self, record_id: str, **fields) -> Optional[ExecutionState]:
        """Update an existing execution record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build UPDATE query dynamically
        allowed_fields = {
            "generation_request_id",
            "finished_at",
            "status",
            "result",
            "notes",
            "version",
            "run_attempt",
        }

        update_fields = {}
        for key, value in fields.items():
            if key in allowed_fields:
                if key == "finished_at" and isinstance(value, datetime):
                    update_fields[key] = value.isoformat()
                elif key == "status" and isinstance(value, ExecutionStatus):
                    update_fields[key] = value.value
                elif key == "result" and value is not None:
                    update_fields[key] = json.dumps(value)
                else:
                    update_fields[key] = value

        if not update_fields:
            logger.warning(f"No valid fields to update for record {record_id}")
            return self.get_by_id(record_id)

        set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
        values = list(update_fields.values())
        values.append(record_id)

        try:
            cursor.execute(f"UPDATE executions SET {set_clause} WHERE id = ?", values)
            conn.commit()

            if cursor.rowcount == 0:
                logger.warning(f"No record found with id: {record_id}")
                return None

            logger.info(f"Updated execution record: {record_id}")
            return self.get_by_id(record_id)
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update execution record: {e}")
            raise

    def list(self, start: datetime, end: datetime, limit: int = 100) -> List[ExecutionState]:
        """List execution records within a date range"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM executions
            WHERE started_at >= ? AND started_at <= ?
            ORDER BY started_at DESC
            LIMIT ?
        """,
            (start.isoformat(), end.isoformat(), limit),
        )

        records = []
        for row in cursor.fetchall():
            records.append(self._row_to_execution_state(row))

        logger.info(f"Retrieved {len(records)} execution records between {start} and {end}")
        return records

    def get_latest(self) -> Optional[ExecutionState]:
        """Get the most recent execution record"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM executions
            ORDER BY started_at DESC
            LIMIT 1
        """
        )

        row = cursor.fetchone()
        if row:
            record = self._row_to_execution_state(row)
            logger.info(f"Retrieved latest execution record: {record.id}")
            return record

        logger.info("No execution records found")
        return None

    def get_by_id(self, record_id: str) -> Optional[ExecutionState]:
        """Get a specific execution record by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM executions WHERE id = ?", (record_id,))
        row = cursor.fetchone()

        if row:
            return self._row_to_execution_state(row)
        return None

    def acquire_run_lock(self, key: str, timeout_seconds: int = 300) -> bool:
        """Try to acquire a lock to prevent parallel runs"""
        conn = self._get_connection()
        cursor = conn.cursor()

        now = datetime.utcnow()
        expires_at = datetime.utcnow()
        # Add timeout_seconds to expires_at
        from datetime import timedelta

        expires_at = now + timedelta(seconds=timeout_seconds)

        try:
            # Clean up expired locks first
            cursor.execute(
                """
                DELETE FROM execution_locks
                WHERE expires_at < ?
            """,
                (now.isoformat(),),
            )

            # Try to acquire lock
            cursor.execute(
                """
                INSERT INTO execution_locks (lock_key, acquired_at, expires_at)
                VALUES (?, ?, ?)
            """,
                (key, now.isoformat(), expires_at.isoformat()),
            )

            conn.commit()
            logger.info(f"Acquired lock: {key}")
            return True
        except sqlite3.IntegrityError:
            # Lock already exists
            conn.rollback()
            logger.warning(f"Failed to acquire lock (already held): {key}")
            return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to acquire lock: {e}")
            return False

    def release_run_lock(self, key: str) -> bool:
        """Release a previously acquired lock"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM execution_locks
                WHERE lock_key = ?
            """,
                (key,),
            )
            conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Released lock: {key}")
                return True
            else:
                logger.warning(f"Lock not found: {key}")
                return False
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to release lock: {e}")
            return False

    def _row_to_execution_state(self, row: sqlite3.Row) -> ExecutionState:
        """Convert a database row to an ExecutionState object"""
        return ExecutionState(
            id=row["id"],
            generation_request_id=row["generation_request_id"],
            started_at=datetime.fromisoformat(row["started_at"]),
            finished_at=datetime.fromisoformat(row["finished_at"]) if row["finished_at"] else None,
            status=ExecutionStatus(row["status"]),
            result=json.loads(row["result"]) if row["result"] else None,
            created_by=row["created_by"],
            notes=row["notes"],
            version=row["version"],
            run_attempt=row["run_attempt"],
        )

    def close(self):
        """Close database connection"""
        if hasattr(self._local, "connection"):
            self._local.connection.close()
            delattr(self._local, "connection")


class ExecutionManager:
    """
    Helper class for managing AI Agent executions.

    Provides high-level methods for starting/finishing runs and querying history.
    """

    def __init__(self, store: Optional[ExecutionStore] = None):
        """
        Initialize the execution manager.

        Args:
            store: ExecutionStore implementation. If None, uses SqliteExecutionStore
        """
        self.store = store if store is not None else SqliteExecutionStore()

    def start_run(
        self,
        generation_request_id: Optional[str] = None,
        created_by: str = "ai_agent",
        notes: Optional[str] = None,
    ) -> ExecutionState:
        """
        Start a new execution run.

        Creates a new execution record with RUNNING status.

        Args:
            generation_request_id: Optional ID to correlate with AI payloads
            created_by: Actor/service starting the run
            notes: Optional notes about the run

        Returns:
            The created ExecutionState record
        """
        record = ExecutionState(
            generation_request_id=generation_request_id,
            status=ExecutionStatus.RUNNING,
            created_by=created_by,
            notes=notes,
        )

        created = self.store.create(record)
        logger.info(f"Started execution run: {created.id}")
        return created

    def finish_run(
        self, record_id: str, status: ExecutionStatus, result: Optional[Dict[str, Any]] = None
    ) -> Optional[ExecutionState]:
        """
        Finish an execution run.

        Updates the record with finished_at, status, and optional result.

        Args:
            record_id: ID of the execution record
            status: Final status (SUCCESS, FAILED, or CANCELLED)
            result: Optional result payload (should be small summary)

        Returns:
            Updated ExecutionState or None if record not found
        """
        updated = self.store.update(
            record_id, finished_at=datetime.utcnow(), status=status, result=result
        )

        if updated:
            logger.info(f"Finished execution run: {record_id} with status {status.value}")
        else:
            logger.warning(f"Failed to finish run - record not found: {record_id}")

        return updated

    def get_history(self, start: datetime, end: datetime, limit: int = 100) -> List[ExecutionState]:
        """
        Get execution history within a date range.

        Args:
            start: Start datetime (inclusive)
            end: End datetime (inclusive)
            limit: Maximum number of records to return

        Returns:
            List of ExecutionState records
        """
        return self.store.list(start, end, limit)

    def get_latest(self) -> Optional[ExecutionState]:
        """
        Get the most recent execution record.

        Returns:
            Latest ExecutionState or None if no records exist
        """
        return self.store.get_latest()

    def can_start_run(self) -> bool:
        """
        Check if a new run can be started.

        Simple policy check: returns False if there's a RUNNING record,
        True otherwise. This prevents overlapping runs.

        Returns:
            True if a run can be started, False otherwise
        """
        latest = self.get_latest()

        if latest is None:
            # No previous runs, safe to start
            return True

        if latest.status == ExecutionStatus.RUNNING:
            logger.warning(
                f"Cannot start run - execution {latest.id} is still RUNNING "
                f"(started at {latest.started_at})"
            )
            return False

        # Previous run is not RUNNING, safe to start new one
        return True
