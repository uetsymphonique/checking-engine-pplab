-- Database: caldera_purple
-- User: db_caldera
-- Full Cleanup Script - Drops all tables and returns database to clean state

-- Set search path to use checking_engine schema
SET search_path TO checking_engine, public;

-- Disable foreign key checks temporarily to avoid dependency issues
SET session_replication_role = replica;

-- Drop tables in reverse dependency order to handle foreign keys
DROP TABLE IF EXISTS detection_results CASCADE;
DROP TABLE IF EXISTS detection_executions CASCADE;
DROP TABLE IF EXISTS execution_results CASCADE;
DROP TABLE IF EXISTS operations CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Drop triggers (if any remain)
DROP TRIGGER IF EXISTS update_operations_updated_at ON operations;

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- Optionally drop the entire schema (uncomment if you want to remove schema completely)
-- DROP SCHEMA IF EXISTS checking_engine CASCADE;

-- Optionally drop extensions (uncomment if you want to remove them completely)
-- Note: These extensions might be used by other applications, so be careful
-- DROP EXTENSION IF EXISTS "uuid-ossp";
-- DROP EXTENSION IF EXISTS "pg_trgm";
-- DROP EXTENSION IF EXISTS "btree_gin";

-- Verify cleanup
SELECT 
    tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('operations', 'execution_results', 'detection_executions', 'detection_results');

-- Should return no rows if cleanup was successful

PRINT 'Full cleanup completed - all tables and functions removed!'; 