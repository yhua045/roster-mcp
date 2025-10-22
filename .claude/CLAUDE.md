# Project-Specific Instructions for Claude Code

## Git Workflow - IMPORTANT

### Always Create New Branches from `main`

**CRITICAL:** Before starting any new feature or issue, ALWAYS:

1. **Switch to main branch first:**
   ```bash
   git checkout main
   ```

2. **Pull latest changes:**
   ```bash
   git pull origin main
   ```

3. **Then create new feature branch:**
   ```bash
   git checkout -b feature/descriptive-name-issue-XX
   ```

**DO NOT:**
- ❌ Create new branches from other feature branches
- ❌ Work directly on main branch
- ❌ Create branches without pulling latest main first

### Branch Naming Convention

Use this pattern:
- `feature/descriptive-name-issue-XX` for new features
- `fix/descriptive-name-issue-XX` for bug fixes
- `refactor/descriptive-name` for refactoring
- `docs/descriptive-name` for documentation

**Examples:**
- `feature/json-file-writer-issue-18`
- `feature/scheduler-json-writer-issue-20`
- `fix/validation-error-issue-25`

## Development Workflow

### Test-Driven Development (TDD)

This project follows TDD principles:

1. **Tests First** - Write tests before implementation
2. **RED** - Write failing tests
3. **GREEN** - Implement to make tests pass
4. **REFACTOR** - Clean up code

### Testing

**Run tests before committing:**
```bash
# Run specific test file
python3 -m unittest tests.test_services.test_scheduler -v

# Run all service tests
python3 -m unittest discover tests/test_services -v

# Run all tests (check for regressions)
python3 -m unittest discover tests -v
```

**All tests must pass before creating PR.**

### Commit Message Format

Follow conventional commits:

```
type: brief description (Issue #XX)

Detailed description of changes...

Implementation:
- Key point 1
- Key point 2

Tests:
- Test coverage details

Files:
- File changes summary

Acceptance Criteria Met:
✓ Criterion 1
✓ Criterion 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `docs:` - Documentation
- `chore:` - Maintenance

### Pull Request Workflow

1. **Create feature branch from main** (see Git Workflow above)
2. **Write tests first** (TDD approach)
3. **Implement feature**
4. **Run all tests** - ensure no regressions
5. **Commit with detailed message**
6. **Push to remote**
7. **Create PR with comprehensive description**

**PR Description Must Include:**
- Summary
- Motivation
- Implementation details
- Test coverage
- Acceptance criteria checklist
- Example usage

## Project Structure

```
roster-mcp/
├── src/
│   ├── config/          # Configuration and settings
│   ├── services/        # Business logic services
│   └── interfaces/      # Abstract interfaces
├── tests/
│   ├── test_services/   # Service tests
│   └── test_interfaces/ # Interface tests
├── roster-json/         # Generated roster outputs (gitignored)
└── .claude/             # Claude Code configuration
```

## Code Standards

### Type Hints
- Always use type hints for function parameters and return values
- Use `Optional[Type]` for nullable values
- Use `Dict[str, Any]` for flexible dictionaries

### Error Handling
- Use specific exception types (`ValueError`, `TypeError`, `IOError`)
- Log errors before raising
- Provide meaningful error messages
- Don't let scheduler/services crash on errors

### Testing Standards
- Mock external dependencies
- Use `setUp()` and `tearDown()` for fixture management
- Clean up test files/directories in `tearDown()`
- Test happy path and error cases
- Test edge cases (None, empty, invalid inputs)

### Documentation
- Docstrings for all public methods
- Include Args, Returns, Raises sections
- Provide usage examples in docstrings

## Common Tasks

### Starting a New Feature

```bash
# 1. Switch to main and update
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/my-feature-issue-XX

# 3. Write tests first
# Create tests/test_services/test_my_feature.py

# 4. Run tests (should fail - RED)
python3 -m unittest tests.test_services.test_my_feature -v

# 5. Implement feature
# Edit src/services/my_feature.py

# 6. Run tests (should pass - GREEN)
python3 -m unittest tests.test_services.test_my_feature -v

# 7. Run all tests (check regressions)
python3 -m unittest discover tests/test_services -v

# 8. Commit and push
git add .
git commit -m "feat: implement my feature (Issue #XX)"
git push -u origin feature/my-feature-issue-XX

# 9. Create PR
gh pr create --title "..." --body "..." --base main
```

### Reviewing GitHub Issues

Use `gh` CLI to fetch issue details:
```bash
gh issue view XX --json title,body,labels
```

## Environment Variables

Key environment variables:
- `WRITE_ROSTER_JSON=true` - Enable roster writing (default: true)
- `ROSTER_OUTPUT_DIR=roster-json` - Output directory (default: roster-json)
- `LOG_LEVEL=INFO` - Logging level
- `DRY_RUN=false` - Dry run mode

## Dependencies

Install dependencies:
```bash
pip3 install -r requirements.txt
```

Core dependencies:
- `requests` - API client
- `pyyaml` - Configuration
- `python-dotenv` - Environment variables

## Troubleshooting

### Tests Failing Due to Missing Dependencies
```bash
pip3 install requests
```

### Git Merge Conflicts
```bash
git checkout main
git pull origin main
git checkout feature/my-branch
git merge main
# Resolve conflicts
git add .
git commit -m "chore: merge main"
```

## Remember

1. **ALWAYS start from main branch** for new features
2. **Write tests first** (TDD)
3. **Run all tests** before committing
4. **Use descriptive branch names** with issue numbers
5. **Write comprehensive commit messages**
6. **Create detailed PR descriptions**
7. **Clean up test artifacts** in tearDown()
8. **Use dependency injection** for testability
