-- Database: caldera_purple
-- User: db_caldera
-- Sample Data Script for Testing Checking Engine

-- Set search path to use checking_engine schema
SET search_path TO checking_engine, public;

-- Sample operation
INSERT INTO operations (operation_id, name, operation_start, metadata) VALUES
(
    '550e8400-e29b-41d4-a716-446655440000',
    'Test Operation',
    NOW() - INTERVAL '1 hour',
    '{"description": "Sample operation for testing", "operator": "test_user"}'::jsonb
) ON CONFLICT (operation_id) DO NOTHING;

-- Sample execution result
INSERT INTO execution_results (
    operation_id, 
    agent_host, 
    agent_paw, 
    link_id, 
    command, 
    pid, 
    status, 
    result_data, 
    agent_reported_time, 
    link_state,
    raw_message
) VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'test-host',
    'test-paw-123',
    '660e8400-e29b-41d4-a716-446655440001',
    'whoami',
    1234,
    0,
    '{"stdout": "testuser\n", "stderr": "", "exit_code": "0"}'::jsonb,
    NOW() - INTERVAL '30 minutes',
    'SUCCESS',
    '{"timestamp": "2025-01-23T10:00:00Z", "message_type": "link_result", "operation": "Test Operation"}'::jsonb
);

-- Sample detection executions
INSERT INTO detection_executions (
    execution_result_id,
    operation_id,
    detection_type,
    detection_platform,
    detection_config,
    status,
    started_at,
    completed_at,
    retry_count,
    max_retries
) VALUES 
(
    (SELECT id FROM execution_results WHERE link_id = '660e8400-e29b-41d4-a716-446655440001'),
    '550e8400-e29b-41d4-a716-446655440000',
    'api',
    'cym',
    '{
        "command": "search index=security eventCode=4624 user=testuser",
        "endpoint": "https://siem.test.com/api/search",
        "timeout": 30,
        "headers": {"Authorization": "Bearer test123"}
    }'::jsonb,
    'completed',
    NOW() - INTERVAL '25 minutes',
    NOW() - INTERVAL '24 minutes',
    0,
    3
),
(
    (SELECT id FROM execution_results WHERE link_id = '660e8400-e29b-41d4-a716-446655440001'),
    '550e8400-e29b-41d4-a716-446655440000',
    'linux',
    'sh',
    '{
        "command": "journalctl -u ssh --since \"30 minutes ago\" | grep testuser",
        "executor": "sh",
        "target_agent": "linux-agent-test",
        "timeout": 30
    }'::jsonb,
    'completed',
    NOW() - INTERVAL '23 minutes',
    NOW() - INTERVAL '22 minutes',
    0,
    3
);

-- Sample detection results
INSERT INTO detection_results (
    detection_execution_id,
    detected,
    raw_response,
    parsed_results,
    result_timestamp,
    result_source,
    metadata
) VALUES 
(
    (SELECT id FROM detection_executions WHERE detection_platform = 'cym' LIMIT 1),
    true,
    '{
        "events": [
            {
                "timestamp": "2025-01-23T10:00:15Z",
                "event_id": 4624,
                "user": "testuser",
                "source_ip": "192.168.1.100"
            }
        ],
        "total_count": 1
    }'::jsonb,
    '{
        "detected": true,
        "confidence": 0.95,
        "events_found": 1,
        "detection_rule": "User Login Detection"
    }'::jsonb,
    NOW() - INTERVAL '24 minutes',
    'siem.test.com',
    '{"confidence": 0.95, "severity": "medium"}'::jsonb
),
(
    (SELECT id FROM detection_executions WHERE detection_platform = 'sh' LIMIT 1),
    false,
    '{
        "stdout": "",
        "stderr": "",
        "exit_code": 0
    }'::jsonb,
    '{
        "detected": false,
        "events_found": 0,
        "detection_rule": "SSH Log Analysis"
    }'::jsonb,
    NOW() - INTERVAL '22 minutes',
    'linux-agent-test',
    '{"confidence": 0.8, "severity": "low"}'::jsonb
);

-- Verify sample data
SELECT 
    o.name as operation_name,
    er.command,
    er.agent_host,
    de.detection_type,
    de.detection_platform,
    de.status as detection_status,
    dr.detected,
    dr.result_timestamp
FROM operations o
JOIN execution_results er ON o.operation_id = er.operation_id
JOIN detection_executions de ON er.id = de.execution_result_id
LEFT JOIN detection_results dr ON de.id = dr.detection_execution_id
ORDER BY er.created_at, dr.result_timestamp;

PRINT 'Sample data inserted successfully!'; 