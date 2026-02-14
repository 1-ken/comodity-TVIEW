# PostgreSQL Configuration Guide

## Overview
This application has been configured to use **PostgreSQL** for all persistent data writes instead of JSON files.

### What's Stored in PostgreSQL
- **Alerts** - Price alerts with configurations and status
- **Price History** - Historical price snapshots for replay functionality
- **Candles** - OHLC candle data for multiple timeframes (1m, 5m, 15m, 30m, 1h, 4h, daily, 3d)

## Quick Setup

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from: https://www.postgresql.org/download/windows/

### 2. Create Database and User

The easiest way is to use the built-in superuser `postgres`:

```bash
# Switch to postgres user
sudo -u postgres psql

# Then in the psql prompt, create database:
CREATE DATABASE commodities;

# Exit psql
\q
```

**Or directly:**
```bash
sudo -u postgres createdb commodities
```

### 3. Configure Connection String

Edit `.env` file in the project root:

```env
# PostgreSQL Database Configuration
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/commodities

# Optional: Enable SQL query logging (set to "True" to enable)
SQL_ECHO=False
```

**Components:**
- `postgres` - username
- `postgres` - password (default for PostgreSQL)
- `localhost` - host (change if DB is on different machine)
- `5432` - port (default PostgreSQL port)
- `commodities` - database name

### 4. Initialize Database Tables

```bash
# Activate virtual environment
source .venv/bin/activate

# Initialize database (creates all tables)
python init_db.py
```

Expected output:
```
============================================================
PostgreSQL Database Initialization
============================================================

Testing database connection...
✓ Database connection successful

Initializing database tables...
✓ Database initialized successfully!

Tables created:
  - alerts
  - price_history
  - candles

============================================================
Database is ready for use!
============================================================
```

### 5. Start the Application

```bash
source .venv/bin/activate
python run.py
```

## Database Connection Troubleshooting

### Error: "connection refused"
**Problem:** PostgreSQL not running or not on the specified host/port

**Solution:**
```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Start PostgreSQL if needed
sudo service postgresql start

# On macOS:
brew services start postgresql
```

### Error: "authentication failed"
**Problem:** Wrong username/password in DATABASE_URL

**Solution:**
```bash
# List PostgreSQL users
sudo -u postgres psql -c "\du"

# Reset password for postgres user
sudo -u postgres psql
ALTER USER postgres WITH PASSWORD 'new_password';
\q
```

### Error: "database does not exist"
**Problem:** Database 'commodities' not created

**Solution:**
```bash
# Create the database
sudo -u postgres createdb commodities

# Verify it was created
sudo -u postgres psql -c "\l"
```

### Cannot connect from Python
**Problem:** psycopg2 not installed or connection string malformed

**Solution:**
```bash
# Reinstall dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Test connection
python -c "from app.db.database import test_connection; test_connection()"
```

## Verify Data Persistence

After running the application, verify data is being stored:

```bash
# Connect to database
sudo -u postgres psql commodities

# List all alerts
SELECT id, pair, target_price, condition, status FROM alerts;

# Count price history records
SELECT COUNT(*) as snapshot_count FROM price_history;

# Count candles
SELECT COUNT(*) as candle_count FROM candles;

# Exit
\q
```

## Performance Indexes

The database has been configured with indexes for optimal query performance:

- `alerts`: Indexed on `(pair, status)` for fast alert lookup
- `price_history`: Indexed on `timestamp` for range queries
- `candles`: Indexed on `(pair, timeframe, timestamp)` for efficient candle retrieval

## Migration from JSON

The application maintains backward compatibility. Old JSON files are backed up as:
- `storage/alerts_legacy.json` → JSON-based alerts (archived)
- `storage/price_history_legacy.json` → JSON-based history (archived)
- Services: `alerts_legacy.py`, `price_history_legacy.py`, `candle_storage_legacy.py`

To use the old JSON-based system, rename these files back and update imports in `app/core/state.py`.

## Backup and Restore

### Backup PostgreSQL Database

```bash
# Create backup file
sudo -u postgres pg_dump commodities > commodities_backup.sql

# Compressed backup
sudo -u postgres pg_dump commodities | gzip > commodities_backup.sql.gz
```

### Restore PostgreSQL Database

```bash
# From backup
sudo -u postgres psql commodities < commodities_backup.sql

# From compressed backup
gunzip -c commodities_backup.sql.gz | sudo -u postgres psql commodities
```

## Production Considerations

1. **Use strong passwords** instead of default 'postgres'
2. **Enable SSL connections** for remote databases
3. **Set up regular backups** using cron jobs
4. **Monitor database size** and perform maintenance
5. **Use connection pooling** for high-traffic scenarios
6. **Enable query logging** for debugging (set `SQL_ECHO=True` in .env)

## Key Environment Variables

```env
# Connection
DATABASE_URL=postgresql://user:password@host:port/dbname

# Optional: Enable detailed SQL logging
SQL_ECHO=False

# Application
LOG_LEVEL=INFO
```

## Related Files

- `app/db/database.py` - Database configuration and session management
- `app/models/models.py` - SQLAlchemy ORM models
- `app/services/alerts.py` - Alerts service (PostgreSQL)
- `app/services/price_history.py` - Price history service (PostgreSQL)
- `app/services/candle_storage.py` - Candle storage service (PostgreSQL)
- `init_db.py` - Database initialization script
- `.env` - Environment configuration file

## Support

If you encounter issues:

1. Check `.env` for correct DATABASE_URL
2. Verify PostgreSQL is running
3. Review application logs for error messages
4. Test connection: `python init_db.py`
5. Check PostgreSQL logs: `/var/log/postgresql/` (Linux)
