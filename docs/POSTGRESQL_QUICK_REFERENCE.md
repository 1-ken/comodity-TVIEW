# PostgreSQL Configuration - Quick Reference

## Connection Credentials
```
Host:     localhost
Port:     5432
Database: commodities
User:     myuser
Password: mypassword
```

## Database Connection String
```
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/commodities
```

## Quick Commands

### Connect to Database
```bash
PGPASSWORD=mypassword psql -h localhost -U myuser -d commodities
```

### List All Tables
```sql
\dt
```

### View Alerts
```sql
SELECT id, pair, target_price, condition, status, created_at 
FROM alerts ORDER BY created_at DESC;
```

### View Price History
```sql
SELECT COUNT(*) FROM price_history;
SELECT timestamp, snapshot FROM price_history ORDER BY timestamp DESC LIMIT 5;
```

### View Candles
```sql
SELECT pair, timeframe, COUNT(*) FROM candles GROUP BY pair, timeframe;
SELECT * FROM candles WHERE pair = 'BTCUSD' AND timeframe = '1m' LIMIT 10;
```

### Delete Alert
```sql
DELETE FROM alerts WHERE id = 'uuid-here';
```

### Clear Old Data
```sql
-- Delete old price history (older than 7 days)
DELETE FROM price_history WHERE timestamp < NOW() - INTERVAL '7 days';

-- Delete old candles (older than 30 days)
DELETE FROM candles WHERE timestamp < NOW() - INTERVAL '30 days';
```

## Application Commands

### Initialize Database
```bash
source .venv/bin/activate
python init_db.py
```

### Start Application
```bash
python run.py
```

### Test API
```bash
# Get snapshot
curl http://localhost:8001/snapshot

# Create alert
curl -X POST http://localhost:8001/api/alerts \
  -H "Content-Type: application/json" \
  -d '{"pair":"BTCUSD","target_price":70000,"condition":"above","channels":["email"],"email":"test@test.com"}'

# Get all alerts
curl http://localhost:8001/api/alerts

# Get specific alert
curl http://localhost:8001/api/alerts/{alert_id}

# Delete alert
curl -X DELETE http://localhost:8001/api/alerts/{alert_id}
```

## Database Backup & Restore

### Create Backup
```bash
PGPASSWORD=mypassword pg_dump -h localhost -U myuser commodities > commodities_backup.sql
```

### Restore from Backup
```bash
PGPASSWORD=mypassword psql -h localhost -U myuser commodities < commodities_backup.sql
```

### Compressed Backup
```bash
PGPASSWORD=mypassword pg_dump -h localhost -U myuser commodities | gzip > commodities_backup.sql.gz
gunzip -c commodities_backup.sql.gz | PGPASSWORD=mypassword psql -h localhost -U myuser commodities
```

## PostgreSQL Service Commands

```bash
# Check status
sudo service postgresql status

# Start
sudo service postgresql start

# Stop
sudo service postgresql stop

# Restart
sudo service postgresql restart
```

## Troubleshooting

### Test Connection
```bash
source .venv/bin/activate
python init_db.py
```

### Check Database Size
```bash
PGPASSWORD=mypassword psql -h localhost -U myuser commodities -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;"
```

### View Table Sizes
```bash
PGPASSWORD=mypassword psql -h localhost -U myuser commodities -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Enable Query Logging (for debugging)

Update `.env`:
```env
SQL_ECHO=True
```

This will log all SQL queries to the console.

## Restore JSON Files (if needed)

```bash
# Restore legacy services
mv app/services/alerts_legacy.py app/services/alerts.py
mv app/services/price_history_legacy.py app/services/price_history.py
mv app/services/candle_storage_legacy.py app/services/candle_storage.py

# Remove database initialization from app/core/state.py
# Restart application
```

## Environment File Location
```
/home/here/Desktop/prompts/commodities/.env
```

## Documentation Files
- `docs/POSTGRESQL_SETUP.md` - Complete setup guide
- `docs/POSTGRESQL_MIGRATION_COMPLETE.md` - Migration summary
- `app/db/database.py` - Database configuration
- `app/models/models.py` - Database models
