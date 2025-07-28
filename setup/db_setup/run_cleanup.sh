#!/bin/bash

# Database cleanup script for Checking Engine
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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to execute SQL file
execute_sql() {
    local sql_file=$1
    local description=$2
    
    print_status "Executing $description..."
    
    if [ ! -f "$sql_file" ]; then
        print_error "SQL file not found: $sql_file"
        exit 1
    fi
    
    # Execute SQL file
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file"; then
        print_success "$description completed successfully"
    else
        print_error "Failed to execute $description"
        exit 1
    fi
}

# Function to test database connection
test_connection() {
    print_status "Testing database connection..."
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version();" > /dev/null 2>&1; then
        print_success "Database connection successful"
    else
        print_error "Cannot connect to database"
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Cleanup options:"
    echo "  --full    Full cleanup: Drop all tables and return to clean database"
    echo "  --data    Data cleanup: Delete all data but keep schema and tables"
    echo "  --help    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --full    # Remove all tables, indexes, functions"
    echo "  $0 --data    # Remove all data, keep schema"
}

# Function for confirmation
confirm_action() {
    local action=$1
    echo ""
    print_warning "⚠️  WARNING: This will $action"
    print_warning "⚠️  This action cannot be undone!"
    echo ""
    echo -n "Are you absolutely sure you want to continue? (type 'yes' to confirm): "
    read -r response
    if [[ "$response" != "yes" ]]; then
        print_status "Operation cancelled by user"
        exit 0
    fi
}

# Main execution
main() {
    echo "================================================================"
    echo "          Checking Engine Database Cleanup Script"
    echo "================================================================"
    echo ""
    
    # Parse command line arguments
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    case "$1" in
        --full)
            CLEANUP_TYPE="full"
            CLEANUP_DESCRIPTION="drop all tables and return database to clean state"
            CLEANUP_FILE="05_cleanup_full.sql"
            ;;
        --data)
            CLEANUP_TYPE="data"
            CLEANUP_DESCRIPTION="delete all data but preserve schema"
            CLEANUP_FILE="06_cleanup_data.sql"
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Invalid option: $1"
            show_usage
            exit 1
            ;;
    esac
    
    # Check if password is provided
    if [ -z "$DB_PASSWORD" ]; then
        print_warning "Database password not set in environment variable DB_PASSWORD"
        echo -n "Please enter database password for user '$DB_USER': "
        read -s DB_PASSWORD
        echo ""
        export DB_PASSWORD
    fi
    
    # Test connection first
    test_connection
    
    # Confirm action
    confirm_action "$CLEANUP_DESCRIPTION"
    
    echo ""
    print_status "Starting $CLEANUP_TYPE cleanup process..."
    echo ""
    
    # Execute cleanup
    execute_sql "$CLEANUP_FILE" "$CLEANUP_TYPE cleanup"
    
    echo ""
    echo "================================================================"
    print_success "Database $CLEANUP_TYPE cleanup completed successfully!"
    echo "================================================================"
    echo ""
    
    if [[ "$CLEANUP_TYPE" == "full" ]]; then
        print_status "Database is now in clean state (no tables)"
        print_status "You can run './run_setup.sh' to recreate the schema"
    else
        print_status "All data has been removed, schema preserved"
        print_status "You can insert new data or run sample data script"
    fi
}

# Run main function
main "$@" 