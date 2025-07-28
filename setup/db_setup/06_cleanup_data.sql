-- Database: caldera_purple
-- User: db_caldera
-- Data Cleanup Script - Removes all data but keeps tables, indexes, and schema

-- Set search path to use checking_engine schema
SET search_path TO checking_engine, public;

-- Disable triggers temporarily to speed up deletion
SET session_replication_role = replica;

-- Delete data in reverse dependency order to handle foreign keys
DELETE FROM detection_results;
DELETE FROM detection_executions;
DELETE FROM execution_results;
DELETE FROM operations;

-- Re-enable triggers
SET session_replication_role = DEFAULT;

-- Reset sequences (if any auto-increment fields were used)
-- Note: Our schema uses UUIDs, so no sequences to reset

-- Verify data cleanup
SELECT 
    schemaname,
    tablename,
    n_tup_ins AS total_inserts,
    n_tup_upd AS total_updates,
    n_tup_del AS total_deletes,
    n_live_tup AS current_rows,
    n_dead_tup AS dead_rows
FROM pg_stat_user_tables 
WHERE tablename IN ('operations', 'execution_results', 'detection_executions', 'detection_results')
ORDER BY tablename;

-- Get row counts for verification
SELECT 'operations' as table_name, COUNT(*) as row_count FROM operations
UNION ALL
SELECT 'execution_results', COUNT(*) FROM execution_results
UNION ALL  
SELECT 'detection_executions', COUNT(*) FROM detection_executions
UNION ALL
SELECT 'detection_results', COUNT(*) FROM detection_results
ORDER BY table_name;

-- Vacuum tables to reclaim space after large deletions
VACUUM ANALYZE operations;
VACUUM ANALYZE execution_results;
VACUUM ANALYZE detection_executions;
VACUUM ANALYZE detection_results;

PRINT 'Data cleanup completed - all data removed, schema preserved!'; 