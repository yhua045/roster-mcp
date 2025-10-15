#!/usr/bin/env python
"""
Example: Integrating Execution State Machine with AI Agent

This example demonstrates how to use the execution state machine
to track and manage AI Agent roster generation runs.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
from datetime import datetime, timedelta

from src.services.execution_state import ExecutionManager, ExecutionStatus

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def ai_agent_with_execution_tracking():
    """
    Example of how AI Agent would use the execution state machine.

    This simulates the workflow:
    1. Check if we can start a run
    2. Start tracking the execution
    3. Perform AI Agent work (simulated)
    4. Record the result
    """
    print("\n" + "=" * 70)
    print("AI Agent with Execution State Tracking")
    print("=" * 70)

    # Initialize the execution manager
    exec_manager = ExecutionManager()

    # Safety check: Can we start a new run?
    if not exec_manager.can_start_run():
        print("\n✗ Cannot start - another execution is still running")
        print("  Check the status of the running execution and wait for it to complete.")
        return

    print("\n✓ Safety check passed - ready to start execution")

    # Start tracking the execution
    execution = exec_manager.start_run(
        created_by="ai_agent_scheduler", notes="Scheduled roster generation for next 3 months"
    )

    print(f"\n📊 Execution started:")
    print(f"   ID: {execution.id}")
    print(f"   Status: {execution.status.value}")
    print(f"   Started at: {execution.started_at}")

    try:
        # Simulate AI Agent work
        print("\n🤖 Performing AI Agent tasks...")
        print("   1. Fetching historical events...")
        print("   2. Evaluating member availability...")
        print("   3. Building AI payload...")
        print("   4. Generating rosters...")
        print("   5. Validating results...")

        # Simulate some processing time
        import time

        time.sleep(0.5)

        # Simulate successful completion
        result = {
            "generated_count": 12,
            "validated_count": 12,
            "submitted_count": 12,
            "duration_seconds": 0.5,
            "date_range": {"from": "2025-10-15", "to": "2026-01-15"},
        }

        # Record successful completion
        exec_manager.finish_run(execution.id, status=ExecutionStatus.SUCCESS, result=result)

        print("\n✅ Execution completed successfully!")
        print(f"   Result: {result}")

    except Exception as e:
        # Record failure
        error_result = {"error": str(e), "error_type": type(e).__name__}

        exec_manager.finish_run(execution.id, status=ExecutionStatus.FAILED, result=error_result)

        print(f"\n❌ Execution failed: {e}")
        print(f"   Error recorded: {error_result}")
        raise


def check_execution_history():
    """
    Example of querying execution history for reporting or monitoring.
    """
    print("\n" + "=" * 70)
    print("Execution History Report")
    print("=" * 70)

    exec_manager = ExecutionManager()

    # Get executions from the last 7 days
    end = datetime.utcnow()
    start = end - timedelta(days=7)

    history = exec_manager.get_history(start, end, limit=10)

    if not history:
        print("\n📭 No executions found in the last 7 days")
        return

    print(f"\n📊 Found {len(history)} executions in the last 7 days:")
    print()

    for i, record in enumerate(history, 1):
        print(f"{i}. {record.id[:8]}... ({record.status.value})")
        print(f"   Started: {record.started_at}")
        if record.finished_at:
            duration = (record.finished_at - record.started_at).total_seconds()
            print(f"   Duration: {duration:.1f}s")
        if record.result:
            print(f"   Result: {record.result}")
        print()


def check_latest_execution():
    """
    Example of checking the latest execution for monitoring or debugging.
    """
    print("\n" + "=" * 70)
    print("Latest Execution Status")
    print("=" * 70)

    exec_manager = ExecutionManager()
    latest = exec_manager.get_latest()

    if not latest:
        print("\n📭 No previous executions found")
        return

    print(f"\n📊 Latest execution:")
    print(f"   ID: {latest.id}")
    print(f"   Status: {latest.status.value}")
    print(f"   Started: {latest.started_at}")

    if latest.finished_at:
        print(f"   Finished: {latest.finished_at}")
        duration = (latest.finished_at - latest.started_at).total_seconds()
        print(f"   Duration: {duration:.1f}s")
    else:
        print(f"   Still running...")

    if latest.result:
        print(f"   Result: {latest.result}")

    if latest.notes:
        print(f"   Notes: {latest.notes}")


def simulate_concurrent_run_prevention():
    """
    Example of how the system prevents concurrent runs.
    """
    print("\n" + "=" * 70)
    print("Concurrent Run Prevention")
    print("=" * 70)

    exec_manager = ExecutionManager()

    # Start first execution
    print("\n1️⃣  Starting first execution...")
    execution1 = exec_manager.start_run(created_by="scheduler", notes="First execution")
    print(f"   ✓ Started: {execution1.id[:8]}...")

    # Try to start second execution (should be prevented)
    print("\n2️⃣  Attempting to start second execution...")
    if exec_manager.can_start_run():
        print("   ✗ UNEXPECTED: Second execution was allowed!")
    else:
        print("   ✓ Second execution correctly prevented")
        print("   → First execution is still RUNNING")

    # Complete first execution
    print("\n3️⃣  Completing first execution...")
    exec_manager.finish_run(execution1.id, status=ExecutionStatus.SUCCESS)
    print("   ✓ First execution completed")

    # Now second execution should be allowed
    print("\n4️⃣  Attempting to start execution again...")
    if exec_manager.can_start_run():
        execution2 = exec_manager.start_run(created_by="scheduler", notes="Second execution")
        print(f"   ✓ Second execution started: {execution2.id[:8]}...")
        exec_manager.finish_run(execution2.id, status=ExecutionStatus.SUCCESS)
    else:
        print("   ✗ UNEXPECTED: Second execution was blocked!")


def main():
    """Run all integration examples"""
    print("\n" + "=" * 70)
    print("AI Agent + Execution State Integration Examples")
    print("=" * 70)

    try:
        # Example 1: AI Agent with execution tracking
        ai_agent_with_execution_tracking()

        # Example 2: Check execution history
        check_execution_history()

        # Example 3: Check latest execution
        check_latest_execution()

        # Example 4: Concurrent run prevention
        simulate_concurrent_run_prevention()

        print("\n" + "=" * 70)
        print("✅ All integration examples completed successfully!")
        print("=" * 70)
        print()

    except Exception as e:
        logger.error(f"Integration example failed: {e}", exc_info=True)
        print(f"\n❌ Error running examples: {e}")


if __name__ == "__main__":
    main()
