#!/bin/bash

# Phase 3: Setup Exchanges and Queues
# This script creates exchanges, queues, and bindings

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VHOST="/caldera_checking"
LOG_FILE="rabbitmq_phase3.log"
PASSWORDS_FILE="rabbitmq_passwords.txt"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[PHASE 3]${NC} $1"
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

# Check if running as root or with sudo
check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Load passwords from file
load_passwords() {
    if [ ! -f "$PASSWORDS_FILE" ]; then
        print_error "Passwords file not found: $PASSWORDS_FILE"
        print_error "Please run Phase 2 first to create users and passwords"
        exit 1
    fi
    
    # Source the passwords file
    source $PASSWORDS_FILE
    
    # Set variables from the loaded environment
    ADMIN_PASS=$CALDERA_ADMIN_PASSWORD
    
    if [ -z "$ADMIN_PASS" ]; then
        print_error "Admin password not found in passwords file"
        exit 1
    fi
    
    print_success "Passwords loaded successfully"
}

# Check prerequisites
check_prerequisites() {
    # Check if RabbitMQ is running
    if ! systemctl is-active --quiet rabbitmq-server; then
        print_error "RabbitMQ service is not running. Run Phase 1 first."
        exit 1
    fi
    
    # Check if virtual host exists
    if ! rabbitmqctl list_vhosts | grep -q "$VHOST"; then
        print_error "Virtual host $VHOST does not exist. Run Phase 2 first."
        exit 1
    fi
    
    # Check if admin user exists
    if ! rabbitmqctl list_users | grep -q "caldera_admin"; then
        print_error "Admin user does not exist. Run Phase 2 first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Create exchanges and queues
create_exchanges_and_queues() {
    print_status "Creating exchanges and queues..."
    
    local admin_user="caldera_admin"
    
    # Create exchange
    print_status "Creating main exchange..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare exchange \
        name=caldera.checking.exchange type=topic durable=true >> $LOG_FILE 2>&1
    
    # Create queues
    print_status "Creating instructions queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare queue \
        name=caldera.checking.instructions durable=true >> $LOG_FILE 2>&1
    
    print_status "Creating API responses queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare queue \
        name=caldera.checking.api.responses durable=true >> $LOG_FILE 2>&1
    
    print_status "Creating agent responses queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare queue \
        name=caldera.checking.agent.responses durable=true >> $LOG_FILE 2>&1

    # New tasks queues
    print_status "Creating API tasks queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare queue \
        name=caldera.checking.api.tasks durable=true >> $LOG_FILE 2>&1

    print_status "Creating agent tasks queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare queue \
        name=caldera.checking.agent.tasks durable=true >> $LOG_FILE 2>&1
    
    print_success "Exchanges and queues created"
}

# Create bindings
create_bindings() {
    print_status "Creating queue bindings..."
    
    local admin_user="caldera_admin"
    
    # Binding for instructions queue (Red Team execution results)
    print_status "Creating binding for instructions queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare binding \
        source=caldera.checking.exchange \
        destination=caldera.checking.instructions \
        routing_key=caldera.execution.result >> $LOG_FILE 2>&1
    
    # Binding for API responses queue (SIEM/API detection results)
    print_status "Creating binding for API responses queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare binding \
        source=caldera.checking.exchange \
        destination=caldera.checking.api.responses \
        routing_key=checking.api.response >> $LOG_FILE 2>&1
    
    # Binding for agent responses queue (Agent detection results)
    print_status "Creating binding for agent responses queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare binding \
        source=caldera.checking.exchange \
        destination=caldera.checking.agent.responses \
        routing_key=checking.agent.response >> $LOG_FILE 2>&1

    # Binding for API tasks queue (dispatcher -> API worker)
    print_status "Creating binding for API tasks queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare binding \
        source=caldera.checking.exchange \
        destination=caldera.checking.api.tasks \
        routing_key=checking.api.task >> $LOG_FILE 2>&1

    # Binding for agent tasks queue (dispatcher -> agent worker)
    print_status "Creating binding for agent tasks queue..."
    rabbitmqadmin -u $admin_user -p $ADMIN_PASS -V $VHOST declare binding \
        source=caldera.checking.exchange \
        destination=caldera.checking.agent.tasks \
        routing_key=checking.agent.task >> $LOG_FILE 2>&1
    
    print_success "Queue bindings created successfully"
}

# Test basic functionality
test_functionality() {
    print_status "Testing basic RabbitMQ functionality..."
    
    # Test message publishing and routing
    local test_message='{"test": "phase3_verification", "timestamp": "'$(date -Iseconds)'"}'
    
    # Publish test message
    print_status "Publishing test message..."
    if rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST publish \
        exchange=caldera.checking.exchange \
        routing_key=caldera.execution.result \
        payload="$test_message" >> $LOG_FILE 2>&1; then
        
        # Check if message was queued
        sleep 1  # Small delay for message processing
        local message_count=$(rabbitmqctl list_queues -p $VHOST name messages | grep caldera.checking.instructions | awk '{print $2}')
        
        if [ "$message_count" -gt 0 ]; then
            print_success "Message publishing test passed"
            
            # Consume the test message to clean up
            print_status "Cleaning up test message..."
            rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST get \
                queue=caldera.checking.instructions ackmode=ack_requeue_false >> $LOG_FILE 2>&1
            print_success "Test message cleaned up"
        else
            print_error "Message was not queued properly"
            return 1
        fi
    else
        print_error "Failed to publish test message"
        return 1
    fi
}

# Verify phase 3
verify_phase3() {
    print_status "Verifying Phase 3 setup..."
    
    # Check exchange exists
    local exchange_count=$(rabbitmqctl list_exchanges -p $VHOST | grep -c "caldera.checking.exchange" || true)
    if [ $exchange_count -ne 1 ]; then
        print_error "Exchange was not created"
        return 1
    fi
    
    # Check queues exist
    local queue_count=$(rabbitmqctl list_queues -p $VHOST | grep -c "caldera.checking" || true)
    # there are an additional keyword "caldera.checking" in message log, so we need to add 1
    if [ $queue_count -ne 6 ]; then
        print_error "Not all queues were created (expected 5, found $queue_count)"
        return 1
    fi
    
    # Check bindings exist
    local binding_count=$(rabbitmqctl list_bindings -p $VHOST | grep -c "caldera.checking.exchange" || true)
    if [ $binding_count -ne 5 ]; then
        print_error "Not all bindings were created (expected 5, found $binding_count)"
        return 1
    fi
    
    print_success "Phase 3 completed successfully"
}

# Display setup information
display_setup_info() {
    echo
    print_success "Exchanges and Queues created!"
    echo
    print_status "Exchange:"
    rabbitmqctl list_exchanges -p $VHOST
    echo
    print_status "Queues:"
    rabbitmqctl list_queues -p $VHOST name messages
    echo
    print_status "Bindings:"
    rabbitmqctl list_bindings -p $VHOST
    echo
}

# Main execution
main() {
    echo "======================================"
    echo "Phase 3: Setup Exchanges and Queues"
    echo "======================================"
    echo
    
    # Initialize log file
    echo "Phase 3 Log - $(date)" > $LOG_FILE
    
    print_status "Starting Phase 3: Exchanges and Queues setup..."
    
    # Check prerequisites
    check_privileges
    load_passwords
    check_prerequisites
    
    # Execute phase 3 steps
    create_exchanges_and_queues
    create_bindings
    
    # Test functionality
    test_functionality
    
    # Verify phase 3
    verify_phase3
    
    # Display results
    display_setup_info
    
    echo
    print_success "Phase 3 completed! Exchanges and Queues are ready."
    echo "Next step: Run 04_configure_limits_security.sh"
    echo "Log file: $LOG_FILE"
}

# Run main function
main "$@" 