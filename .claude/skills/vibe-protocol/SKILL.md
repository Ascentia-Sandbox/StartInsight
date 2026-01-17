---
name: vibe-protocol
description: Context keeper - automates documentation updates and progress tracking. Triggers after successful commands or file modifications.
---

# Vibe Protocol Standards (The Context Keeper)

This skill automates the most tedious part of Vibe Coding: keeping documentation synchronized with code changes.

## Trigger
Automatically applies:
- After any successful terminal command (exit code 0)
- After any file modification (create, edit, delete)
- When implementing a feature or completing a task

## Rules

### 1. Automatic Progress Logging
After every successful operation, append a log entry to `memory-bank/progress.md`.

**Format**:
```markdown
- [YYYY-MM-DD] [TASK_ID]: [Brief Description]
  - Files modified: [path/to/file, path/to/another/file]
  - Technical notes: [Key architectural decisions, patterns used]
  - Status: [✓ Complete / ⚠️ Blocked / 🔄 In Progress]
```

**Example**:
```markdown
- [2026-01-18] [PHASE-1.3]: Implemented async database session management
  - Files modified: backend/app/db/session.py, backend/app/core/config.py
  - Technical notes: Used AsyncSession with async context managers, configured connection pooling
  - Status: ✓ Complete
```

### 2. Architecture Updates
If the change affects project structure, immediately update `memory-bank/architecture.md`:

**Triggers for architecture updates**:
- New database models added
- API endpoints created or modified
- New service/module added
- Data flow changes
- Integration with external services

**What to update**:
- Section 5 (Database Schema) for model changes
- Section 6 (API Endpoints) for route changes
- Section 2 (Component Architecture) for new modules
- Section 3 (Data Flow) for flow changes

### 3. Active Context Synchronization
Check `memory-bank/active-context.md` and update task status:

**When to update**:
- Task completed: Move from "Current Tasks" to appropriate section
- Blocker encountered: Add to "Blockers" section
- New insight discovered: Add to "What's Working" or "What's Next"

**Status transitions**:
```
[ ] Planned → [🔄] In Progress → [✓] Complete
                               → [⚠️] Blocked
```

### 4. Phase Tracking
Always verify you're working in the correct phase:
- Read `memory-bank/active-context.md` to confirm current phase
- Check `memory-bank/implementation-plan.md` for phase requirements
- Don't jump ahead to future phases without completing prerequisites

### 5. README Synchronization
When changes affect setup or usage, update relevant README files:
- `backend/README.md`: Backend setup, entry points, development commands
- Root `README.md`: Overall project setup, architecture overview (when created)

## Standard Workflow

After completing any task:

1. **Log to progress.md**:
   ```bash
   # Append entry with date, files, notes, status
   ```

2. **Check architecture impact**:
   ```bash
   # If models/APIs/structure changed, update architecture.md
   ```

3. **Update active-context.md**:
   ```bash
   # Move task to completed, note any blockers
   ```

4. **Verify phase alignment**:
   ```bash
   # Confirm still in correct phase, update if phase completed
   ```

## Example Complete Workflow

### Scenario: Implemented Reddit scraper

**Step 1: Log to progress.md**:
```markdown
- [2026-01-18] [PHASE-1.7]: Implemented Reddit scraper with PRAW integration
  - Files modified: backend/app/scrapers/reddit_scraper.py, backend/requirements.txt
  - Technical notes: Used async PRAW wrapper, implemented rate limiting with tenacity, structured output with ScrapeResult Pydantic model
  - Status: ✓ Complete
```

**Step 2: Update architecture.md** (if applicable):
```markdown
## Section 7: External Integrations

### Reddit (PRAW)
- Purpose: Collect startup discussions and market signals
- Implementation: `app/scrapers/reddit_scraper.py`
- Rate limiting: 60 requests/minute
- Output format: ScrapeResult → Source model
```

**Step 3: Update active-context.md**:
Move task from "Current Tasks" to completed:
```markdown
## Recent Completions
- [✓] Phase 1.7: Reddit scraper implementation
  - Used PRAW async wrapper
  - Integrated with Source model
  - Ready for testing
```

**Step 4: Check phase status**:
If all Phase 1 tasks completed, update:
```markdown
## Current Phase
**Phase 2: Intelligence Layer** (Starting 2026-01-19)
```

## Anti-Patterns to Avoid
- ❌ Completing work without logging to progress.md
- ❌ Skipping architecture.md updates for structural changes
- ❌ Not syncing active-context.md status
- ❌ Working on future phases without completing current phase
- ❌ Letting documentation drift from actual code

## Automation Checklist

After EVERY successful operation, ask:
- [ ] Did I log this to `progress.md`?
- [ ] Does this change require `architecture.md` update?
- [ ] Should I update task status in `active-context.md`?
- [ ] Is the current phase still accurate?
- [ ] Do READMEs need updating?

## Quick Commands

```bash
# Append to progress.md
echo "- [$(date +%Y-%m-%d)] [TASK]: Description" >> memory-bank/progress.md

# Check current phase
grep "Current Phase" memory-bank/active-context.md

# View recent progress
tail -20 memory-bank/progress.md
```

## Integration with Git Workflow

When creating commits, this protocol ensures:
- All changes are documented in progress.md
- Architecture changes are reflected in architecture.md
- Task tracking is current in active-context.md
- README files stay synchronized

This makes every commit traceable and well-documented.
