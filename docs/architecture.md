

# Roster MCP Architecture

## Overview

The Roster MCP system follows a clean, modular architecture based on the **Single Responsibility Principle**. The roster generation pipeline is divided into three main components, each with a clearly defined responsibility.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  Roster Generation Pipeline                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌───────────────────┐
│ RosterDataAgent  │ →  │   AIAnalyzer     │ →  │ RosterOrchestrator│
│  (Data Layer)    │    │ (Analysis Layer) │    │  (Coordination)   │
└──────────────────┘    └──────────────────┘    └───────────────────┘
         ↓                       ↓                        ↓
  Fetches & Prepares      Analyzes & Generates     Coordinates Workflow
```

## Core Components

### 1. RosterDataAgent (`roster_data_agent.py`)

**Responsibility**: Data gathering and preparation

**Does**:
- Fetches historical roster/event data from API
- Evaluates member availability
- Prepares structured data packages for analysis
- Extracts members from events

**Does NOT**:
- Perform AI analysis
- Generate roster recommendations
- Validate rosters

**Key Methods**:
```python
fetch_historical_events(months, category) -> List[Dict]
evaluate_member_availability(members) -> Dict
prepare_analysis_data(months, category) -> Dict
```

**Dependencies**: `RosterAPIClient`

---

### 2. AIAnalyzer (`ai_analyzer.py`)

**Responsibility**: AI-powered analysis and roster generation

**Does**:
- Analyzes historical patterns (frequency, workload, pairings)
- Generates roster recommendations using rule-based or AI algorithms
- Validates proposed rosters
- Generates insights from data

**Does NOT**:
- Fetch data from APIs (receives prepared data)
- Handle data gathering or availability evaluation

**Key Methods**:
```python
analyze_historical_patterns(events) -> Dict
generate_roster(dates, availability, patterns, roles) -> List[Dict]
validate_roster(roster) -> Dict
```

**Dependencies**: None (optionally takes an AI client for advanced generation)

---

### 3. RosterOrchestrator (`roster_orchestrator.py`)

**Responsibility**: Workflow coordination and orchestration

**Does**:
- Coordinates the complete roster generation workflow
- Manages the pipeline from data → analysis → generation → validation
- Provides high-level API for roster generation
- Handles workflow errors and logging

**Does NOT**:
- Implement data fetching logic
- Implement analysis algorithms
- Direct API communication

**Key Methods**:
```python
generate_roster_for_upcoming_months(months_ahead, category, roles) -> Dict
analyze_patterns_only(months, category) -> Dict
validate_existing_roster(roster) -> Dict
```

**Dependencies**: `RosterDataAgent`, `AIAnalyzer`

---

## Supporting Components

### RosterAPIClient (`roster_api_client.py`)

**Responsibility**: REST API communication

- Handles all HTTP requests to roster API
- Authentication and error handling
- Request/response validation

### SchedulerService (`scheduler.py`)

**Responsibility**: Task scheduling and execution

- Periodic roster generation
- Uses `RosterOrchestrator` for execution
- Error handling and retries

---

## Data Flow

### Complete Roster Generation Workflow

```
1. SchedulerService (or manual trigger)
   ↓
2. RosterOrchestrator.generate_roster_for_upcoming_months()
   ↓
3. RosterDataAgent.prepare_analysis_data()
   ├→ fetch_historical_events() → RosterAPIClient.get_events()
   ├→ extract_members_from_events()
   └→ evaluate_member_availability()
   ↓
4. AIAnalyzer.analyze_historical_patterns()
   ├→ Analyze member frequency
   ├→ Analyze role distribution
   ├→ Detect workload imbalances
   └→ Find common pairings
   ↓
5. AIAnalyzer.generate_roster()
   ├→ Generate target dates (Sundays)
   ├→ Apply rule-based or AI algorithm
   ├→ Balance workload
   └→ Avoid consecutive assignments
   ↓
6. AIAnalyzer.validate_roster()
   ├→ Check for duplicate assignments
   ├→ Verify all roles filled
   └→ Validate structure
   ↓
7. Return complete result with rosters, validation, patterns, metadata
```

---

## Design Principles

### Single Responsibility Principle (SRP)

Each class has one clear responsibility:
- **RosterDataAgent**: Data gathering only
- **AIAnalyzer**: Analysis and generation only
- **RosterOrchestrator**: Workflow coordination only

### Dependency Inversion

Components depend on abstractions (interfaces), not concrete implementations:
- `AIAnalyzer` doesn't depend on `RosterAPIClient`
- `RosterOrchestrator` coordinates through interfaces

### Testability

Each component can be tested independently:
- Mock `RosterAPIClient` when testing `RosterDataAgent`
- Mock `RosterDataAgent` and `AIAnalyzer` when testing `RosterOrchestrator`
- Test `AIAnalyzer` with sample data (no API required)

### Flexibility

Easy to swap implementations:
- Change from rule-based to AI-based generation in `AIAnalyzer`
- Replace `RosterAPIClient` with different data source
- Add new orchestration workflows without changing components

---

## Usage Examples

### Basic Usage (via Orchestrator)

```python
from src.services import (
    RosterAPIClient,
    RosterDataAgent,
    AIAnalyzer,
    RosterOrchestrator
)

# Initialize components
api_client = RosterAPIClient(base_url="...", api_key="...")
data_agent = RosterDataAgent(api_client)
analyzer = AIAnalyzer()  # Rule-based
orchestrator = RosterOrchestrator(data_agent, analyzer)

# Generate roster for next 3 months
result = orchestrator.generate_roster_for_upcoming_months(
    months_ahead=3,
    category='chinese'
)

print(f"Generated {len(result['rosters'])} rosters")
print(f"Validation: {'PASS' if result['validation']['is_valid'] else 'FAIL'}")
```

### Analysis Only

```python
# Just analyze patterns without generating roster
analysis = orchestrator.analyze_patterns_only(months=6, category='chinese')
print(analysis['patterns']['insights'])
```

### Custom Workflow

```python
# Use components individually for custom workflow
data = data_agent.prepare_analysis_data(months=3, category='english')
patterns = analyzer.analyze_historical_patterns(data['historical_events'])

# Custom roster generation with specific requirements
custom_rosters = analyzer.generate_roster(
    target_dates=[date(2024, 1, 15), date(2024, 1, 22)],
    available_members=data['availability'],
    historical_patterns=patterns,
    required_roles=['Preacher', 'Worship Leader']
)
```

---

## File Structure

```
src/services/
├── __init__.py                 # Exports all services
├── roster_api_client.py        # API communication
├── roster_data_agent.py        # Data gathering
├── ai_analyzer.py              # Analysis & generation
├── roster_orchestrator.py      # Workflow coordination
└── scheduler.py                # Task scheduling

tests/test_services/
├── test_roster_api_client.py
├── test_roster_data_agent.py
├── test_ai_analyzer.py
├── test_roster_orchestrator.py
└── test_scheduler.py

docs/
├── architecture.md             # This file
├── roster_data_agent.md        # Data agent documentation
├── models.md                   # Domain models
└── api.md                      # API documentation
```

---

## Benefits of This Architecture

✅ **Clear Separation of Concerns**: Each component has one job
✅ **Highly Testable**: Easy to write unit tests with mocks
✅ **Flexible**: Easy to swap implementations
✅ **Maintainable**: Changes isolated to specific components
✅ **Reusable**: Components can be used independently
✅ **Scalable**: Easy to add new features without affecting existing code

---

## Future Enhancements

### Phase 1: AI Integration
- Integrate OpenAI/Claude API in `AIAnalyzer`
- Implement advanced availability logic in `RosterDataAgent`

### Phase 2: Enhanced Scheduling
- Add configurable scheduling strategies
- Support multiple service categories
- Implement conflict resolution

### Phase 3: API Submission
- Add roster submission to `RosterOrchestrator`
- Implement retry logic
- Add rollback capability

---

## See Also

- [RosterDataAgent Documentation](roster_data_agent.md)
- [Domain Models](models.md)
- [API Documentation](api.md)
