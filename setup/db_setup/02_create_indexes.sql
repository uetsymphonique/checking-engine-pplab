-- Database: caldera_purple
-- User: db_caldera
-- PostgreSQL Indexes Creation Script for Checking Engine Performance

-- Set search path to use checking_engine schema
SET search_path TO checking_engine, public;

-- Primary lookup patterns
CREATE INDEX IF NOT EXISTS idx_execution_results_operation 
ON execution_results(operation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_execution_results_link 
ON execution_results(link_id);

CREATE INDEX IF NOT EXISTS idx_detection_executions_operation 
ON detection_executions(operation_id, status);

CREATE INDEX IF NOT EXISTS idx_detection_executions_execution_result 
ON detection_executions(execution_result_id);

CREATE INDEX IF NOT EXISTS idx_detection_results_execution 
ON detection_results(detection_execution_id);

-- Detection type and platform filtering
CREATE INDEX IF NOT EXISTS idx_detection_executions_type_platform 
ON detection_executions(detection_type, detection_platform);

CREATE INDEX IF NOT EXISTS idx_detection_executions_status 
ON detection_executions(status, started_at);

-- JSONB search optimization (requires btree_gin extension)
CREATE INDEX IF NOT EXISTS idx_detection_config_gin 
ON detection_executions USING gin(detection_config);

CREATE INDEX IF NOT EXISTS idx_detection_results_gin 
ON detection_results USING gin(parsed_results);

CREATE INDEX IF NOT EXISTS idx_raw_message_gin 
ON execution_results USING gin(raw_message);

-- Time-based queries
CREATE INDEX IF NOT EXISTS idx_execution_results_time 
ON execution_results(agent_reported_time);

CREATE INDEX IF NOT EXISTS idx_detection_results_time 
ON detection_results(result_timestamp);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_detection_executions_status_time 
ON detection_executions(status, started_at, completed_at);

CREATE INDEX IF NOT EXISTS idx_execution_results_agent 
ON execution_results(agent_paw, agent_host, created_at);

-- Unique constraint indexes
CREATE UNIQUE INDEX IF NOT EXISTS idx_operations_operation_id 
ON operations(operation_id);

CREATE INDEX IF NOT EXISTS idx_execution_results_link_unique 
ON execution_results(link_id, operation_id);

PRINT 'Indexes created successfully!'; 