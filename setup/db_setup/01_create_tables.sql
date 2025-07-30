-- Database: caldera_purple
-- User: db_caldera
-- PostgreSQL Tables Creation Script for Checking Engine

-- Set search path to use checking_engine schema
SET search_path TO checking_engine, public;

-- Enable required extensions first
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. operations table
-- Stores information about Caldera operations
CREATE TABLE IF NOT EXISTS operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    operation_id UUID NOT NULL UNIQUE,  -- Original Caldera operation ID
    operation_start TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb  -- Additional operation context
);

COMMENT ON TABLE operations IS 'MITRE Caldera operations metadata';
COMMENT ON COLUMN operations.operation_id IS 'Original operation ID from Caldera';
COMMENT ON COLUMN operations.metadata IS 'Extensible JSON field for additional operation data';

-- 2. execution_results table
-- Stores RED team command execution results from Caldera agents
CREATE TABLE IF NOT EXISTS execution_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    operation_id UUID NOT NULL REFERENCES operations(operation_id),
    agent_host VARCHAR(255),
    agent_paw VARCHAR(255),
    link_id UUID NOT NULL,  -- Caldera link ID
    command TEXT,
    pid INTEGER,
    status INTEGER,
    result_data JSONB,  -- Contains stdout, stderr, exit_code
    agent_reported_time TIMESTAMPTZ,
    link_state VARCHAR(50),  -- SUCCESS, FAILED, etc.
    created_at TIMESTAMPTZ DEFAULT NOW(),
    raw_message JSONB  -- Complete original message from queue
);

COMMENT ON TABLE execution_results IS 'RED team command execution results from Caldera';
COMMENT ON COLUMN execution_results.link_id IS 'Unique link identifier from Caldera';
COMMENT ON COLUMN execution_results.result_data IS 'JSON containing stdout, stderr, exit_code';
COMMENT ON COLUMN execution_results.raw_message IS 'Complete original message from RabbitMQ';

-- 3. detection_executions table
-- Manages the execution of detection queries/commands across different platforms
CREATE TABLE IF NOT EXISTS detection_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_result_id UUID NOT NULL REFERENCES execution_results(id),
    operation_id UUID NOT NULL REFERENCES operations(operation_id),
    detection_type VARCHAR(50) NOT NULL,  -- 'api', 'windows', 'linux', 'darwin'
    detection_platform VARCHAR(50) NOT NULL,  -- 'cym', 'ajant', 'psh', 'pwsh', 'sh'
    detection_config JSONB NOT NULL,  -- Platform-specific configuration
    status VARCHAR(50) DEFAULT 'pending',  -- pending, running, completed, failed, cancelled
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    execution_metadata JSONB DEFAULT '{}'::jsonb,  -- Timing, errors, context
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE detection_executions IS 'BLUE team detection execution tracking';
COMMENT ON COLUMN detection_executions.detection_type IS 'Platform category: api, windows, linux, darwin';
COMMENT ON COLUMN detection_executions.detection_platform IS 'Specific platform: cym, ajant, psh, sh, etc.';
COMMENT ON COLUMN detection_executions.detection_config IS 'Platform-specific detection configuration';
COMMENT ON COLUMN detection_executions.execution_metadata IS 'Execution context, errors, performance metrics';

-- 4. detection_results table
-- Stores BLUE team detection results from security controls
CREATE TABLE IF NOT EXISTS detection_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_execution_id UUID NOT NULL REFERENCES detection_executions(id),
    detected BOOLEAN,
    raw_response JSONB,  -- Raw response from API/command
    parsed_results JSONB,  -- Structured/parsed detection results
    result_timestamp TIMESTAMPTZ DEFAULT NOW(),
    result_source VARCHAR(255),  -- API endpoint, hostname, etc.
    metadata JSONB DEFAULT '{}'::jsonb,  -- Confidence, severity, rules matched
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE detection_results IS 'BLUE team detection results from security controls';
COMMENT ON COLUMN detection_results.detected IS 'Whether the activity was detected by security control';
COMMENT ON COLUMN detection_results.raw_response IS 'Unprocessed response from detection platform';
COMMENT ON COLUMN detection_results.parsed_results IS 'Structured detection data for analysis';
COMMENT ON COLUMN detection_results.result_source IS 'Source system that provided the detection result';
COMMENT ON COLUMN detection_results.metadata IS 'Additional context: confidence, severity, etc.';

-- Create constraints and check constraints
ALTER TABLE detection_executions 
ADD CONSTRAINT chk_detection_type 
CHECK (detection_type IN ('api', 'windows', 'linux', 'darwin'));

ALTER TABLE detection_executions 
ADD CONSTRAINT chk_status 
CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled'));

ALTER TABLE detection_executions 
ADD CONSTRAINT chk_retry_count 
CHECK (retry_count >= 0 AND retry_count <= max_retries);

-- Create updated_at trigger for operations table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_operations_updated_at 
    BEFORE UPDATE ON operations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

SELECT 'Tables created successfully!' as status; 