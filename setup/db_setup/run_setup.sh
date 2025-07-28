#!/bin/bash

# Database setup script for Checking Engine
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
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$sql_file" > /dev/null 2>&1; then
        print_success "$description completed successfully"
    else
        print_error "Failed to execute $description"
        print_error "Please check the SQL file: $sql_file"
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
        print_error "Please check your connection parameters:"
        echo "  Host: $DB_HOST"
        echo "  Port: $DB_PORT"
        echo "  Database: $DB_NAME"
        echo "  User: $DB_USER"
        exit 1
    fi
}

# Main execution
main() {
    echo "================================================================"
    echo "          Checking Engine Database Setup Script"
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
    
    # Test connection first
    test_connection
    
    echo ""
    print_status "Starting database setup process..."
    echo ""
    
    # Execute setup files in order
    execute_sql "03_create_extensions.sql" "PostgreSQL Extensions Setup"
    execute_sql "00_create_schema.sql" "Checking Engine Schema Creation"
    execute_sql "01_create_tables.sql" "Database Tables Creation"
    execute_sql "02_create_indexes.sql" "Performance Indexes Creation"
    
    # Ask if user wants to insert sample data
    echo ""
    echo -n "Do you want to insert sample test data? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        execute_sql "04_sample_data.sql" "Sample Data Insertion"
    else
        print_warning "Skipping sample data insertion"
    fi
    
    echo ""
    echo "================================================================"
    print_success "Database setup completed successfully!"
    echo "================================================================"
    echo ""
    print_status "Database is ready for Checking Engine operations"
    print_status "Connection details:"
    echo "  Host: $DB_HOST:$DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo ""
    print_status "You can now start the Checking Engine services"
}

# Run main function
main "$@" 