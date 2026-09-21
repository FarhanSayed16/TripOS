# Postgres Backup & Restore (Render)

## Automated Backups
Render automatically takes daily backups of managed PostgreSQL databases. They are retained for 7 days.

## Manual Backup (Dump)
To take a manual backup before a major migration or operation:
1. Get the external database URL from the Render Dashboard.
2. Run `pg_dump`:
   ```bash
   pg_dump "postgres://user:pass@host:port/dbname" -F c > tripos_backup_$(date +%F).dump
   ```

## Restore Procedure
1. Provision a new Render Postgres instance (do not restore over a live corrupted DB unless absolutely necessary).
2. Run `pg_restore`:
   ```bash
   pg_restore -d "postgres://user:pass@new_host:port/dbname" -1 tripos_backup_YYYY-MM-DD.dump
   ```
3. Update the `DATABASE_URL` environment variable on the API and Worker services to point to the new instance.
4. Restart the services.

## Restore dry-run log (FIX-P39-01)

| Date | Environment | Steps | Result |
|---|---|---|---|
| 2026-09-19 | Local Docker Postgres (`tripos` on :5433) | `pg_dump` custom format → restore into `tripos_restore_dryrun` → `SELECT 1` + `alembic_version` check → drop DB | **PASS** — procedure works; Render hosted dry-run still pending live URL |

### Local commands used

```bash
docker exec tripos-postgres pg_dump -U tripos -F c tripos > /tmp/tripos_sprint_t.dump
docker exec tripos-postgres createdb -U tripos tripos_restore_dryrun
docker exec -i tripos-postgres pg_restore -U tripos -d tripos_restore_dryrun -1 < /tmp/tripos_sprint_t.dump
docker exec tripos-postgres psql -U tripos -d tripos_restore_dryrun -c "SELECT version_num FROM alembic_version"
docker exec tripos-postgres dropdb -U tripos tripos_restore_dryrun
```
