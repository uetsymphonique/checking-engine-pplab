#!/bin/bash

# Phase 1: Install RabbitMQ Server
# This script handles basic RabbitMQ installation and service setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

LOG_FILE="rabbitmq_phase1.log"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[PHASE 1]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for RabbitMQ to be ready
wait_for_rabbitmq() {
    print_status "Waiting for RabbitMQ to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if sudo rabbitmqctl status >/dev/null 2>&1; then
            print_success "RabbitMQ is ready!"
            return 0
        fi
        
        print_status "Attempt $attempt/$max_attempts - Waiting for RabbitMQ..."
        sleep 2
        ((attempt++))
    done
    
    print_error "RabbitMQ failed to start within expected time"
    return 1
}

# Check if running as root or with sudo
check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Backup existing configuration
backup_existing_config() {
    if [ -f "/etc/rabbitmq/rabbitmq.conf" ]; then
        print_status "Backing up existing RabbitMQ configuration..."
        cp /etc/rabbitmq/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf.backup.$(date +%Y%m%d_%H%M%S)
        print_success "Configuration backed up"
    fi
}

# Install RabbitMQ
install_rabbitmq() {
    print_status "Installing RabbitMQ Server..."
    
    # Update package list
    # apt update >> $LOG_FILE 2>&1
    
    # Install RabbitMQ
    apt install -y rabbitmq-server >> $LOG_FILE 2>&1
    
    # Enable and start service
    systemctl enable rabbitmq-server >> $LOG_FILE 2>&1
    systemctl start rabbitmq-server >> $LOG_FILE 2>&1
    
    print_success "RabbitMQ Server installed and started"
}

# Enable management plugin
enable_management_plugin() {
    print_status "Enabling RabbitMQ Management Plugin..."
    
    rabbitmq-plugins enable rabbitmq_management >> $LOG_FILE 2>&1
    
    # Install rabbitmqadmin (no need)
    # apt install -y rabbitmqadmin >> $LOG_FILE 2>&1
    
    # Restart service
    systemctl restart rabbitmq-server >> $LOG_FILE 2>&1
    
    wait_for_rabbitmq
    
    print_success "Management plugin enabled"
}

# Verify phase 1
verify_phase1() {
    print_status "Verifying Phase 1 installation..."
    
    # Check service status
    if ! systemctl is-active --quiet rabbitmq-server; then
        print_error "RabbitMQ service is not running"
        return 1
    fi
    
    # Check management plugin
    rabbitmq-plugins list >> $LOG_FILE 2>&1
    # if ! rabbitmq-plugins list | grep -q "[E*] rabbitmq_management"; then
    #     print_error "Management plugin is not enabled"
    #     return 1
    # fi
    
    print_success "Phase 1 completed successfully"
}

# Main execution
main() {
    echo "======================================"
    echo "Phase 1: Install RabbitMQ Server"
    echo "======================================"
    echo
    
    # Initialize log file
    echo "Phase 1 Log - $(date)" > $LOG_FILE
    
    print_status "Starting Phase 1: RabbitMQ installation..."
    
    # Check prerequisites
    check_privileges
    
    # Execute phase 1 steps
    backup_existing_config
    install_rabbitmq
    enable_management_plugin
    
    # Verify phase 1
    verify_phase1
    
    echo
    print_success "Phase 1 completed! RabbitMQ is installed and ready."
    echo "Next step: Run 02_setup_vhost_users.sh"
    echo "Log file: $LOG_FILE"
}

# Run main function
main "$@" 