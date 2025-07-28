# Database Setup for Checking Engine

This directory contains database setup scripts for the Checking Engine PostgreSQL database.

## Prerequisites

- PostgreSQL server running on localhost:5432
- Database `caldera_purple` already created
- User `db_caldera` with appropriate permissions
- `psql` command-line tool installed

## Setup Files

| File | Description |
|------|-------------|
| `01_create_tables.sql` | Creates all database tables and constraints |
| `02_create_indexes.sql` | Creates performance indexes |
| `03_create_extensions.sql` | Installs required PostgreSQL extensions |
| `04_sample_data.sql` | Inserts sample test data (optional) |
| `05_cleanup_full.sql` | Drops all tables and returns database to clean state |
| `06_cleanup_data.sql` | Deletes all data but preserves schema |
| `run_setup.sh` | Automated setup script |
| `run_cleanup.sh` | Automated cleanup script with options |

## Quick Setup

### Option 1: Automated Setup (Recommended)

```bash
cd setup/db_setup/
chmod +x run_setup.sh
./run_setup.sh
```

The script will:
1. Test database connection
2. Install PostgreSQL extensions
3. Create all tables and constraints
4. Create performance indexes
5. Optionally insert sample data

### Option 2: Manual Setup

```bash
# Set environment variable (optional)
export DB_PASSWORD="your_password"

# Run each script manually
psql -h localhost -p 5432 -U db_caldera -d caldera_purple -f 03_create_extensions.sql
psql -h localhost -p 5432 -U db_caldera -d caldera_purple -f 01_create_tables.sql
psql -h localhost -p 5432 -U db_caldera -d caldera_purple -f 02_create_indexes.sql

# Optional: Insert sample data
psql -h localhost -p 5432 -U db_caldera -d caldera_purple -f 04_sample_data.sql
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_PASSWORD` | Database password for user `db_caldera` | (prompted if not set) |
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `DB_NAME` | Database name | caldera_purple |
| `DB_USER` | Database user | db_caldera |

## Database Cleanup

### Option 1: Full Cleanup (Drop All Tables)

Removes all tables, indexes, functions and returns database to clean state:

```bash
cd setup/db_setup/
chmod +x run_cleanup.sh
./run_cleanup.sh --full
```

**Warning**: This completely removes all schema and data!

### Option 2: Data Cleanup (Keep Schema)

Removes all data but preserves tables, indexes, and schema:

```bash
cd setup/db_setup/
./run_cleanup.sh --data
```

### Manual Cleanup

```bash
# Full cleanup
psql -h localhost -p 5432 -U db_caldera -d caldera_purple -f 05_cleanup_full.sql

# Data only cleanup
psql -h localhost -p 5432 -U db_caldera -d caldera_purple -f 06_cleanup_data.sql
```

## Verification

After setup, verify the installation:

```sql
-- Check tables are created
\dt

-- Check extensions are installed
SELECT extname FROM pg_extension;

-- Check sample data (if inserted)
SELECT COUNT(*) FROM operations;
SELECT COUNT(*) FROM execution_results;
SELECT COUNT(*) FROM detection_executions;
SELECT COUNT(*) FROM detection_results;
```

## Database Schema Overview

The database consists of 4 main tables:

1. **operations** - Caldera operation metadata
2. **execution_results** - RED team command execution results
3. **detection_executions** - BLUE team detection execution tracking
4. **detection_results** - BLUE team detection results

For detailed schema documentation, see `../../docs/db.md`.

## Troubleshooting

### Common Issues

**Connection Failed**
```
Error: Cannot connect to database
```
- Check PostgreSQL service is running
- Verify database `caldera_purple` exists
- Verify user `db_caldera` has correct permissions
- Check password is correct

**Permission Denied**
```
Error: permission denied for database caldera_purple
```
- Ensure user `db_caldera` has CREATE permissions on the database:
```sql
GRANT CREATE ON DATABASE caldera_purple TO db_caldera;
GRANT USAGE, CREATE ON SCHEMA public TO db_caldera;
```

**Extension Installation Failed**
```
Error: extension "uuid-ossp" is not available
```
- Install PostgreSQL contrib package:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-contrib
```

**Script Execution Failed**
```
Error: Failed to execute Database Tables Creation
```
- Check PostgreSQL logs for detailed error information
- Ensure all prerequisites are met
- Try running individual SQL files manually

### Manual Cleanup

**Recommended**: Use the automated cleanup scripts instead:

```bash
# Full cleanup (removes all tables)
./run_cleanup.sh --full

# Data cleanup (removes data, keeps schema)  
./run_cleanup.sh --data
```

**Alternative**: Manual SQL cleanup:

```sql
-- Connect as db_caldera user
\c caldera_purple

-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS detection_results CASCADE;
DROP TABLE IF EXISTS detection_executions CASCADE;
DROP TABLE IF EXISTS execution_results CASCADE;
DROP TABLE IF EXISTS operations CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column();
```

## Security Notes

- Store database password in environment variables, not in scripts
- Use connection pooling in production
- Consider SSL/TLS for database connections
- Implement proper backup and recovery procedures
- Monitor database performance and logs

## Next Steps

After successful database setup:

1. Configure the Checking Engine backend application
2. Set up RabbitMQ message broker
3. Configure Caldera plugin to publish messages
4. Test end-to-end data flow

For more information, see the main documentation in `../docs/`. 