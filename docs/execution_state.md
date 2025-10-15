# Execution State Machine

## Overview

The execution state machine provides a state machine and storage layer to track AI Agent executions. This ensures idempotency and prevents duplicate or overlapping automation runs.

## Purpose

- Record each AI Agent run with metadata
- Enable safety checks before proceeding with new runs
- Provide simple APIs for querying execution history
- Prevent concurrent/overlapping automation runs using locks

## Module Location

- **Implementation**: `src/services/execution_state.py`
- **Tests**: `tests/test_services/test_execution_state.py`

## Key Components

### 1. ExecutionState (Dataclass)

Represents a single AI Agent execution run.

**Schema:**
```python
@dataclass
class ExecutionState:
    id: str                              # Unique UUID
    generation_request_id: Optional[str] # Correlates with AI payloads
    started_at: datetime                 # When execution started (UTC)
    finished_at: Optional[datetime]      # When execution finished (UTC)
    status: ExecutionStatus              # PENDING, RUNNING, SUCCESS, FAILED, CANCELLED
    result: Optional[Dict[str, Any]]     # Small payload with outcome/failure
    created_by: str                      # Actor/service that started the run
    notes: Optional[str]                 # Optional notes
    version: int                         # Version for retries/idempotency
    run_attempt: int                     # Attempt number
```

**Status Values:**
- `PENDING`: Execution created but not yet started
- `RUNNING`: Execution is currently in progress
- `SUCCESS`: Execution completed successfully
- `FAILED`: Execution failed with errors
- `CANCELLED`: Execution was cancelled

### 2. ExecutionStore (Abstract Interface)

Abstract base class defining the storage interface.

**Methods:**
- `create(record)`: Create a new execution record
- `update(record_id, **fields)`: Update an existing record
- `list(start, end, limit)`: List records within a date range
- `get_latest()`: Get the most recent execution
- `get_by_id(record_id)`: Get a specific record by ID
- `acquire_run_lock(key, timeout_seconds)`: Acquire a lock to prevent parallel runs
- `release_run_lock(key)`: Release a previously acquired lock

### 3. SqliteExecutionStore (Concrete Implementation)

SQLite implementation of ExecutionStore.

**Features:**
- Persists to `var/execution_state.db` by default
- Thread-safe with connection pooling
- Transaction support for consistency
- Lock expiration mechanism
- Automatic database initialization

**Database Schema:**
```sql
CREATE TABLE executions (
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
);

CREATE TABLE execution_locks (
    lock_key TEXT PRIMARY KEY,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);
```

### 4. ExecutionManager (Helper Class)

High-level API for managing executions.

**Methods:**
- `start_run(generation_request_id, created_by, notes)`: Start a new run
- `finish_run(record_id, status, result)`: Finish a run
- `get_history(start, end, limit)`: Get execution history
- `get_latest()`: Get the latest execution
- `can_start_run()`: Check if a new run can be started (safety check)

## Usage Examples

### Basic Usage

```python
from src.services.execution_state import ExecutionManager, ExecutionStatus

# Initialize the manager (uses default SQLite store)
manager = ExecutionManager()

# Check if we can start a run
if manager.can_start_run():
    # Start a new execution
    record = manager.start_run(
        generation_request_id="gen-123",
        created_by="ai_agent",
        notes="Generating rosters for next 3 months"
    )
    
    try:
        # Perform your AI Agent work here
        # ...
        
        # Finish successfully
        manager.finish_run(
            record.id,
            status=ExecutionStatus.SUCCESS,
            result={"generated_count": 10, "validated_count": 10}
        )
    except Exception as e:
        # Finish with failure
        manager.finish_run(
            record.id,
            status=ExecutionStatus.FAILED,
            result={"error": str(e)}
        )
else:
    print("Cannot start run - another execution is still running")
```

### Query Execution History

```python
from datetime import datetime, timedelta
from src.services.execution_state import ExecutionManager

manager = ExecutionManager()

# Get executions from the last 7 days
end = datetime.utcnow()
start = end - timedelta(days=7)

history = manager.get_history(start, end, limit=100)

for record in history:
    print(f"ID: {record.id}")
    print(f"Status: {record.status.value}")
    print(f"Started: {record.started_at}")
    print(f"Result: {record.result}")
    print("---")
```

### Get Latest Execution

```python
from src.services.execution_state import ExecutionManager

manager = ExecutionManager()

latest = manager.get_latest()

if latest:
    print(f"Latest run: {latest.id}")
    print(f"Status: {latest.status.value}")
    print(f"Started at: {latest.started_at}")
else:
    print("No previous executions found")
```

### Using Custom Store

```python
from src.services.execution_state import (
    ExecutionManager,
    SqliteExecutionStore
)

# Use a custom database path
store = SqliteExecutionStore(db_path="/custom/path/state.db")
manager = ExecutionManager(store=store)

# Use the manager as normal
record = manager.start_run()
```

### Working with Locks

```python
from src.services.execution_state import SqliteExecutionStore

store = SqliteExecutionStore()

# Try to acquire a lock
if store.acquire_run_lock("ai-agent-run", timeout_seconds=300):
    try:
        # Perform work that should not run in parallel
        # ...
        pass
    finally:
        # Always release the lock
        store.release_run_lock("ai-agent-run")
else:
    print("Could not acquire lock - another process is running")
```

## Integration with AI Agent

The execution state machine is designed to be used by the AI Agent before and after roster generation:

```python
from src.services.ai_agent import AIAgent
from src.services.execution_state import ExecutionManager, ExecutionStatus

# Initialize components
agent = AIAgent(api_client)
exec_manager = ExecutionManager()

# Safety check before starting
if not exec_manager.can_start_run():
    print("Skipping - another run is in progress")
    return

# Start tracking the run
record = exec_manager.start_run(
    created_by="scheduler",
    notes="Scheduled roster generation"
)

try:
    # Fetch historical data
    events = agent.fetch_last_three_months()
    
    # Extract members and evaluate availability
    members = []
    for event in events:
        members.extend(event.get('members', []))
    availability = agent.evaluate_availability_placeholder(members)
    
    # Build AI payload
    payload = agent.build_ai_payload(
        historical_events=events,
        availability=availability,
        months_ahead=3
    )
    
    # The generation_request_id from the payload can be linked
    exec_manager.store.update(
        record.id,
        generation_request_id=payload['metadata']['generation_request_id']
    )
    
    # Send to AI for roster generation
    # ... AI processing ...
    
    # Mark as successful
    exec_manager.finish_run(
        record.id,
        status=ExecutionStatus.SUCCESS,
        result={
            "generated_count": 15,
            "request_id": payload['metadata']['generation_request_id']
        }
    )
    
except Exception as e:
    # Mark as failed
    exec_manager.finish_run(
        record.id,
        status=ExecutionStatus.FAILED,
        result={"error": str(e), "error_type": type(e).__name__}
    )
    raise
```

## Storage Location

By default, the SQLite database is stored at:
- `var/execution_state.db` (relative to project root)

The `var/` directory is automatically created if it doesn't exist and is excluded from git via `.gitignore`.

## Best Practices

### 1. Keep Result Payloads Small

The `result` field should contain summary metadata, not full generated rosters:

✅ **Good:**
```python
result = {
    "generated_count": 10,
    "request_id": "gen-123",
    "duration_seconds": 45.2
}
```

❌ **Bad:**
```python
result = {
    "full_rosters": [...],  # Don't store large payloads
    "all_events": [...]      # Keep it small!
}
```

### 2. Always Use can_start_run()

Before starting a new execution, check if it's safe:

```python
if manager.can_start_run():
    record = manager.start_run()
    # ... do work ...
else:
    # Log warning or wait
    print("Cannot start - run already in progress")
```

### 3. Always Finish Runs

Make sure to call `finish_run()` in both success and error cases:

```python
record = manager.start_run()
try:
    # ... do work ...
    manager.finish_run(record.id, ExecutionStatus.SUCCESS)
except Exception as e:
    manager.finish_run(record.id, ExecutionStatus.FAILED, 
                      result={"error": str(e)})
    raise
```

### 4. Use Locks for Critical Sections

For operations that absolutely cannot run in parallel:

```python
if store.acquire_run_lock("critical-operation", timeout_seconds=600):
    try:
        # Critical work here
        pass
    finally:
        store.release_run_lock("critical-operation")
```

## Future Enhancements

The execution state system is designed to be extended with:

1. **Production Database**: Switch from SQLite to PostgreSQL for production
2. **Advisory Locks**: Use database-level advisory locks for better concurrency
3. **Leader Election**: Implement distributed leader election for multi-instance deployments
4. **Safety Heuristics**: Extend `can_start_run()` with more sophisticated safety checks
5. **Metrics and Monitoring**: Add metrics export for execution history and performance
6. **Retry Logic**: Automatic retry with exponential backoff for failed executions

## API Reference

### ExecutionStatus

```python
class ExecutionStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
```

### ExecutionManager

#### `__init__(store: Optional[ExecutionStore] = None)`
Initialize the execution manager with an optional custom store.

#### `start_run(generation_request_id: Optional[str] = None, created_by: str = "ai_agent", notes: Optional[str] = None) -> ExecutionState`
Start a new execution run and return the created record.

#### `finish_run(record_id: str, status: ExecutionStatus, result: Optional[Dict[str, Any]] = None) -> Optional[ExecutionState]`
Finish an execution run with the given status and optional result.

#### `get_history(start: datetime, end: datetime, limit: int = 100) -> List[ExecutionState]`
Get execution history within the specified date range.

#### `get_latest() -> Optional[ExecutionState]`
Get the most recent execution record.

#### `can_start_run() -> bool`
Check if a new run can be started (returns False if there's a RUNNING execution).

### SqliteExecutionStore

#### `__init__(db_path: Optional[str] = None)`
Initialize store with optional custom database path. Defaults to `var/execution_state.db`.

#### `create(record: ExecutionState) -> ExecutionState`
Create a new execution record in the database.

#### `update(record_id: str, **fields) -> Optional[ExecutionState]`
Update an existing record's fields.

#### `list(start: datetime, end: datetime, limit: int = 100) -> List[ExecutionState]`
List records within a date range, ordered by started_at DESC.

#### `get_latest() -> Optional[ExecutionState]`
Get the most recent execution record.

#### `get_by_id(record_id: str) -> Optional[ExecutionState]`
Get a specific record by ID.

#### `acquire_run_lock(key: str, timeout_seconds: int = 300) -> bool`
Try to acquire a lock, returns True if successful.

#### `release_run_lock(key: str) -> bool`
Release a lock, returns True if the lock was released.

#### `close()`
Close database connection.

## Testing

Run the execution state tests:

```bash
pytest tests/test_services/test_execution_state.py -v
```

The test suite covers:
- ExecutionState dataclass operations
- SqliteExecutionStore CRUD operations
- ExecutionManager workflow
- Concurrency and lock behavior
- Record persistence across store instances
