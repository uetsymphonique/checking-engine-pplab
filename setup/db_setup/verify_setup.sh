#!/bin/bash

# Database verification script for Checking Engine
# Database: caldera_purple
# User: db_caldera

set -e  # Exit on any error

# Database connection parameters
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="caldera_purple"
DB_USER="db_caldera"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Function to execute SQL and return result
execute_sql_query() {
    local query=$1
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "$query" 2>/dev/null | xargs
}

# Function to test database connection
test_connection() {
    print_status "Testing database connection..."
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        print_success "Database connection successful"
        
        # Get PostgreSQL version
        version=$(execute_sql_query "SELECT version();")
        echo "  PostgreSQL Version: ${version:0:50}..."
        return 0
    else
        print_error "Cannot connect to database"
        echo "  Host: $DB_HOST:$DB_PORT"
        echo "  Database: $DB_NAME"
        echo "  User: $DB_USER"
        return 1
    fi
}

# Function to check if database exists
check_database() {
    print_status "Checking database existence..."
    
    db_exists=$(PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -lqt 2>/dev/null | cut -d \| -f 1 | grep -w "$DB_NAME" | wc -l)
    
    if [ "$db_exists" -eq 1 ]; then
        print_success "Database '$DB_NAME' exists"
        return 0
    else
        print_error "Database '$DB_NAME' does not exist"
        return 1
    fi
}

# Function to check schema
check_schema() {
    print_status "Checking checking_engine schema..."
    
    schema_exists=$(execute_sql_query "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'checking_engine';")
    if [ "$schema_exists" -eq 1 ]; then
        print_success "Schema 'checking_engine' exists"
        
        # Check ownership
        owner=$(execute_sql_query "SELECT schema_owner FROM information_schema.schemata WHERE schema_name = 'checking_engine';")
        echo "  → Owner: $owner"
        return 0
    else
        print_error "Schema 'checking_engine' does NOT exist"
        return 1
    fi
}

# Function to check extensions
check_extensions() {
    print_status "Checking PostgreSQL extensions..."
    
    local expected_extensions=("uuid-ossp" "pg_trgm" "btree_gin")
    local all_good=true
    
    for ext in "${expected_extensions[@]}"; do
        installed=$(execute_sql_query "SELECT COUNT(*) FROM pg_extension WHERE extname = '$ext';")
        if [ "$installed" -eq 1 ]; then
            print_success "Extension '$ext' is installed"
        else
            print_error "Extension '$ext' is NOT installed"
            all_good=false
        fi
    done
    
    return $all_good
}

# Function to check tables
check_tables() {
    print_status "Checking database tables..."
    
    local expected_tables=("operations" "execution_results" "detection_executions" "detection_results")
    local all_good=true
    
    for table in "${expected_tables[@]}"; do
        exists=$(execute_sql_query "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'checking_engine' AND table_name = '$table';")
        if [ "$exists" -eq 1 ]; then
            print_success "Table '$table' exists"
            
            # Get row count
            row_count=$(execute_sql_query "SELECT COUNT(*) FROM $table;")
            echo "  → Rows: $row_count"
        else
            print_error "Table '$table' does NOT exist"
            all_good=false
        fi
    done
    
    return $all_good
}

# Function to check indexes
check_indexes() {
    print_status "Checking database indexes..."
    
    index_count=$(execute_sql_query "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'checking_engine';")
    print_success "Found $index_count indexes"
    
    # List some important indexes
    local important_indexes=("idx_execution_results_operation" "idx_detection_executions_type_platform" "idx_detection_results_execution")
    
    for idx in "${important_indexes[@]}"; do
        exists=$(execute_sql_query "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'checking_engine' AND indexname = '$idx';")
        if [ "$exists" -eq 1 ]; then
            print_success "Index '$idx' exists"
        else
            print_warning "Index '$idx' is missing"
        fi
    done
}

# Function to check functions
check_functions() {
    print_status "Checking database functions..."
    
    func_exists=$(execute_sql_query "SELECT COUNT(*) FROM pg_proc WHERE proname = 'update_updated_at_column';")
    if [ "$func_exists" -eq 1 ]; then
        print_success "Function 'update_updated_at_column' exists"
    else
        print_warning "Function 'update_updated_at_column' is missing"
    fi
}

# Function to check permissions
check_permissions() {
    print_status "Checking user permissions..."
    
    # Test basic operations
    local test_passed=true
    
    # Try to create a test table
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "CREATE TEMP TABLE test_permissions (id int);" > /dev/null 2>&1; then
        print_success "CREATE permission: OK"
    else
        print_error "CREATE permission: FAILED"
        test_passed=false
    fi
    
    # Test if user can access existing tables (if they exist)
    if execute_sql_query "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'checking_engine';" > /dev/null 2>&1; then
        print_success "SELECT permission: OK"
    else
        print_error "SELECT permission: FAILED"
        test_passed=false
    fi
    
    return $test_passed
}

# Function to show detailed table info
show_table_details() {
    print_status "Detailed table information..."
    
    echo ""
    echo "Schema Overview:"
    echo "==============="
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            schemaname,
            tablename,
            tableowner,
            hasindexes,
            hasrules,
            hastriggers
        FROM pg_tables 
        WHERE schemaname = 'checking_engine'
        ORDER BY tablename;
    " 2>/dev/null || echo "No tables found in checking_engine schema"
    
    echo ""
    echo "Extensions:"
    echo "==========="
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        SELECT 
            extname as extension_name,
            extversion as version
        FROM pg_extension 
        ORDER BY extname;
    " 2>/dev/null || echo "No extensions found"
}

# Function to suggest fixes
suggest_fixes() {
    echo ""
    echo "================================================================"
    echo "                    TROUBLESHOOTING SUGGESTIONS"
    echo "================================================================"
    echo ""
    
    print_status "If tables are missing, run setup:"
    echo "  cd $(pwd)"
    echo "  ./run_setup.sh"
    echo ""
    
    print_status "If permissions are wrong, check database grants:"
    echo "  GRANT CREATE ON DATABASE $DB_NAME TO $DB_USER;"
    echo "  GRANT USAGE, CREATE ON SCHEMA public TO $DB_USER;"
    echo ""
    
    print_status "If extensions are missing, install contrib:"
    echo "  sudo apt-get install postgresql-contrib    # Ubuntu/Debian"
    echo "  sudo yum install postgresql-contrib        # CentOS/RHEL"
    echo ""
    
    print_status "Manual table creation:"
    echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f 01_create_tables.sql"
}

# Main verification function
main() {
    echo "================================================================"
    echo "          Checking Engine Database Verification"
    echo "================================================================"
    echo ""
    
    # Check if password is provided
    if [ -z "$DB_PASSWORD" ]; then
        print_warning "Database password not set in environment variable DB_PASSWORD"
        echo -n "Please enter database password for user '$DB_USER': "
        read -s DB_PASSWORD
        echo ""
        export DB_PASSWORD
    fi
    
    local overall_status=0
    
    # Run all checks
    echo "Running verification checks..."
    echo ""
    
    check_database || overall_status=1
    test_connection || overall_status=1
    check_permissions || overall_status=1
    check_schema || overall_status=1
    check_extensions || overall_status=1
    check_tables || overall_status=1
    check_indexes || overall_status=1
    check_functions || overall_status=1
    
    echo ""
    show_table_details
    
    echo ""
    echo "================================================================"
    if [ $overall_status -eq 0 ]; then
        print_success "All checks passed! Database setup is complete and working."
        echo ""
        print_status "Your database is ready for Checking Engine operations."
        print_status "You can now:"
        echo "  - Connect DBeaver to monitor data"
        echo "  - Start the Checking Engine backend"
        echo "  - Configure Caldera to send messages"
    else
        print_error "Some checks failed. Database setup needs attention."
        suggest_fixes
    fi
    echo "================================================================"
    
    return $overall_status
}

# Run main function
main "$@" 