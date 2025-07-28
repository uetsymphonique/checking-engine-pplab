-- Database: caldera_purple
-- User: db_caldera  
-- Create dedicated schema for Checking Engine

-- Create schema owned by db_caldera
CREATE SCHEMA IF NOT EXISTS checking_engine AUTHORIZATION db_caldera;

-- Set search path to include our schema
ALTER USER db_caldera SET search_path TO checking_engine, public;

-- Grant all permissions on the schema
GRANT ALL PRIVILEGES ON SCHEMA checking_engine TO db_caldera;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA checking_engine TO db_caldera;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA checking_engine TO db_caldera;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA checking_engine TO db_caldera;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA checking_engine GRANT ALL PRIVILEGES ON TABLES TO db_caldera;
ALTER DEFAULT PRIVILEGES IN SCHEMA checking_engine GRANT ALL PRIVILEGES ON SEQUENCES TO db_caldera;
ALTER DEFAULT PRIVILEGES IN SCHEMA checking_engine GRANT ALL PRIVILEGES ON FUNCTIONS TO db_caldera;

-- Verify schema creation
SELECT schema_name, schema_owner 
FROM information_schema.schemata 
WHERE schema_name = 'checking_engine';

SELECT 'Schema checking_engine created successfully!' as status; 