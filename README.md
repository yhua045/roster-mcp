# Roster MCP - AI-Powered Church Roster Management

An intelligent roster management system that uses AI to analyze past scheduling patterns and automatically generate optimal future rosters for church services.

## Features

- **AI-Powered Scheduling**: Analyzes historical roster data to create balanced schedules
- **REST API Integration**: Seamlessly connects with existing roster systems
- **Automated Scheduling**: Runs on configurable intervals to generate upcoming rosters
- **Domain-Driven Design**: Clear separation of Event, ServiceInfo, and Member models
- **Role-Based Assignment**: Supports multiple roles (worship leader, musicians, ushers, etc.)

## Architecture

This project follows a clean, maintainable architecture designed for single-developer maintenance:

```
src/
├── models/      # Domain models (Event, ServiceInfo, Member)
├── services/    # Business logic (API client, AI analyzer, scheduler)
├── config/      # Configuration management
├── utils/       # Shared utilities
└── exceptions/  # Custom exceptions
```

## Domain Models

- **Event**: Represents service occurrences on specific dates
- **ServiceInfo**: Contains metadata about services (category, footnotes, skip info)
- **Member**: Links people to events with specific roles

See [docs/models.md](docs/models.md) for detailed model documentation.

## Getting Started

### Prerequisites

- Python 3.9+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yhua045/roster-mcp.git
cd roster-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Run the application:
```bash
python src/main.py
```

## Configuration

The application can be configured via environment variables or YAML configuration files in the `config/` directory.

## API Integration

The system integrates with REST APIs to:
- Retrieve historical roster data
- Fetch member availability
- Submit generated rosters

## Development

### Running Tests
```bash
pytest tests/
```

### Database Migrations
```bash
# Apply migrations
python -m migrations.apply
```

## Documentation

- [Domain Models](docs/models.md) - Detailed model specifications
- [API Documentation](docs/api.md) - REST API endpoints and contracts
- [AI Agent](docs/ai_agent.md) - Data gathering and payload preparation for AI roster generation
- [Deployment Guide](docs/deployment.md) - Production deployment instructions

## License

MIT

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.