# Claude Code Configuration

This directory contains configuration and instructions for Claude Code when working on this project.

## Files

### `CLAUDE.md`
Comprehensive project-specific instructions including:
- Git workflow (branching from main)
- TDD methodology
- Testing standards
- Commit message format
- PR workflow
- Code standards
- Common tasks reference

**Claude Code will read this file** to understand project conventions.

### `rules.md`
Strict rules that Claude Code must follow:
- MANDATORY git branch workflow
- TDD workflow requirements
- Testing requirements
- Commit standards
- Branch naming patterns
- Automatic checks before PR

**Claude Code treats these as hard requirements.**

### `commands/`
Custom slash commands for this project (if any).

### `settings.local.json`
Local Claude Code settings (not committed to git).

## How It Works

When Claude Code starts working on this project, it will:

1. **Read `CLAUDE.md`** - Learn project conventions and workflow
2. **Follow `rules.md`** - Enforce mandatory requirements
3. **Apply automatically** - No need to remind on every task

## Key Enforced Behaviors

### Git Workflow
Claude Code will automatically:
- Switch to `main` branch before creating new feature branches
- Pull latest changes from `main`
- Create properly named feature branches
- Never branch from feature branches

### TDD Workflow
Claude Code will:
- Write tests before implementation
- Run tests to verify they fail first (RED)
- Implement features to make tests pass (GREEN)
- Run all tests to check for regressions

### Commit Standards
Every commit will include:
- Issue number in title
- Detailed description
- Test coverage summary
- Acceptance criteria checklist

## Updating Instructions

To modify Claude Code's behavior:

1. **Edit `CLAUDE.md`** for general guidelines and preferences
2. **Edit `rules.md`** for strict requirements
3. Commit changes to git
4. Claude Code will pick up changes in next session

## Example: Enforcing Main Branch Workflow

Before (manual reminder needed):
```
User: "Work on issue #20"
You: *creates branch from current feature branch* ❌
```

After (automatic):
```
User: "Work on issue #20"
Claude Code:
1. git checkout main
2. git pull origin main
3. git checkout -b feature/scheduler-json-writer-issue-20
✅ Correct workflow automatically followed
```

## Benefits

✅ **Consistency** - Same workflow every time
✅ **No reminders** - Claude Code remembers project rules
✅ **Best practices** - TDD, testing, clean commits enforced
✅ **Team alignment** - Everyone follows same standards
✅ **Quality** - Automated checks before commits/PRs

## Troubleshooting

If Claude Code doesn't follow the workflow:

1. Check if `.claude/CLAUDE.md` exists and is readable
2. Check if `.claude/rules.md` exists
3. Restart Claude Code session
4. Explicitly reference: "Please follow the rules in .claude/rules.md"

## Version Control

These files should be committed to git so that:
- All team members benefit
- Project standards are documented
- Claude Code configuration is versioned
