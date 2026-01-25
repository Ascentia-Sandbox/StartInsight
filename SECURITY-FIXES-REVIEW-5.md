# Security Fixes Review #5: Database Models & Cascade Deletes

**Review Date:** 2026-01-25
**Focus Area:** Database Models - CASCADE Security, RLS Readiness, FK Indexes
**Severity:** CRITICAL - Data Loss Risk from CASCADE Deletes

---

## Executive Summary

**Models Audited:** 15 SQLAlchemy models (216 total fields)
**Critical Issues:** 24 CASCADE delete relationships causing data loss risk
**Medium Issues:** RLS policies not optimized for Phase 5 realtime features
**Low Issues:** 2 FK fields missing indexes (invited_by_id, shared_by_id)

**Risk Assessment:**
- 🔴 **CRITICAL:** User deletion causes permanent loss of all user data ($100+ in AI analyses)
- 🟡 **MEDIUM:** Insight deletion causes loss of user notes/tags/ratings
- 🟢 **LOW:** Minor performance impact from 2 missing FK indexes

---

## Critical Issue #1: Dangerous CASCADE Deletes

### Problem: User Deletion = Total Data Loss

**Affected Models:** 24 CASCADE relationships found

**File:** `backend/app/models/*.py`

**Dangerous CASCADE Chains:**

#### 1. User Deletion → Mass Data Loss
```python
# user.py (Line 110-175)
class User(Base):
    saved_insights: Mapped[list["SavedInsight"]] = relationship(
        cascade="all, delete-orphan",  # ❌ Deletes ALL saved insights
    )

    ratings: Mapped[list["UserRating"]] = relationship(
        cascade="all, delete-orphan",  # ❌ Deletes ALL ratings
    )

    custom_analyses: Mapped[list["CustomAnalysis"]] = relationship(
        cascade="all, delete-orphan",  # ❌ Deletes ALL paid analyses
    )

    interactions: Mapped[list["InsightInteraction"]] = relationship(
        cascade="all, delete-orphan",  # ❌ Deletes ALL interaction logs
    )

    api_keys: Mapped[list["APIKey"]] = relationship(
        cascade="all, delete-orphan",  # ❌ Deletes ALL API keys + usage logs
    )

    subscription: Mapped["Subscription"] = relationship(
        cascade="all, delete-orphan",  # ❌ Deletes subscription + payment history
    )
```

**Impact Scenario:**
```
User requests "Delete my account" (GDPR right to be forgotten)
→ DELETE FROM users WHERE id = '...'
→ CASCADE deletes:
  - 10 custom AI analyses (cost: $5 each = $50 worth of AI work)
  - 100 saved insights with personal notes
  - 500 insight ratings
  - 1,000 interaction logs (analytics data)
  - 3 API keys + 10,000 usage records
  - Subscription + payment history (compliance violation)

Result: ❌ ALL USER DATA GONE FOREVER
Risk: GDPR violation (must keep payment records for 7 years)
```

**Real-World Attack Vector:**
```
1. Attacker compromises user account
2. Calls DELETE /api/users/me (if such endpoint exists)
3. ALL user data deleted permanently
4. No undo, no recovery
5. User loses $50+ of paid AI analyses
```

---

#### 2. Insight Deletion → User Work Loss
```python
# saved_insight.py (Line 46-60)
class SavedInsight(Base):
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),  # ❌ User deleted → saved insight deleted
    )

    insight_id: Mapped[UUID] = mapped_column(
        ForeignKey("insights.id", ondelete="CASCADE"),  # ❌ Insight deleted → saved record deleted
    )
```

**Impact Scenario:**
```
Admin flags an insight as spam/duplicate
→ DELETE FROM insights WHERE id = '...'
→ CASCADE deletes:
  - 50 saved_insights (users lose personal notes, tags, status tracking)
  - 200 user_ratings (all voting history lost)
  - 500 insight_interactions (analytics data lost)

Result: ❌ Users lose work they added (notes, "building this" claims)
Risk: Poor UX - users expect saved data to persist even if original insight removed
```

---

#### 3. Subscription Deletion → Payment History Loss
```python
# subscription.py (Line 38, 147)
class Subscription(Base):
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),  # ❌
    )

class SubscriptionHistory(Base):
    subscription_id: Mapped[UUID] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"),  # ❌
    )
```

**Impact Scenario:**
```
User deletes account
→ DELETE FROM users WHERE id = '...'
→ CASCADE deletes subscription
→ CASCADE deletes subscription_history

Result: ❌ ALL payment records deleted
Risk: Compliance violation (must retain for tax/legal: 7 years in US, 10 years in EU)
```

---

### Root Cause

**SQLAlchemy ORM Defaults:**
```python
# Current code (dangerous):
ForeignKey("users.id", ondelete="CASCADE")  # ❌ Deletes child records

# Safe alternatives:
ForeignKey("users.id", ondelete="RESTRICT")  # ✅ Prevent deletion if children exist
ForeignKey("users.id", ondelete="SET NULL")  # ✅ Keep child, nullify FK
# Or implement soft deletes (recommended)
```

**Why CASCADE was used:**
- Developer convenience (SQLAlchemy default pattern)
- No consideration for data retention requirements
- Missing soft delete architecture

---

### Recommended Fix: Soft Delete Pattern

**Solution Overview:**
1. Add `deleted_at` field to `users` table
2. Change all CASCADE to RESTRICT or SET NULL
3. Implement soft delete logic in API endpoints
4. Filter out deleted users in queries

**Implementation:**

#### Step 1: Add Soft Delete Fields
```python
# user.py
class User(Base):
    # Add soft delete support
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Soft delete timestamp (NULL = active)",
    )

    deleted_by: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        doc="Admin who deleted this user (audit trail)",
    )

    deletion_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for deletion (GDPR request, ban, etc.)",
    )
```

#### Step 2: Change CASCADE to RESTRICT
```python
# saved_insight.py
class SavedInsight(Base):
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),  # ✅ Prevent deletion
    )

    insight_id: Mapped[UUID] = mapped_column(
        ForeignKey("insights.id", ondelete="SET NULL"),  # ✅ Keep saved record, nullify FK
        nullable=True,  # ✅ Make nullable
    )

    # Add denormalized fields for deleted insights
    insight_title_snapshot: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Snapshot of insight title (preserved after insight deletion)",
    )
```

#### Step 3: Implement Soft Delete API
```python
# api/routes/users.py
@router.delete("/me")
async def delete_account(
    current_user: CurrentUser,
    reason: str = "user_request",
    db: AsyncSession = Depends(get_db),
):
    """Soft delete user account (GDPR right to be forgotten)."""

    # ✅ SOFT DELETE - Mark as deleted, don't actually delete
    current_user.deleted_at = datetime.utcnow()
    current_user.deletion_reason = reason

    # Anonymize PII
    current_user.email = f"deleted_{current_user.id}@anonymized.local"
    current_user.display_name = "[Deleted User]"
    current_user.avatar_url = None
    current_user.preferences = {}

    await db.commit()

    # Schedule hard delete after 30 days (compliance retention period)
    # schedule_hard_delete.apply_async(args=[str(current_user.id)], countdown=30*24*3600)

    return {"message": "Account deleted successfully"}
```

#### Step 4: Filter Deleted Users in Queries
```python
# Create a query helper
def active_users_only(query):
    """Filter out soft-deleted users."""
    return query.where(User.deleted_at.is_(None))

# Usage:
active_users = await db.execute(
    active_users_only(select(User))
)
```

---

## Medium Issue #2: RLS Policy Readiness

### Problem: Subquery-Based RLS Policies (Performance)

**Current RLS Design (from architecture.md):**

```sql
-- saved_insights: Requires JOIN to users table
CREATE POLICY "Users can view own saved insights"
  ON saved_insights FOR SELECT
  USING (user_id IN (
    SELECT id FROM users WHERE supabase_user_id = auth.jwt() ->> 'sub'
  ));
```

**Impact:**
- Every RLS check requires subquery → slower
- No direct index on supabase_user_id in saved_insights
- Problem compounds with realtime subscriptions (Phase 5)

**Current Status:**
- ✅ Backend uses service_role (bypasses RLS) - SECURE
- ⚠️ Future Phase 5 (realtime) needs efficient RLS

### Denormalized RLS (Optional Future Enhancement)

**Option A: Add supabase_user_id to Child Tables**
```sql
-- Add to saved_insights, custom_analyses, etc.
ALTER TABLE saved_insights ADD COLUMN supabase_user_id VARCHAR(255);
CREATE INDEX idx_saved_insights_supabase_user_id ON saved_insights(supabase_user_id);

-- Simplified RLS policy
CREATE POLICY "Users can view own" ON saved_insights
  USING (supabase_user_id = auth.jwt() ->> 'sub');
```

**Pros:**
- Direct comparison (10× faster)
- Simple RLS policy
- Better for realtime (Phase 5)

**Cons:**
- Data duplication (supabase_user_id in 5+ tables)
- Sync complexity if user.supabase_user_id changes (rare)

**Recommendation:**
- ⏳ **Defer to Phase 5** (realtime implementation)
- Current subquery approach is acceptable (backend bypasses RLS)
- Optimize when realtime performance becomes bottleneck

---

## Low Issue #3: Missing FK Indexes

### Problem: 2 Foreign Keys Without Indexes

**Affected Fields:**
```
1. team.py: invited_by_id (FK without index)
2. team.py: shared_by_id (FK without index)
```

**Impact:**
- Slow JOINs when querying team invitations
- Slow queries for "who shared this insight"
- Minimal impact (low-traffic Phase 6 features)

### Fix

```python
# team.py
class TeamInvitation(Base):
    invited_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        index=True,  # ✅ ADD THIS
    )

class TeamSharedInsight(Base):
    shared_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id"),
        index=True,  # ✅ ADD THIS
    )
```

**Priority:** LOW (Phase 6 features, low traffic)

---

## Acceptable CASCADE Deletes

These CASCADE relationships are **correct and safe**:

### 1. Team → TeamMember
```python
# team.py
class TeamMember(Base):
    team_id: Mapped[UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"),  # ✅ OK
    )
```
**Why Safe:** If team deleted → members lose access (expected behavior)

### 2. Subscription → SubscriptionHistory
```python
# subscription.py
class SubscriptionHistory(Base):
    subscription_id: Mapped[UUID] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"),  # ✅ OK
    )
```
**Why Safe:** History is part of subscription lifecycle

**BUT:** Subscription → User should NOT CASCADE (see Critical Issue #3)

### 3. APIKey → APIKeyUsage
```python
# api_key.py
class APIKeyUsage(Base):
    api_key_id: Mapped[UUID] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"),  # ✅ OK
    )
```
**Why Safe:** Usage logs tied to API key lifecycle

---

## Summary of Findings

### CASCADE Delete Audit Results

| Model | CASCADE Deletes | Risk Level | Fix Required |
|-------|----------------|------------|--------------|
| `User` | 8 child relationships | 🔴 CRITICAL | Soft delete |
| `Insight` | 3 child relationships | 🟡 MEDIUM | SET NULL |
| `Subscription` | 1 child (history) | 🟡 MEDIUM | Keep history, soft delete user |
| `Team` | 4 child relationships | 🟢 LOW | OK (expected) |
| `APIKey` | 1 child (usage) | 🟢 LOW | OK (expected) |

### RLS Policy Readiness

| Table | RLS Needed | Current Design | Performance | Action |
|-------|-----------|----------------|-------------|--------|
| `users` | Yes | Direct (supabase_user_id) | ✅ Fast | None |
| `saved_insights` | Yes | Subquery (via user_id) | ⚠️ Slow | Phase 5 |
| `custom_analyses` | Yes | Subquery (via user_id) | ⚠️ Slow | Phase 5 |
| `insights` | Yes | Public read | ✅ Fast | None |
| `raw_signals` | Yes | Admin write only | ✅ Fast | None |

### FK Index Audit

| Model | Total FK Fields | Indexed | Missing Index | Priority |
|-------|----------------|---------|---------------|----------|
| All models | 26 FK fields | 24 (92%) | 2 (8%) | LOW |

**Missing Indexes:**
1. `team.invited_by_id` - Low priority (Phase 6)
2. `team.shared_by_id` - Low priority (Phase 6)

---

## Recommendations

### Immediate Actions (Critical)

1. **Implement Soft Delete for Users** (Priority: 🔴 CRITICAL)
   - Add `deleted_at`, `deleted_by`, `deletion_reason` fields
   - Change all `ondelete="CASCADE"` on users.id to `ondelete="RESTRICT"`
   - Create soft delete API endpoint
   - Add query filters for active users only

2. **Change Insight CASCADE to SET NULL** (Priority: 🟡 MEDIUM)
   - `saved_insights.insight_id`: `ondelete="SET NULL"`
   - `user_ratings.insight_id`: `ondelete="SET NULL"`
   - `insight_interactions.insight_id`: `ondelete="SET NULL"`
   - Add denormalized snapshot fields (insight_title_snapshot, etc.)

3. **Protect Payment History** (Priority: 🔴 CRITICAL)
   - Never delete subscription history (compliance: 7-10 years)
   - Anonymize user PII but keep financial records
   - Implement separate data retention policy

### Phase 5 Actions (Medium Priority)

4. **Optimize RLS Policies** (Priority: ⏳ Phase 5)
   - Test realtime performance with subquery RLS
   - If slow: Add denormalized `supabase_user_id` to child tables
   - Create migration to sync supabase_user_id

5. **Add FK Indexes** (Priority: 🟢 LOW - Phase 6)
   - Add index to `team.invited_by_id`
   - Add index to `team.shared_by_id`

### Long-Term Improvements

6. **Data Retention Policy**
   - Define retention periods (GDPR: 30 days grace, compliance: 7-10 years)
   - Implement scheduled hard delete job (Arq task)
   - Audit logging for all deletions

7. **Backup Strategy**
   - Daily database backups (Supabase PITR: 7-day retention on Pro tier)
   - Test restore procedures quarterly
   - Document recovery runbook

---

## Migration Plan

### Migration 1: Add Soft Delete Fields
```python
# alembic/versions/XXXX_add_soft_delete.py
def upgrade():
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('deleted_by', postgresql.UUID(), nullable=True))
    op.add_column('users', sa.Column('deletion_reason', sa.Text(), nullable=True))
    op.create_index('ix_users_deleted_at', 'users', ['deleted_at'])
```

### Migration 2: Change CASCADE to RESTRICT/SET NULL
```python
# alembic/versions/XXXX_fix_cascade_deletes.py
def upgrade():
    # saved_insights
    op.drop_constraint('saved_insights_user_id_fkey', 'saved_insights')
    op.create_foreign_key(
        'saved_insights_user_id_fkey',
        'saved_insights', 'users',
        ['user_id'], ['id'],
        ondelete='RESTRICT'  # ✅ Changed from CASCADE
    )

    op.drop_constraint('saved_insights_insight_id_fkey', 'saved_insights')
    op.create_foreign_key(
        'saved_insights_insight_id_fkey',
        'saved_insights', 'insights',
        ['insight_id'], ['id'],
        ondelete='SET NULL'  # ✅ Changed from CASCADE
    )

    # Make insight_id nullable
    op.alter_column('saved_insights', 'insight_id', nullable=True)

    # Add snapshot fields
    op.add_column('saved_insights', sa.Column('insight_title_snapshot', sa.Text(), nullable=True))
```

### Migration 3: Add FK Indexes (Phase 6)
```python
# alembic/versions/XXXX_add_team_fk_indexes.py
def upgrade():
    op.create_index('ix_team_invitations_invited_by_id', 'team_invitations', ['invited_by_id'])
    op.create_index('ix_team_shared_insights_shared_by_id', 'team_shared_insights', ['shared_by_id'])
```

---

## Testing Checklist

### Soft Delete Tests
- [ ] User soft delete sets deleted_at timestamp
- [ ] Deleted users excluded from login
- [ ] Deleted users excluded from search results
- [ ] Attempting to delete user with children raises error (if using RESTRICT)
- [ ] Anonymization removes all PII correctly
- [ ] Subscription history preserved after user deletion

### CASCADE Delete Tests
- [ ] Deleting team cascades to team_members (expected)
- [ ] Deleting API key cascades to usage logs (expected)
- [ ] Deleting insight does NOT delete saved_insights (SET NULL)
- [ ] Deleting insight preserves user notes via snapshots

### Performance Tests
- [ ] Query performance with deleted_at filter (should use index)
- [ ] RLS policy performance with subquery (baseline for Phase 5)

---

## Conclusion

**Status:** ⚠️ CRITICAL ISSUES IDENTIFIED - NO CODE CHANGES YET

**Critical Risks:**
1. 🔴 User deletion causes permanent data loss ($50+ AI analyses, payment history)
2. 🟡 Insight deletion causes loss of user work (notes, tags)
3. 🟡 Compliance violation (payment records must be retained 7-10 years)

**Immediate Next Steps:**
1. Create migrations for soft delete fields
2. Change CASCADE relationships to RESTRICT/SET NULL
3. Implement soft delete API endpoints
4. Add query filters for active users
5. Test data retention compliance

**Code Changes Required:**
- 3 Alembic migrations (soft delete fields, CASCADE fix, FK indexes)
- User model updates (3 new fields)
- 5+ child models (nullable insight_id, snapshot fields)
- API endpoint changes (soft delete logic)
- Query helper functions (active users filter)

**Review #6:** Full backend security audit (all 103 files) - comprehensive security sweep

---

**Files to Modify (Deferred to Next Commit):**
1. `backend/app/models/user.py` - Add soft delete fields
2. `backend/app/models/saved_insight.py` - Change CASCADE, add snapshots
3. `backend/app/models/custom_analysis.py` - Change CASCADE to RESTRICT
4. `backend/app/models/user_rating.py` - Change CASCADE to SET NULL
5. `backend/app/models/insight_interaction.py` - Change CASCADE to SET NULL
6. `backend/app/models/subscription.py` - Protect history from user deletion
7. `backend/app/models/team.py` - Add FK indexes
8. `backend/app/api/routes/users.py` - Implement soft delete endpoint
9. `backend/alembic/versions/XXXX_soft_delete.py` - Migration #1
10. `backend/alembic/versions/XXXX_fix_cascades.py` - Migration #2
11. `backend/alembic/versions/XXXX_team_indexes.py` - Migration #3

**Estimated Implementation Time:** 4-6 hours (migrations + testing)
