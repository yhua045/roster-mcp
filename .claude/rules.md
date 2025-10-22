# Claude Code Rules for This Project

## Git Branch Workflow - MANDATORY

### ALWAYS Follow This Sequence

When starting ANY new task/issue/feature:

```bash
# Step 1: ALWAYS switch to main first
git checkout main

# Step 2: ALWAYS pull latest changes
git pull origin main

# Step 3: THEN create new feature branch
git checkout -b feature/descriptive-name-issue-XX
```

**NEVER:**
- Create branches from other feature branches
- Skip pulling latest main
- Work directly on main branch

### Exception Handling

If currently on a feature branch and asked to start new work:
1. Ask user: "Should I switch to main first before creating the new branch?"
2. If yes, execute the 3-step sequence above
3. If no, clarify with user before proceeding

## TDD Workflow - MANDATORY

For all new features:
1. Write tests FIRST (before implementation)
2. Run tests to verify they fail (RED)
3. Implement feature
4. Run tests to verify they pass (GREEN)
5. Refactor if needed
6. Run ALL tests to check for regressions

## Testing Requirements

Before committing:
- ✅ All new tests must pass
- ✅ All existing tests must still pass (no regressions)
- ✅ Run: `python3 -m unittest discover tests/test_services -v`

## Commit Standards

Every commit must:
- Include issue number: `feat: description (Issue #XX)`
- Have detailed commit body
- Include test coverage summary
- Include acceptance criteria checklist
- End with Claude Code attribution

## Branch Naming

Pattern: `{type}/{description}-issue-{number}`

Examples:
- `feature/json-file-writer-issue-18`
- `feature/scheduler-json-writer-issue-20`
- `fix/validation-error-issue-25`
- `refactor/cleanup-services`

## Automatic Checks

Before creating any PR, verify:
- [ ] Started from latest main branch
- [ ] All tests pass (150+ tests)
- [ ] No test files left in working directory
- [ ] Comprehensive PR description written
- [ ] Issue number included in title

## File Cleanup

Always clean up in tearDown():
- Remove test output directories (roster-json, etc.)
- Remove temporary test files
- Use `shutil.rmtree()` for directories

## Error Handling Philosophy

- Services should NOT crash on errors
- Log errors with meaningful messages
- Raise specific exception types
- Use try-except for external operations
