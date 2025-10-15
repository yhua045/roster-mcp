#!/usr/bin/env python
"""
Example demonstrating the Execution State Machine usage.

This script shows how to track AI Agent executions and prevent duplicate runs.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime, timedelta
from time import sleep

from src.services.execution_state import (
    ExecutionManager,
    ExecutionStatus,
    SqliteExecutionStore,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def example_basic_usage():
    """Example 1: Basic execution tracking"""
    print("\n" + "=" * 60)
    print("Example 1: Basic Execution Tracking")
    print("=" * 60)

    manager = ExecutionManager()

    # Check if we can start a run
    if manager.can_start_run():
        print("\n✓ Can start a new run")

        # Start a new execution
        record = manager.start_run(
            generation_request_id="example-gen-123",
            created_by="demo_script",
            notes="Example execution for demonstration",
        )

        print(f"\nStarted execution:")
        print(f"  ID: {record.id}")
        print(f"  Status: {record.status.value}")
        print(f"  Started at: {record.started_at}")

        # Simulate some work
        print("\nSimulating work...")
        sleep(1)

        # Finish successfully
        manager.finish_run(
            record.id,
            status=ExecutionStatus.SUCCESS,
            result={"generated_count": 10, "validated_count": 10, "duration_seconds": 1.0},
        )

        print("\n✓ Execution finished successfully")

        # Retrieve the finished record
        finished = manager.store.get_by_id(record.id)
        print(f"\nFinal status: {finished.status.value}")
        print(f"Result: {finished.result}")
    else:
        print("\n✗ Cannot start - another run is in progress")


def example_prevent_concurrent_runs():
    """Example 2: Preventing concurrent runs"""
    print("\n" + "=" * 60)
    print("Example 2: Preventing Concurrent Runs")
    print("=" * 60)

    manager = ExecutionManager()

    # Start first execution
    record1 = manager.start_run(created_by="demo_script", notes="First execution")
    print(f"\n✓ Started first execution: {record1.id}")

    # Try to start second execution (should be prevented)
    if manager.can_start_run():
        print("\n✗ Unexpected: Second run was allowed to start")
    else:
        print("\n✓ Correctly prevented second run (first is still RUNNING)")

    # Finish the first execution
    manager.finish_run(record1.id, ExecutionStatus.SUCCESS)
    print(f"\n✓ Finished first execution")

    # Now second execution should be allowed
    if manager.can_start_run():
        record2 = manager.start_run(created_by="demo_script", notes="Second execution")
        print(f"\n✓ Started second execution: {record2.id}")
        manager.finish_run(record2.id, ExecutionStatus.SUCCESS)
    else:
        print("\n✗ Unexpected: Second run was blocked")


def example_error_handling():
    """Example 3: Handling execution failures"""
    print("\n" + "=" * 60)
    print("Example 3: Error Handling")
    print("=" * 60)

    manager = ExecutionManager()

    # Start execution
    record = manager.start_run(created_by="demo_script", notes="Execution that will fail")

    print(f"\n✓ Started execution: {record.id}")

    try:
        # Simulate work that fails
        print("\nSimulating work that fails...")
        raise ValueError("Something went wrong!")
    except Exception as e:
        # Record the failure
        manager.finish_run(
            record.id,
            status=ExecutionStatus.FAILED,
            result={"error": str(e), "error_type": type(e).__name__},
        )

        print(f"\n✓ Recorded failure: {e}")

        # Retrieve the failed record
        failed = manager.store.get_by_id(record.id)
        print(f"\nFinal status: {failed.status.value}")
        print(f"Error details: {failed.result}")


def example_query_history():
    """Example 4: Querying execution history"""
    print("\n" + "=" * 60)
    print("Example 4: Querying Execution History")
    print("=" * 60)

    manager = ExecutionManager()

    # Create several executions
    print("\nCreating sample executions...")
    for i in range(5):
        record = manager.start_run(
            generation_request_id=f"gen-{i}",
            created_by="demo_script",
            notes=f"Sample execution {i+1}",
        )

        # Finish with different statuses
        if i % 3 == 0:
            status = ExecutionStatus.SUCCESS
        elif i % 3 == 1:
            status = ExecutionStatus.FAILED
        else:
            status = ExecutionStatus.SUCCESS

        manager.finish_run(record.id, status=status)
        sleep(0.1)  # Small delay to ensure different timestamps

    # Query recent history
    end = datetime.utcnow()
    start = end - timedelta(days=1)

    history = manager.get_history(start, end, limit=10)

    print(f"\n✓ Retrieved {len(history)} executions from last 24 hours:")
    print()

    for record in history:
        print(f"ID: {record.id[:8]}...")
        print(f"  Request ID: {record.generation_request_id}")
        print(f"  Status: {record.status.value}")
        print(f"  Started: {record.started_at}")
        print(f"  Created by: {record.created_by}")
        print()


def example_get_latest():
    """Example 5: Getting the latest execution"""
    print("\n" + "=" * 60)
    print("Example 5: Getting Latest Execution")
    print("=" * 60)

    manager = ExecutionManager()

    # Get latest (might be from previous examples)
    latest = manager.get_latest()

    if latest:
        print(f"\n✓ Latest execution found:")
        print(f"  ID: {latest.id}")
        print(f"  Status: {latest.status.value}")
        print(f"  Started: {latest.started_at}")
        print(f"  Created by: {latest.created_by}")
        if latest.result:
            print(f"  Result: {latest.result}")
    else:
        print("\n✓ No previous executions found")


def example_using_locks():
    """Example 6: Using locks for critical sections"""
    print("\n" + "=" * 60)
    print("Example 6: Using Locks for Critical Sections")
    print("=" * 60)

    store = SqliteExecutionStore()

    # Try to acquire a lock
    lock_key = "critical-operation"

    print(f"\nAttempting to acquire lock: {lock_key}")
    if store.acquire_run_lock(lock_key, timeout_seconds=60):
        print("✓ Lock acquired")

        try:
            # Perform critical work
            print("\nPerforming critical work...")
            sleep(1)
            print("✓ Critical work completed")
        finally:
            # Always release the lock
            store.release_run_lock(lock_key)
            print("✓ Lock released")
    else:
        print("✗ Could not acquire lock (already held)")

    # Try to acquire again (should succeed now)
    print(f"\nAttempting to acquire lock again: {lock_key}")
    if store.acquire_run_lock(lock_key, timeout_seconds=60):
        print("✓ Lock acquired successfully")
        store.release_run_lock(lock_key)
    else:
        print("✗ Could not acquire lock")


def example_custom_db_path():
    """Example 7: Using a custom database path"""
    print("\n" + "=" * 60)
    print("Example 7: Custom Database Path")
    print("=" * 60)

    import tempfile
    import os

    # Create a temporary database file
    temp_dir = tempfile.gettempdir()
    db_path = os.path.join(temp_dir, "custom_execution_state.db")

    print(f"\nUsing custom database: {db_path}")

    # Create store with custom path
    store = SqliteExecutionStore(db_path=db_path)
    manager = ExecutionManager(store=store)

    # Use the manager
    record = manager.start_run(created_by="demo_script", notes="Using custom database path")

    print(f"✓ Created record in custom database: {record.id}")

    manager.finish_run(record.id, ExecutionStatus.SUCCESS)
    print("✓ Execution completed")

    # Clean up
    store.close()
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Cleaned up temporary database")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Execution State Machine Examples")
    print("=" * 60)

    try:
        example_basic_usage()
        example_prevent_concurrent_runs()
        example_error_handling()
        example_query_history()
        example_get_latest()
        example_using_locks()
        example_custom_db_path()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print()

    except Exception as e:
        logger.error(f"Example execution failed: {e}", exc_info=True)
        print(f"\n✗ Error running examples: {e}")


if __name__ == "__main__":
    main()
