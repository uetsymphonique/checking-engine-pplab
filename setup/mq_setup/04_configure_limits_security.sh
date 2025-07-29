#!/bin/bash

# Phase 4: Configure Limits and Security
# This script configures resource limits, policies, and security settings

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VHOST="/caldera_checking"
LOG_FILE="rabbitmq_phase4.log"
PASSWORDS_FILE="rabbitmq_passwords.txt"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[PHASE 4]${NC} $1"
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
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
    
    # Check if queues exist
    local queue_count=$(rabbitmqctl list_queues -p $VHOST | grep -c "caldera.checking" || true)
    # there are an additional keyword "caldera.checking" in message log, so we need to add 1
    if [ $queue_count -ne 6 ]; then
        print_error "Queues not found. Run Phase 3 first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Configure resource limits for users
configure_user_limits() {
    print_status "Configuring user resource limits..."
    
    # Set connection limits per user
    print_status "Setting connection limits for caldera_publisher..."
    rabbitmqctl set_user_limits -p $VHOST caldera_publisher '{"max-connections": 100}' >> $LOG_FILE 2>&1
    
    print_status "Setting connection limits for checking_consumer..."
    rabbitmqctl set_user_limits -p $VHOST checking_consumer '{"max-connections": 100}' >> $LOG_FILE 2>&1
    
    print_status "Setting connection limits for checking_worker..."
    rabbitmqctl set_user_limits -p $VHOST checking_worker '{"max-connections": 100}' >> $LOG_FILE 2>&1
    
    print_status "Setting connection limits for checking_dispatcher..."
    rabbitmqctl set_user_limits -p $VHOST checking_dispatcher '{"max-connections": 100}' >> $LOG_FILE 2>&1
    
    print_status "Setting connection limits for checking_result_consumer..."
    rabbitmqctl set_user_limits -p $VHOST checking_result_consumer '{"max-connections": 100}' >> $LOG_FILE 2>&1
    
    print_success "User resource limits configured"
}

# Configure queue policies
configure_queue_policies() {
    print_status "Configuring queue policies..."
    
    # Set queue policies for reliability and limits
    rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST declare policy \
        name=caldera-checking-limits \
        pattern="^caldera\.checking\..*" \
        definition='{"max-length": 10000, "message-ttl": 3600000, "ha-mode": "all"}' >> $LOG_FILE 2>&1
    
    print_success "Queue policies configured"
}

# Configure firewall
configure_firewall() {
    print_status "Configuring firewall rules..."
    
    if command_exists ufw; then
        ufw allow 5672/tcp >> $LOG_FILE 2>&1
        ufw allow 15672/tcp >> $LOG_FILE 2>&1
        ufw --force reload >> $LOG_FILE 2>&1
        print_success "UFW firewall rules configured"
    elif command_exists firewall-cmd; then
        firewall-cmd --permanent --add-port=5672/tcp >> $LOG_FILE 2>&1
        firewall-cmd --permanent --add-port=15672/tcp >> $LOG_FILE 2>&1
        firewall-cmd --reload >> $LOG_FILE 2>&1
        print_success "Firewalld rules configured"
    else
        print_warning "No supported firewall found (ufw/firewalld)"
        print_warning "Please manually configure firewall to allow ports 5672 and 15672"
    fi
}

# Create configuration files
create_config_files() {
    print_status "Creating configuration files..."
    
    # Create rabbitmq.conf
    print_status "Creating RabbitMQ configuration file..."
    cat > /etc/rabbitmq/rabbitmq.conf << EOF
# RabbitMQ Configuration for Checking Engine
# Generated on: $(date)

# Network settings
listeners.tcp.default = 5672
management.tcp.port = 15672

# Memory and disk limits
vm_memory_high_watermark.relative = 0.6
disk_free_limit.relative = 1.0

# Logging
log.console = true
log.console.level = info
log.file = /var/log/rabbitmq/rabbit.log
log.file.level = info

# Additional security settings
auth_mechanisms.1 = PLAIN
auth_mechanisms.2 = AMQPLAIN

# Management plugin settings
management.tcp.port = 15672
management.http_log_dir = /var/log/rabbitmq/management_access.log

# Security settings
loopback_users = none
EOF

    # Create .env template
    print_status "Creating environment template file..."
    cat > .env.example << EOF
# RabbitMQ Configuration for Checking Engine
# Copy this file to .env and update with actual passwords from $PASSWORDS_FILE

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_VHOST=$VHOST
RABBITMQ_MANAGEMENT_PORT=15672

# User Credentials (update with actual passwords)
RABBITMQ_ADMIN_USER=caldera_admin
RABBITMQ_ADMIN_PASS=<from_password_file>

RABBITMQ_PUBLISHER_USER=caldera_publisher
RABBITMQ_PUBLISHER_PASS=<from_password_file>

RABBITMQ_CONSUMER_USER=checking_consumer
RABBITMQ_CONSUMER_PASS=<from_password_file>

RABBITMQ_WORKER_USER=checking_worker
RABBITMQ_WORKER_PASS=<from_password_file>

RABBITMQ_DISPATCHER_USER=checking_dispatcher
RABBITMQ_DISPATCHER_PASS=<from_password_file>

RABBITMQ_RESULT_CONSUMER_USER=checking_result_consumer
RABBITMQ_RESULT_CONSUMER_PASS=<from_password_file>

RABBITMQ_MONITOR_USER=monitor_user
RABBITMQ_MONITOR_PASS=<from_password_file>

# Exchange and Queue Names
RABBITMQ_EXCHANGE=caldera.checking.exchange
RABBITMQ_INSTRUCTIONS_QUEUE=caldera.checking.instructions
RABBITMQ_API_TASKS_QUEUE=caldera.checking.api.tasks
RABBITMQ_AGENT_TASKS_QUEUE=caldera.checking.agent.tasks
RABBITMQ_API_RESPONSES_QUEUE=caldera.checking.api.responses
RABBITMQ_AGENT_RESPONSES_QUEUE=caldera.checking.agent.responses

# Routing Keys
ROUTING_KEY_EXECUTION_RESULT=caldera.execution.result
ROUTING_KEY_API_TASK=checking.api.task
ROUTING_KEY_AGENT_TASK=checking.agent.task
ROUTING_KEY_API_RESPONSE=checking.api.response
ROUTING_KEY_AGENT_RESPONSE=checking.agent.response
EOF
    
    print_success "Configuration files created"
}

# Test resource limits
test_resource_limits() {
    print_status "Testing resource limits configuration..."
    
    # Test user limits
    local user_limits_output
    user_limits_output=$(rabbitmqctl list_user_limits --user caldera_publisher 2>/dev/null || echo "No limits set")
    
    if [[ "$user_limits_output" == *"max-connections"* ]]; then
        print_success "User limits are properly configured"
    else
        print_warning "User limits may not be set correctly"
    fi
    
    # Test policies
    local policy_count=$(rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST list policies | grep -c "caldera-checking-limits" || true)
    
    if [ $policy_count -eq 1 ]; then
        print_success "Queue policies are properly configured"
    else
        print_error "Queue policies not found"
        return 1
    fi
}

# Verify phase 4
verify_phase4() {
    print_status "Verifying Phase 4 configuration..."
    
    # Check if configuration file exists
    if [ ! -f "/etc/rabbitmq/rabbitmq.conf" ]; then
        print_error "RabbitMQ configuration file was not created"
        return 1
    fi
    
    # Check if .env template exists
    if [ ! -f ".env.example" ]; then
        print_error "Environment template file was not created"
        return 1
    fi
    
    # Test resource limits
    test_resource_limits
    
    print_success "Phase 4 completed successfully"
}

# Display configuration information
display_config_info() {
    echo
    print_success "Limits and Security configured!"
    echo
    print_status "User Limits:"
    echo "  caldera_publisher: max 100 connections"
    echo "  checking_consumer: max 100 connections"
    echo "  checking_worker: max 100 connections"
    echo "  checking_dispatcher: max 100 connections"
    echo "  checking_result_consumer: max 100 connections"
    echo
    print_status "Queue Policies:"
    rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST list policies
    echo
    print_status "Configuration Files Created:"
    echo "  /etc/rabbitmq/rabbitmq.conf - Main RabbitMQ configuration"
    echo "  .env.example - Environment template for applications"
    echo
    print_warning "Next Steps:"
    echo "  1. Copy .env.example to .env and update with actual passwords"
    echo "  2. Restart RabbitMQ to apply configuration changes"
    echo "  3. Run Phase 5 for final verification"
}

# Main execution
main() {
    echo "======================================"
    echo "Phase 4: Configure Limits and Security"
    echo "======================================"
    echo
    
    # Initialize log file
    echo "Phase 4 Log - $(date)" > $LOG_FILE
    
    print_status "Starting Phase 4: Limits and Security configuration..."
    
    # Check prerequisites
    check_privileges
    load_passwords
    check_prerequisites
    
    # Execute phase 4 steps
    configure_user_limits
    configure_queue_policies
    # configure_firewall
    create_config_files
    
    # Verify phase 4
    verify_phase4
    
    # Display results
    display_config_info
    
    echo
    print_success "Phase 4 completed! Limits and Security are configured."
    echo "Next step: Run 05_final_verification.sh"
    echo "Log file: $LOG_FILE"
}

# Run main function
main "$@" 