#!/bin/bash

# Flush All Queues Script
# This script removes all messages from the Checking Engine queues

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VHOST="/caldera_checking"
PASSWORDS_FILE="rabbitmq_passwords.txt"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[FLUSH]${NC} $1"
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
    if [ -f "$PASSWORDS_FILE" ]; then
        source $PASSWORDS_FILE
        ADMIN_PASS=$CALDERA_ADMIN_PASSWORD
        
        if [ -z "$ADMIN_PASS" ]; then
            print_warning "Admin password not found in passwords file"
            print_warning "Will use sudo rabbitmqctl purge_queue instead"
            USE_RABBITMQCTL=true
        else
            print_success "Admin password loaded from $PASSWORDS_FILE"
            USE_RABBITMQCTL=false
        fi
    else
        print_warning "Passwords file not found: $PASSWORDS_FILE"
        print_warning "Will use sudo rabbitmqctl purge_queue instead"
        USE_RABBITMQCTL=true
    fi
}

# Check prerequisites
check_prerequisites() {
    # Check if RabbitMQ is running
    if ! systemctl is-active --quiet rabbitmq-server; then
        print_error "RabbitMQ service is not running"
        exit 1
    fi
    
    # Check virtual host exists
    if ! rabbitmqctl list_vhosts | grep -q "$VHOST"; then
        print_error "Virtual host $VHOST does not exist"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Show current queue status
show_queue_status() {
    print_status "Current queue status:"
    sudo rabbitmqctl list_queues -p $VHOST name messages
    echo
}

# Flush using rabbitmqctl (faster method)
flush_with_rabbitmqctl() {
    print_status "Flushing queues using rabbitmqctl purge_queue..."
    
    # Purge instructions queue
    print_status "Purging caldera.checking.instructions..."
    sudo rabbitmqctl purge_queue caldera.checking.instructions -p $VHOST
    
    # Purge api.responses queue
    print_status "Purging caldera.checking.api.responses..."
    sudo rabbitmqctl purge_queue caldera.checking.api.responses -p $VHOST
    
    # Purge agent.responses queue
    print_status "Purging caldera.checking.agent.responses..."
    sudo rabbitmqctl purge_queue caldera.checking.agent.responses -p $VHOST
    
    print_success "All queues purged using rabbitmqctl"
}

# Flush using rabbitmqadmin (message-by-message)
flush_with_rabbitmqadmin() {
    print_status "Flushing queues using rabbitmqadmin get..."
    
    # Flush instructions queue
    print_status "Flushing caldera.checking.instructions..."
    while true; do
        local result=$(rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V $VHOST get \
            queue=caldera.checking.instructions ackmode=ack_requeue_false 2>/dev/null || echo "No messages")
        
        if [[ "$result" == *"No messages"* ]]; then
            break
        fi
    done
    
    # Flush api.responses queue
    print_status "Flushing caldera.checking.api.responses..."
    while true; do
        local result=$(rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V $VHOST get \
            queue=caldera.checking.api.responses ackmode=ack_requeue_false 2>/dev/null || echo "No messages")
        
        if [[ "$result" == *"No messages"* ]]; then
            break
        fi
    done
    
    # Flush agent.responses queue
    print_status "Flushing caldera.checking.agent.responses..."
    while true; do
        local result=$(rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V $VHOST get \
            queue=caldera.checking.agent.responses ackmode=ack_requeue_false 2>/dev/null || echo "No messages")
        
        if [[ "$result" == *"No messages"* ]]; then
            break
        fi
    done
    
    print_success "All queues flushed using rabbitmqadmin"
}

# Main flush function
flush_all_queues() {
    print_status "Starting queue flush operation..."
    
    if [ "$USE_RABBITMQCTL" = true ]; then
        flush_with_rabbitmqctl
    else
        flush_with_rabbitmqadmin
    fi
    
    print_success "Queue flush completed"
}

# Main execution
main() {
    echo "======================================"
    echo "Flush All Queues - Checking Engine"
    echo "======================================"
    echo
    
    # Check prerequisites
    check_privileges
    load_passwords
    check_prerequisites
    
    # Show status before
    print_status "BEFORE flush:"
    show_queue_status
    
    # Ask for confirmation
    echo -e "${YELLOW}This will remove ALL messages from the following queues:${NC}"
    echo "  - caldera.checking.instructions"
    echo "  - caldera.checking.api.responses"
    echo "  - caldera.checking.agent.responses"
    echo
    echo -e "${YELLOW}Are you sure you want to continue? (y/N):${NC}"
    read -r confirmation
    
    case "$confirmation" in
        [yY]|[yY][eE][sS])
            flush_all_queues
            ;;
        *)
            print_warning "Operation cancelled by user"
            exit 0
            ;;
    esac
    
    # Show status after
    print_status "AFTER flush:"
    show_queue_status
    
    print_success "🎉 All queues successfully flushed!"
    echo
    print_status "Queue states should now show 0 messages for all queues"
    print_status "You can verify by running: sudo rabbitmqctl list_queues -p $VHOST name messages"
}

# Run main function
main "$@" 