# Backup & Disaster Recovery Strategy

## Overview
StartInsight uses Supabase PostgreSQL with automatic backups. This document outlines backup verification, restore procedures, and disaster recovery.

## Backup Configuration

### Supabase Automatic Backups
- **Frequency:** Daily at 02:00 UTC
- **Retention:** 7 days (Pro plan)
- **Location:** Supabase Sydney region (ap-southeast-2)
- **Encryption:** AES-256 at rest
- **Backup Method:** Physical (full database snapshot)

### Verification (Weekly)
```bash
# Check backup status via Supabase dashboard
# Project > Settings > Database > Backups

# Expected:
# - Last backup: < 24 hours ago
# - Status: Success
# - Size: ~500MB (as of 2026-02-07)
```

## Restore Procedures

### Scenario 1: Point-in-Time Recovery (Last 7 Days)

**When:** Accidental data deletion, bad migration, data corruption

**Steps:**
1. Access Supabase Dashboard > Project > Database > Backups
2. Select target backup (date/time)
3. Click "Restore"
4. Confirm database name and target project
5. Wait 10-30 minutes for restore (depends on size)
6. Verify data integrity:
   ```sql
   SELECT COUNT(*) FROM insights;
   SELECT MAX(created_at) FROM raw_signals;
   SELECT COUNT(*) FROM users WHERE is_active = true;
   ```
7. Update application DATABASE_URL if needed
8. Restart Railway deployment

**RTO (Recovery Time Objective):** 30-60 minutes
**RPO (Recovery Point Objective):** Up to 24 hours (last backup)

### Scenario 2: Manual Export (Before Risky Operations)

**When:** Before major migrations, schema changes, data transformations

**Steps:**
```bash
# Export full database
pg_dump -h db.mxduetfcsgttwwgszjae.supabase.co -U postgres -d postgres -F c -f backup_$(date +%F).dump

# Export specific tables (critical data only)
pg_dump -h db.mxduetfcsgttwwgszjae.supabase.co -U postgres -d postgres \
  -t insights -t raw_signals -t users -t subscriptions \
  -F c -f critical_tables_$(date +%F).dump

# Store in S3 or local encrypted storage
aws s3 cp backup_$(date +%F).dump s3://startinsight-backups/manual/
```

**Restore from manual backup:**
```bash
# Restore full database
pg_restore -h db.mxduetfcsgttwwgszjae.supabase.co -U postgres -d postgres -c backup_2026-02-07.dump

# Restore specific tables
pg_restore -h db.mxduetfcsgttwwgszjae.supabase.co -U postgres -d postgres \
  -t insights -t raw_signals critical_tables_2026-02-07.dump
```

## Testing Schedule

### Monthly Backup Test (First Monday)
1. Select random backup from last 7 days
2. Restore to test project (create separate Supabase project for testing)
3. Verify row counts match production (within 24h)
4. Verify API endpoints return data
5. Document test results in `backup-test-log.md`

### Quarterly Disaster Recovery Drill
1. Simulate complete database loss
2. Restore from oldest backup (7 days ago)
3. Measure RTO (time to restore)
4. Verify application functionality
5. Update procedures based on learnings

## Backup Monitoring

### Alerts (Supabase Dashboard)
- ⚠️ Warning: Backup failed (retry in 1 hour)
- 🚨 Critical: 2 consecutive backup failures

### Manual Check (Weekly)
```bash
# Check backup age via Supabase API
curl -X GET 'https://api.supabase.io/v1/projects/{project_id}/database/backups' \
  -H "Authorization: Bearer {service_key}"

# Expected: last_backup_at < 24 hours ago
```

## Escalation Path

| Issue | Contact | SLA |
|-------|---------|-----|
| Backup failed | Supabase Support | 4 hours |
| Restore needed | DevOps team → Supabase | 1 hour |
| Data loss > 24h | Founder + Supabase Enterprise | Immediate |

## Cost Considerations

- **Supabase Pro:** $25/mo (includes 7-day backup retention)
- **Manual exports:** Free (storage cost only)
- **Extended retention (30 days):** Contact Supabase sales ($$$)

## Recovery Scenarios

| Scenario | Solution | RTO | RPO |
|----------|----------|-----|-----|
| Accidental DELETE | Point-in-time restore | 30 min | 24 hrs |
| Bad migration | Rollback + restore | 60 min | 24 hrs |
| Database corruption | Full restore | 60 min | 24 hrs |
| Supabase region outage | Wait or migrate region | 2-4 hrs | 0 (replica) |
| Complete data loss | Restore from backup | 60 min | 24 hrs |

## Data Criticality Matrix

| Data Type | Criticality | Backup Strategy | Retention |
|-----------|-------------|-----------------|-----------|
| Insights | HIGH | Daily auto-backup | 7 days |
| Raw Signals | MEDIUM | Daily auto-backup | 7 days |
| User Data | CRITICAL | Daily auto-backup + manual before changes | 7 days |
| Subscriptions | CRITICAL | Daily auto-backup + manual before changes | 7 days |
| Analytics | LOW | Daily auto-backup | 7 days |

## Pre-Deployment Backup Checklist

Before deploying major changes:

- [ ] Create manual backup
- [ ] Verify backup size (> 0 bytes)
- [ ] Test restore to dev environment
- [ ] Document rollback procedure
- [ ] Notify team of maintenance window
- [ ] Set up monitoring alerts

## Post-Incident Report Template

```markdown
# Incident Report: [Date]

## Incident Type
[Data loss / Corruption / Accidental deletion]

## Timeline
- **Detection:** [Time]
- **Response:** [Time]
- **Restore Started:** [Time]
- **Restore Complete:** [Time]
- **Verification:** [Time]

## Impact
- **Data Loss:** [Duration/Rows affected]
- **Users Affected:** [Count]
- **Downtime:** [Duration]

## Root Cause
[What went wrong]

## Resolution
[How we fixed it]

## Lessons Learned
[What we'll change]
```

## Automation Opportunities

Future improvements:
1. **Daily backup verification script** - Automate weekly manual checks
2. **Backup age monitoring** - Alert if backup > 25 hours old
3. **Automated restore testing** - Monthly restore to test environment
4. **Backup size trend tracking** - Monitor growth patterns

## Contact Information

**Supabase Support:**
- Dashboard: https://supabase.com/dashboard/support
- Email: support@supabase.io
- Slack: (Enterprise only)

**Internal Escalation:**
- DevOps Lead: [Contact info]
- Founder: [Contact info]
- On-call: [PagerDuty/Opsgenie]
