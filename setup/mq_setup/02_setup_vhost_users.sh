#!/bin/bash

# Phase 2: Setup Virtual Host and Users
# This script creates virtual host and all required users with secure passwords

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VHOST="/caldera_checking"
LOG_FILE="rabbitmq_phase2.log"
PASSWORDS_FILE="rabbitmq_passwords.txt"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[PHASE 2]${NC} $1"
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

# Function to generate secure password
generate_password() {
    openssl rand -base64 24 | tr -d "=+/" | cut -c1-20
}

# Check if running as root or with sudo
check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Check prerequisites
check_prerequisites() {
    # Check if RabbitMQ is running
    if ! systemctl is-active --quiet rabbitmq-server; then
        print_error "RabbitMQ service is not running. Run Phase 1 first."
        exit 1
    fi
    
    # Check if management plugin is enabled
    # if ! rabbitmq-plugins list | grep -q "rabbitmq_management.*E"; then
    #     print_error "Management plugin is not enabled. Run Phase 1 first."
    #     exit 1
    # fi
    
    print_success "Prerequisites check passed"
}

# Create virtual host
create_virtual_host() {
    print_status "Creating virtual host: $VHOST"
    
    rabbitmqctl add_vhost $VHOST >> $LOG_FILE 2>&1
    
    print_success "Virtual host created: $VHOST"
}

# Remove default guest user for security
remove_guest_user() {
    print_status "Removing default guest user for security..."
    
    rabbitmqctl delete_user guest >> $LOG_FILE 2>&1 || true
    
    print_success "Default guest user removed"
}

# Create users with passwords
create_users() {
    print_status "Creating RabbitMQ users..."
    
    # Generate passwords
    ADMIN_PASS=$(generate_password)
    PUBLISHER_PASS=$(generate_password)
    CONSUMER_PASS=$(generate_password)
    WORKER_PASS=$(generate_password)
    MONITOR_PASS=$(generate_password)
    DISPATCHER_PASS=$(generate_password)
    RESULT_PASS=$(generate_password)
    
    # Store passwords securely
    cat > $PASSWORDS_FILE << EOF
# RabbitMQ User Passwords
# Generated on: $(date)
# IMPORTANT: Store these passwords securely and update your application configurations

CALDERA_ADMIN_PASSWORD=$ADMIN_PASS
CALDERA_PUBLISHER_PASSWORD=$PUBLISHER_PASS
CHECKING_CONSUMER_PASSWORD=$CONSUMER_PASS
CHECKING_WORKER_PASSWORD=$WORKER_PASS
MONITOR_USER_PASSWORD=$MONITOR_PASS
CHECKING_DISPATCHER_PASSWORD=$DISPATCHER_PASS
CHECKING_RESULT_CONSUMER_PASSWORD=$RESULT_PASS

# Connection strings for applications:
RABBITMQ_ADMIN_URL=amqp://caldera_admin:$ADMIN_PASS@localhost:5672$VHOST
RABBITMQ_PUBLISHER_URL=amqp://caldera_publisher:$PUBLISHER_PASS@localhost:5672$VHOST
RABBITMQ_CONSUMER_URL=amqp://checking_consumer:$CONSUMER_PASS@localhost:5672$VHOST
RABBITMQ_WORKER_URL=amqp://checking_worker:$WORKER_PASS@localhost:5672$VHOST
RABBITMQ_MONITOR_URL=amqp://monitor_user:$MONITOR_PASS@localhost:5672$VHOST
RABBITMQ_DISPATCHER_URL=amqp://checking_dispatcher:$DISPATCHER_PASS@localhost:5672$VHOST
RABBITMQ_RESULT_CONSUMER_URL=amqp://checking_result_consumer:$RESULT_PASS@localhost:5672$VHOST
EOF
    
    chmod 600 $PASSWORDS_FILE
    
    # Create admin user
    print_status "Creating admin user..."
    rabbitmqctl add_user caldera_admin $ADMIN_PASS >> $LOG_FILE 2>&1
    rabbitmqctl set_user_tags caldera_admin administrator >> $LOG_FILE 2>&1
    rabbitmqctl set_permissions -p $VHOST caldera_admin ".*" ".*" ".*" >> $LOG_FILE 2>&1
    
    # Create publisher user
    print_status "Creating publisher user..."
    rabbitmqctl add_user caldera_publisher $PUBLISHER_PASS >> $LOG_FILE 2>&1
    rabbitmqctl set_user_tags caldera_publisher management >> $LOG_FILE 2>&1
    rabbitmqctl set_permissions -p $VHOST caldera_publisher \
        "^$" \
        "^caldera\.checking\.exchange$" \
        "^$" >> $LOG_FILE 2>&1
    
    # Create consumer user
    print_status "Creating consumer user..."
    rabbitmqctl add_user checking_consumer $CONSUMER_PASS >> $LOG_FILE 2>&1
    rabbitmqctl set_user_tags checking_consumer management >> $LOG_FILE 2>&1
    rabbitmqctl set_permissions -p $VHOST checking_consumer \
        "^$" \
        "^$" \
        "^caldera\.checking\.instructions$" >> $LOG_FILE 2>&1
    
    # Create worker user
    print_status "Creating worker user..."
    rabbitmqctl add_user checking_worker $WORKER_PASS >> $LOG_FILE 2>&1
    rabbitmqctl set_user_tags checking_worker management >> $LOG_FILE 2>&1
    rabbitmqctl set_permissions -p $VHOST checking_worker \
        "^$" \
        "^caldera\.checking\.(exchange|(api|agent)\.responses)$" \
        "^caldera\.checking\.(api\.tasks|agent\.tasks)$" >> $LOG_FILE 2>&1

    # 5. Dispatcher publisher user
    print_status "Creating dispatcher publisher user..."
    rabbitmqctl add_user checking_dispatcher $DISPATCHER_PASS >> $LOG_FILE 2>&1
    rabbitmqctl set_user_tags checking_dispatcher management >> $LOG_FILE 2>&1
    rabbitmqctl set_permissions -p $VHOST checking_dispatcher \
        "^$" \
        "^caldera\.checking\.exchange$" \
        "^$" >> $LOG_FILE 2>&1

    # 6. Result consumer user
    print_status "Creating result consumer user..."
    rabbitmqctl add_user checking_result_consumer $RESULT_PASS >> $LOG_FILE 2>&1
    rabbitmqctl set_user_tags checking_result_consumer management >> $LOG_FILE 2>&1
    rabbitmqctl set_permissions -p $VHOST checking_result_consumer \
        "^$" \
        "^$" \
        "^caldera\.checking\.(api|agent)\.responses$" >> $LOG_FILE 2>&1
    
    # Create monitor user
    print_status "Creating monitor user..."
    rabbitmqctl add_user monitor_user $MONITOR_PASS >> $LOG_FILE 2>&1
    rabbitmqctl set_user_tags monitor_user monitoring >> $LOG_FILE 2>&1
    rabbitmqctl set_permissions -p $VHOST monitor_user \
        "^$" \
        "^$" \
        "^caldera\.checking\..*$" >> $LOG_FILE 2>&1
    
    print_success "All users created with secure passwords"
    
    # Export passwords for next phases
    export ADMIN_PASS
    export PUBLISHER_PASS
    export CONSUMER_PASS
    export WORKER_PASS
    export MONITOR_PASS
    export DISPATCHER_PASS
    export RESULT_PASS
}

# Verify phase 2
verify_phase2() {
    print_status "Verifying Phase 2 setup..."
    
    # Check virtual host
    if ! rabbitmqctl list_vhosts | grep -q "$VHOST"; then
        print_error "Virtual host was not created"
        return 1
    fi
    
    # Check users
    local user_count=$(rabbitmqctl list_users | grep -c "caldera\|checking\|monitor" || true)
    if [ $user_count -ne 7 ]; then
        print_error "Not all users were created successfully"
        return 1
    fi
    
    print_success "Phase 2 completed successfully"
}

# Display user information
display_user_info() {
    echo
    print_success "Users and Virtual Host created!"
    echo
    print_status "Virtual Host: $VHOST"
    echo
    print_status "Created Users:"
    rabbitmqctl list_users
    echo
    print_status "User Permissions:"
    rabbitmqctl list_permissions -p $VHOST
    echo
    print_warning "Passwords saved to: $PASSWORDS_FILE"
    print_warning "Keep this file secure!"
}

# Main execution
main() {
    echo "======================================"
    echo "Phase 2: Setup Virtual Host and Users"
    echo "======================================"
    echo
    
    # Initialize log file
    echo "Phase 2 Log - $(date)" > $LOG_FILE
    
    print_status "Starting Phase 2: Virtual Host and Users setup..."
    
    # Check prerequisites
    check_privileges
    check_prerequisites
    
    # Execute phase 2 steps
    create_virtual_host
    remove_guest_user
    create_users
    
    # Verify phase 2
    verify_phase2
    
    # Display results
    display_user_info
    
    echo
    print_success "Phase 2 completed! Users and Virtual Host are ready."
    echo "Next step: Run 03_setup_exchanges_queues.sh"
    echo "Log file: $LOG_FILE"
    echo "Passwords file: $PASSWORDS_FILE"
}

# Run main function
main "$@" 