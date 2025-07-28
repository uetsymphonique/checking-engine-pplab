-- Database: caldera_purple
-- User: db_caldera
-- PostgreSQL Extensions Setup Script for Checking Engine

-- Required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- UUID generation functions
CREATE EXTENSION IF NOT EXISTS "pg_trgm";      -- Text similarity search
CREATE EXTENSION IF NOT EXISTS "btree_gin";    -- Optimized GIN indexes for better JSONB performance

-- Optional extensions (comment out if not available)
-- CREATE EXTENSION IF NOT EXISTS "pg_cron";      -- Scheduled tasks (requires superuser)
-- CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";  -- Query performance monitoring (requires superuser)

-- Verify extensions are installed
SELECT 
    extname AS extension_name,
    extversion AS version
FROM pg_extension 
WHERE extname IN ('uuid-ossp', 'pg_trgm', 'btree_gin', 'pg_cron', 'pg_stat_statements')
ORDER BY extname;

PRINT 'Extensions setup completed!'; 