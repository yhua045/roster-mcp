"""
Tests for execution state machine and storage layer
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import sqlite3
import threading
import time

from src.services.execution_state import (
    ExecutionState,
    ExecutionStatus,
    ExecutionStore,
    SqliteExecutionStore,
    ExecutionManager,
)


class TestExecutionState:
    """Test ExecutionState dataclass"""

    def test_create_default_execution_state(self):
        """Test creating ExecutionState with defaults"""
        state = ExecutionState()

        assert state.id is not None
        assert isinstance(state.id, str)
        assert state.status == ExecutionStatus.PENDING
        assert state.created_by == "ai_agent"
        assert state.version == 1
        assert state.run_attempt == 1
        assert state.started_at is not None
        assert state.finished_at is None
        assert state.result is None

    def test_create_execution_state_with_params(self):
        """Test creating ExecutionState with specific parameters"""
        now = datetime.utcnow()
        result = {"status": "success", "count": 5}

        state = ExecutionState(
            id="test-123",
            generation_request_id="gen-456",
            started_at=now,
            status=ExecutionStatus.SUCCESS,
            result=result,
            created_by="test_user",
            notes="Test execution",
            version=2,
            run_attempt=3,
        )

        assert state.id == "test-123"
        assert state.generation_request_id == "gen-456"
        assert state.started_at == now
        assert state.status == ExecutionStatus.SUCCESS
        assert state.result == result
        assert state.created_by == "test_user"
        assert state.notes == "Test execution"
        assert state.version == 2
        assert state.run_attempt == 3

    def test_to_dict(self):
        """Test converting ExecutionState to dictionary"""
        now = datetime.utcnow()
        state = ExecutionState(
            id="test-123",
            generation_request_id="gen-456",
            started_at=now,
            status=ExecutionStatus.RUNNING,
            created_by="test_user",
        )

        data = state.to_dict()

        assert data["id"] == "test-123"
        assert data["generation_request_id"] == "gen-456"
        assert data["started_at"] == now.isoformat()
        assert data["status"] == "RUNNING"
        assert data["created_by"] == "test_user"

    def test_from_dict(self):
        """Test creating ExecutionState from dictionary"""
        now = datetime.utcnow()
        data = {
            "id": "test-123",
            "generation_request_id": "gen-456",
            "started_at": now.isoformat(),
            "finished_at": None,
            "status": "SUCCESS",
            "result": {"count": 10},
            "created_by": "test_user",
            "notes": "Test note",
            "version": 1,
            "run_attempt": 1,
        }

        state = ExecutionState.from_dict(data)

        assert state.id == "test-123"
        assert state.generation_request_id == "gen-456"
        assert state.status == ExecutionStatus.SUCCESS
        assert state.result == {"count": 10}
        assert state.created_by == "test_user"

    def test_execution_status_enum(self):
        """Test ExecutionStatus enum values"""
        assert ExecutionStatus.PENDING.value == "PENDING"
        assert ExecutionStatus.RUNNING.value == "RUNNING"
        assert ExecutionStatus.SUCCESS.value == "SUCCESS"
        assert ExecutionStatus.FAILED.value == "FAILED"
        assert ExecutionStatus.CANCELLED.value == "CANCELLED"


class TestSqliteExecutionStore:
    """Test SqliteExecutionStore implementation"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def store(self, temp_db):
        """Create a SqliteExecutionStore for testing"""
        store = SqliteExecutionStore(db_path=temp_db)
        yield store
        store.close()

    def test_create_record(self, store):
        """Test creating a new execution record"""
        record = ExecutionState(
            generation_request_id="gen-123",
            status=ExecutionStatus.RUNNING,
            created_by="test_agent",
        )

        created = store.create(record)

        assert created.id == record.id
        assert created.generation_request_id == "gen-123"
        assert created.status == ExecutionStatus.RUNNING
        assert created.created_by == "test_agent"

    def test_get_by_id(self, store):
        """Test retrieving record by ID"""
        record = ExecutionState(status=ExecutionStatus.PENDING)
        store.create(record)

        retrieved = store.get_by_id(record.id)

        assert retrieved is not None
        assert retrieved.id == record.id
        assert retrieved.status == ExecutionStatus.PENDING

    def test_get_by_id_not_found(self, store):
        """Test retrieving non-existent record"""
        retrieved = store.get_by_id("non-existent-id")
        assert retrieved is None

    def test_update_record(self, store):
        """Test updating an execution record"""
        record = ExecutionState(status=ExecutionStatus.RUNNING)
        store.create(record)

        finished_at = datetime.utcnow()
        result = {"status": "completed", "count": 5}

        updated = store.update(
            record.id,
            finished_at=finished_at,
            status=ExecutionStatus.SUCCESS,
            result=result,
        )

        assert updated is not None
        assert updated.status == ExecutionStatus.SUCCESS
        assert updated.result == result
        assert updated.finished_at is not None

    def test_update_nonexistent_record(self, store):
        """Test updating a record that doesn't exist"""
        updated = store.update("non-existent", status=ExecutionStatus.SUCCESS)
        assert updated is None

    def test_list_records(self, store):
        """Test listing records within date range"""
        now = datetime.utcnow()

        # Create records with different timestamps
        record1 = ExecutionState(started_at=now - timedelta(hours=2))
        record2 = ExecutionState(started_at=now - timedelta(hours=1))
        record3 = ExecutionState(started_at=now)

        store.create(record1)
        store.create(record2)
        store.create(record3)

        # List all records
        start = now - timedelta(hours=3)
        end = now + timedelta(hours=1)
        records = store.list(start, end, limit=10)

        assert len(records) == 3
        # Should be ordered by started_at DESC
        assert records[0].id == record3.id
        assert records[1].id == record2.id
        assert records[2].id == record1.id

    def test_list_records_with_limit(self, store):
        """Test listing records respects limit"""
        now = datetime.utcnow()

        for i in range(5):
            record = ExecutionState(started_at=now - timedelta(hours=i))
            store.create(record)

        start = now - timedelta(days=1)
        end = now + timedelta(hours=1)
        records = store.list(start, end, limit=3)

        assert len(records) == 3

    def test_get_latest(self, store):
        """Test getting the most recent record"""
        now = datetime.utcnow()

        record1 = ExecutionState(started_at=now - timedelta(hours=2))
        record2 = ExecutionState(started_at=now - timedelta(hours=1))
        record3 = ExecutionState(started_at=now)

        store.create(record1)
        store.create(record2)
        store.create(record3)

        latest = store.get_latest()

        assert latest is not None
        assert latest.id == record3.id

    def test_get_latest_empty_store(self, store):
        """Test getting latest from empty store"""
        latest = store.get_latest()
        assert latest is None

    def test_acquire_run_lock(self, store):
        """Test acquiring a run lock"""
        success = store.acquire_run_lock("test-lock", timeout_seconds=60)
        assert success is True

    def test_acquire_run_lock_already_held(self, store):
        """Test acquiring a lock that's already held"""
        store.acquire_run_lock("test-lock", timeout_seconds=60)

        # Try to acquire again
        success = store.acquire_run_lock("test-lock", timeout_seconds=60)
        assert success is False

    def test_release_run_lock(self, store):
        """Test releasing a run lock"""
        store.acquire_run_lock("test-lock", timeout_seconds=60)

        success = store.release_run_lock("test-lock")
        assert success is True

        # Should be able to acquire again after release
        success = store.acquire_run_lock("test-lock", timeout_seconds=60)
        assert success is True

    def test_release_nonexistent_lock(self, store):
        """Test releasing a lock that doesn't exist"""
        success = store.release_run_lock("non-existent-lock")
        assert success is False

    def test_lock_expiration(self, store):
        """Test that expired locks are cleaned up"""
        # Acquire lock with very short timeout
        store.acquire_run_lock("test-lock", timeout_seconds=1)

        # Wait for expiration
        time.sleep(2)

        # Should be able to acquire again after expiration
        success = store.acquire_run_lock("test-lock", timeout_seconds=60)
        assert success is True

    def test_record_persistence(self, temp_db):
        """Test that records persist across store instances"""
        # Create record with first store
        store1 = SqliteExecutionStore(db_path=temp_db)
        record = ExecutionState(generation_request_id="persist-test")
        store1.create(record)
        store1.close()

        # Retrieve with second store
        store2 = SqliteExecutionStore(db_path=temp_db)
        retrieved = store2.get_by_id(record.id)
        store2.close()

        assert retrieved is not None
        assert retrieved.generation_request_id == "persist-test"


class TestExecutionManager:
    """Test ExecutionManager helper class"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def manager(self, temp_db):
        """Create an ExecutionManager for testing"""
        store = SqliteExecutionStore(db_path=temp_db)
        manager = ExecutionManager(store=store)
        yield manager
        store.close()

    def test_start_run(self, manager):
        """Test starting a new run"""
        record = manager.start_run(
            generation_request_id="gen-123", created_by="test_agent", notes="Test run"
        )

        assert record is not None
        assert record.generation_request_id == "gen-123"
        assert record.status == ExecutionStatus.RUNNING
        assert record.created_by == "test_agent"
        assert record.notes == "Test run"

    def test_finish_run_success(self, manager):
        """Test finishing a run successfully"""
        record = manager.start_run()

        result = {"count": 10, "status": "completed"}
        finished = manager.finish_run(record.id, status=ExecutionStatus.SUCCESS, result=result)

        assert finished is not None
        assert finished.status == ExecutionStatus.SUCCESS
        assert finished.result == result
        assert finished.finished_at is not None

    def test_finish_run_failed(self, manager):
        """Test finishing a run with failure"""
        record = manager.start_run()

        result = {"error": "Something went wrong"}
        finished = manager.finish_run(record.id, status=ExecutionStatus.FAILED, result=result)

        assert finished is not None
        assert finished.status == ExecutionStatus.FAILED
        assert finished.result == result

    def test_finish_run_not_found(self, manager):
        """Test finishing a non-existent run"""
        finished = manager.finish_run("non-existent-id", status=ExecutionStatus.SUCCESS)

        assert finished is None

    def test_get_history(self, manager):
        """Test getting execution history"""
        now = datetime.utcnow()

        # Create multiple runs
        for i in range(3):
            manager.start_run(generation_request_id=f"gen-{i}")

        # Get history
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=1)
        history = manager.get_history(start, end, limit=10)

        assert len(history) == 3

    def test_get_latest(self, manager):
        """Test getting the latest execution"""
        record1 = manager.start_run(generation_request_id="gen-1")
        time.sleep(0.1)  # Small delay to ensure different timestamps
        record2 = manager.start_run(generation_request_id="gen-2")

        latest = manager.get_latest()

        assert latest is not None
        assert latest.id == record2.id

    def test_can_start_run_empty(self, manager):
        """Test can_start_run with no previous runs"""
        assert manager.can_start_run() is True

    def test_can_start_run_with_completed(self, manager):
        """Test can_start_run with completed previous run"""
        record = manager.start_run()
        manager.finish_run(record.id, ExecutionStatus.SUCCESS)

        assert manager.can_start_run() is True

    def test_can_start_run_with_running(self, manager):
        """Test can_start_run with running previous run"""
        manager.start_run()

        # Should not be able to start another run
        assert manager.can_start_run() is False

    def test_can_start_run_with_failed(self, manager):
        """Test can_start_run with failed previous run"""
        record = manager.start_run()
        manager.finish_run(record.id, ExecutionStatus.FAILED)

        # Should be able to start a new run
        assert manager.can_start_run() is True

    def test_default_store_creation(self):
        """Test ExecutionManager creates default store"""
        manager = ExecutionManager()
        assert manager.store is not None
        assert isinstance(manager.store, SqliteExecutionStore)


class TestConcurrency:
    """Test concurrent access to the store"""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        yield db_path

        # Cleanup
        Path(db_path).unlink(missing_ok=True)

    def test_concurrent_lock_acquisition(self, temp_db):
        """Test that only one thread can acquire a lock"""
        store1 = SqliteExecutionStore(db_path=temp_db)
        store2 = SqliteExecutionStore(db_path=temp_db)

        results = []

        def try_acquire_lock(store, results_list):
            success = store.acquire_run_lock("concurrent-test", timeout_seconds=60)
            results_list.append(success)

        thread1 = threading.Thread(target=try_acquire_lock, args=(store1, results))
        thread2 = threading.Thread(target=try_acquire_lock, args=(store2, results))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Exactly one thread should have acquired the lock
        assert sum(results) == 1
        assert True in results
        assert False in results

        store1.close()
        store2.close()

    def test_concurrent_record_creation(self, temp_db):
        """Test creating records from multiple threads"""
        store = SqliteExecutionStore(db_path=temp_db)

        def create_record(store, index):
            record = ExecutionState(generation_request_id=f"gen-{index}")
            store.create(record)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_record, args=(store, i))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All records should be created
        now = datetime.utcnow()
        records = store.list(now - timedelta(hours=1), now + timedelta(hours=1), limit=10)

        assert len(records) == 5

        store.close()
