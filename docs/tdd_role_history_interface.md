# TDD Interface Design: Role History Manager

## Summary

This document describes the interface-first design for the Role History Management component, created following Test-Driven Development (TDD) principles for Issue #15.

## Design Approach

### 1. **Interface First, Implementation Later**
We defined the public API contracts without implementation, focusing on WHAT the component does, not HOW.

### 2. **Adapter Pattern for Storage**
The design uses the Adapter Pattern to allow different storage backends (SQLite, PostgreSQL, Redis, in-memory) to be swapped without changing business logic.

### 3. **Comprehensive Test Coverage**
All interface methods have comprehensive unit tests (36 tests) covering:
- Happy path scenarios
- Edge cases
- Error conditions
- Integration points

## Files Created

### Interface Definitions
- `src/interfaces/__init__.py` - Package exports
- `src/interfaces/role_history_manager.py` - Interface definitions

### Test Suite
- `tests/test_interfaces/__init__.py` - Test package
- `tests/test_interfaces/test_role_history_manager.py` - 36 unit tests

## Architecture Overview

```
┌─────────────────────────────────────┐
│    IRoleHistoryManager (Interface)  │
│                                     │
│  - normalize_role_name()            │
│  - compute_role_history()           │
│  - persist_role_history()           │
│  - get_role_history_from_storage()  │
│  - get_all_role_history()           │
│  - get_eligible_members_for_role()  │
│  - recompute_role_history()         │
└──────────────┬──────────────────────┘
               │ uses
               ▼
┌─────────────────────────────────────┐
│    IStorageAdapter (Interface)      │
│                                     │
│  - save_role_history()              │
│  - get_role_history()               │
│  - get_all_role_history()           │
│  - delete_role_history()            │
│  - clear_all_history()              │
│  - health_check()                   │
└─────────────────────────────────────┘
               │
               ▼
   ┌───────────────────────┐
   │ Concrete Adapters     │
   ├───────────────────────┤
   │ - SQLiteAdapter       │
   │ - PostgreSQLAdapter   │
   │ - RedisAdapter        │
   │ - InMemoryAdapter     │
   └───────────────────────┘
```

## Key Interfaces

### 1. IRoleHistoryManager

**Responsibility:** Manage historical role assignments and member eligibility

**Key Methods:**
- `compute_role_history()` - Analyze events to build role-member mappings
- `persist_role_history()` - Save computed history via storage adapter
- `get_eligible_members_for_role()` - Query who can perform a role
- `recompute_role_history()` - Orchestrate full refresh cycle

**Design Principles:**
- Single Responsibility: Only manages role history, doesn't fetch events
- Dependency Inversion: Depends on IStorageAdapter abstraction
- Open/Closed: New storage backends via adapter implementation

### 2. IStorageAdapter

**Responsibility:** Abstract storage operations for role history

**Key Methods:**
- `save_role_history()` - Persist single role mapping
- `get_role_history()` - Retrieve single role mapping
- `get_all_role_history()` - Retrieve all mappings
- `health_check()` - Verify storage availability

**Implementations Supported:**
- SQLite (current - using existing AIAnalyzer DB)
- PostgreSQL (future)
- Redis (future - for caching)
- In-memory (testing)

## Test Coverage (36 Tests)

### Test Categories

#### 1. normalize_role_name (5 tests)
- Lowercase conversion
- Whitespace trimming
- Chinese character handling
- None/empty handling

#### 2. compute_role_history (9 tests)
- Basic computation
- Set deduplication
- Role name normalization
- Missing data handling
- Lookback window filtering
- Invalid date handling

#### 3. persist_role_history (4 tests)
- Storage adapter integration
- Empty data handling
- Error validation
- Timestamp updates

#### 4. get_role_history_from_storage (3 tests)
- Retrieval from storage
- Role name normalization
- Non-existent role handling

#### 5. get_all_role_history (2 tests)
- Bulk retrieval
- Empty storage handling

#### 6. get_eligible_members_for_role (5 tests)
- Historical eligibility lookup
- Fallback for new roles
- Sorted output
- Empty list handling

#### 7. recompute_role_history (3 tests)
- Full orchestration
- Lookback filtering
- Return value validation

#### 8. Storage Adapter Integration (2 tests)
- Dependency injection verification
- Multi-role persistence

#### 9. Edge Cases (3 tests)
- Missing members key
- Multiple roles per member
- Set immutability (defensive copying)

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all interface tests
python -m pytest tests/test_interfaces/test_role_history_manager.py -v

# Expected output: 36 passed
```

## Next Steps

### Phase 1: Implement Storage Adapters
1. **SQLiteStorageAdapter** - Implement using existing roster.db
   - Reuse existing `role_history` table from AIAnalyzer
   - Implement all IStorageAdapter methods
   - Add integration tests

2. **InMemoryStorageAdapter** - For testing
   - Simple dict-based implementation
   - No persistence
   - Fast for unit tests

### Phase 2: Implement RoleHistoryManager
1. Create concrete implementation of IRoleHistoryManager
2. Wire up SQLiteStorageAdapter
3. Verify all 36 tests pass with concrete implementation
4. Add integration tests with real database

### Phase 3: Integration with AIAnalyzer
1. Refactor existing AIAnalyzer to use IRoleHistoryManager
2. Remove duplicate role history code
3. Update existing tests to use new interfaces
4. Ensure backward compatibility

### Phase 4: AI Provider Interfaces (Future)
Following the same TDD approach, create:
- `IAIProvider` - Abstract AI service interaction
- `OpenAIAdapter` - OpenAI implementation
- `ClaudeAdapter` - Anthropic Claude implementation
- `MockAIAdapter` - Testing fallback

## Benefits of This Design

### 1. **Testability**
- All interfaces have comprehensive test coverage
- Easy to mock dependencies
- Tests run in milliseconds (no I/O)

### 2. **Flexibility**
- Swap storage backends without code changes
- Support multiple AI providers via adapters
- Easy to extend with new functionality

### 3. **Maintainability**
- Clear separation of concerns
- Well-documented contracts
- Single responsibility per interface

### 4. **Type Safety**
- Full type hints throughout
- IDEs provide autocomplete
- Catch errors at development time

## Example Usage (Future Implementation)

```python
from src.interfaces import IRoleHistoryManager
from src.adapters import SQLiteStorageAdapter

# Setup
storage = SQLiteStorageAdapter(db_path="roster.db")
manager = RoleHistoryManager(storage_adapter=storage)

# Compute and persist role history
events = fetch_events_from_api()
history = manager.recompute_role_history(events, lookback_months=12)

# Query eligible members for a role
eligible = manager.get_eligible_members_for_role(
    "證道",
    all_members=["張三", "李四", "王五"]
)

print(f"Eligible preachers: {eligible}")
# Output: ['張三', '李四']  # Based on historical data
```

## Related Issues

- Issue #15: AI-based roster generation (main issue)
- Issue #8: Role eligibility tracking (dependency)

## References

- Interface definitions: `src/interfaces/role_history_manager.py`
- Test suite: `tests/test_interfaces/test_role_history_manager.py`
- Existing implementation: `src/services/ai_analyzer.py` (to be refactored)
