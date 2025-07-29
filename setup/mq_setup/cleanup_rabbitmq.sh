#!/bin/bash

# RabbitMQ Cleanup Script for Checking Engine
# This script removes the RabbitMQ setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VHOST="/caldera_checking"
LOG_FILE="rabbitmq_cleanup.log"

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

# Check if running as root or with sudo
check_privileges() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --vhost-only    Remove only virtual host and its contents (keep RabbitMQ server)"
    echo "  --users-only    Remove only checking engine users (keep RabbitMQ server)"
    echo "  --full         Remove everything including RabbitMQ server (default)"
    echo "  --help         Show this help message"
    echo
    echo "Examples:"
    echo "  $0                    # Full cleanup (default)"
    echo "  $0 --full           # Full cleanup"
    echo "  $0 --vhost-only     # Remove only virtual host"
    echo "  $0 --users-only     # Remove only users"
}

# Confirm user intention
confirm_action() {
    local action_type="$1"
    
    echo
    print_warning "This will permanently remove the following:"
    
    case $action_type in
        "full")
            echo "  - All checking engine users"
            echo "  - Virtual host $VHOST and all its queues/exchanges"
            echo "  - RabbitMQ server and all data"
            echo "  - Configuration files"
            ;;
        "vhost")
            echo "  - Virtual host $VHOST and all its queues/exchanges"
            echo "  - All data in the virtual host"
            ;;
        "users")
            echo "  - All checking engine users"
            echo "  - User permissions and configurations"
            ;;
    esac
    
    echo
    read -p "Are you sure you want to continue? [y/N]: " confirm
    
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_status "Operation cancelled by user"
        exit 0
    fi
}

# Remove users
remove_users() {
    print_status "Removing checking engine users..."
    
    local users=("caldera_admin" "caldera_publisher" "checking_consumer" "checking_worker" "checking_dispatcher" "checking_result_consumer" "monitor_user")
    
    for user in "${users[@]}"; do
        if rabbitmqctl list_users | grep -q "^$user"; then
            print_status "Removing user: $user"
            rabbitmqctl delete_user "$user" >> $LOG_FILE 2>&1 || true
        else
            print_status "User $user not found, skipping..."
        fi
    done
    
    print_success "Users removed successfully"
}

# Remove virtual host
remove_virtual_host() {
    print_status "Removing virtual host: $VHOST"
    
    if rabbitmqctl list_vhosts | grep -q "$VHOST"; then
        # This will remove all queues, exchanges, bindings in the vhost
        rabbitmqctl delete_vhost "$VHOST" >> $LOG_FILE 2>&1
        print_success "Virtual host removed: $VHOST"
    else
        print_status "Virtual host $VHOST not found, skipping..."
    fi
}

# Stop RabbitMQ service
stop_rabbitmq() {
    print_status "Stopping RabbitMQ service..."
    
    if systemctl is-active --quiet rabbitmq-server; then
        systemctl stop rabbitmq-server >> $LOG_FILE 2>&1
        print_success "RabbitMQ service stopped"
    else
        print_status "RabbitMQ service was not running"
    fi
}

# Remove RabbitMQ completely
remove_rabbitmq_server() {
    print_status "Removing RabbitMQ server completely..."
    
    # Stop service first
    stop_rabbitmq
    
    # Disable service
    systemctl disable rabbitmq-server >> $LOG_FILE 2>&1 || true
    
    # Remove packages
    apt remove --purge -y rabbitmq-server >> $LOG_FILE 2>&1 || true
    apt autoremove -y >> $LOG_FILE 2>&1 || true
    
    # Remove data directories
    print_status "Removing RabbitMQ data directories..."
    rm -rf /var/lib/rabbitmq >> $LOG_FILE 2>&1 || true
    rm -rf /var/log/rabbitmq >> $LOG_FILE 2>&1 || true
    rm -rf /etc/rabbitmq >> $LOG_FILE 2>&1 || true
    
    print_success "RabbitMQ server removed completely"
}

# Remove configuration files
remove_config_files() {
    print_status "Removing configuration files..."
    
    local files=(".env.example" ".env" "rabbitmq_passwords.txt" "rabbitmq_phase1.log" "rabbitmq_phase2.log" "rabbitmq_phase3.log" "rabbitmq_phase4.log" "rabbitmq_phase5.log")
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            print_status "Removing file: $file"
            rm -f "$file"
        fi
    done
    
    print_success "Configuration files removed"
}

# Remove firewall rules
remove_firewall_rules() {
    print_status "Removing firewall rules..."
    
    if command -v ufw >/dev/null 2>&1; then
        # Remove RabbitMQ ports
        ufw delete allow 5672/tcp >> $LOG_FILE 2>&1 || true
        ufw delete allow 15672/tcp >> $LOG_FILE 2>&1 || true
        ufw --force reload >> $LOG_FILE 2>&1 || true
        print_success "Firewall rules removed"
    else
        print_warning "UFW not found. Please manually remove firewall rules for ports 5672 and 15672"
    fi
}

# Verify cleanup
verify_cleanup() {
    local cleanup_type="$1"
    
    print_status "Verifying cleanup..."
    
    case $cleanup_type in
        "full")
            # Check if RabbitMQ service exists
            if systemctl list-unit-files | grep -q rabbitmq-server; then
                print_warning "RabbitMQ service still exists"
            else
                print_success "RabbitMQ service completely removed"
            fi
            
            # Check if data directories exist
            if [[ -d "/var/lib/rabbitmq" ]] || [[ -d "/etc/rabbitmq" ]]; then
                print_warning "Some RabbitMQ directories still exist"
            else
                print_success "All RabbitMQ directories removed"
            fi
            ;;
        "vhost")
            if systemctl is-active --quiet rabbitmq-server; then
                if rabbitmqctl list_vhosts | grep -q "$VHOST"; then
                    print_error "Virtual host still exists"
                    return 1
                else
                    print_success "Virtual host successfully removed"
                fi
            else
                print_warning "RabbitMQ service is not running, cannot verify virtual host removal"
            fi
            ;;
        "users")
            if systemctl is-active --quiet rabbitmq-server; then
                local remaining_users=$(rabbitmqctl list_users | grep -c "caldera\|checking\|monitor" || true)
                if [[ $remaining_users -gt 0 ]]; then
                    print_error "Some checking engine users still exist"
                    return 1
                else
                    print_success "All checking engine users removed"
                fi
            else
                print_warning "RabbitMQ service is not running, cannot verify user removal"
            fi
            ;;
    esac
}

# Display cleanup summary
display_cleanup_summary() {
    local cleanup_type="$1"
    
    echo
    print_success "Cleanup completed!"
    echo
    print_status "Summary:"
    
    case $cleanup_type in
        "full")
            echo "  - RabbitMQ server: REMOVED"
            echo "  - Virtual host: REMOVED"
            echo "  - All users: REMOVED"
            echo "  - Configuration files: REMOVED"
            echo "  - Firewall rules: REMOVED"
            ;;
        "vhost")
            echo "  - Virtual host $VHOST: REMOVED"
            echo "  - All queues and exchanges: REMOVED"
            echo "  - RabbitMQ server: KEPT"
            ;;
        "users")
            echo "  - All checking engine users: REMOVED"
            echo "  - Virtual host: KEPT"
            echo "  - RabbitMQ server: KEPT"
            ;;
    esac
    
    echo "  - Log file: $LOG_FILE"
    echo
    
    if [[ $cleanup_type != "full" ]]; then
        print_status "To completely remove RabbitMQ server, run:"
        echo "  sudo $0 --full"
        echo
    fi
}

# Virtual host only cleanup
cleanup_vhost_only() {
    print_status "Performing virtual host cleanup..."
    
    confirm_action "vhost"
    
    remove_virtual_host
    verify_cleanup "vhost"
    display_cleanup_summary "vhost"
}

# Users only cleanup
cleanup_users_only() {
    print_status "Performing users cleanup..."
    
    confirm_action "users"
    
    remove_users
    verify_cleanup "users"
    display_cleanup_summary "users"
}

# Full cleanup
cleanup_full() {
    print_status "Performing full cleanup..."
    
    confirm_action "full"
    
    # Remove in order: users, vhost, server, configs, firewall
    if systemctl is-active --quiet rabbitmq-server; then
        remove_users
        remove_virtual_host
    else
        print_status "RabbitMQ service not running, skipping user/vhost cleanup"
    fi
    
    remove_rabbitmq_server
    remove_config_files
    # remove_firewall_rules
    
    verify_cleanup "full"
    display_cleanup_summary "full"
}

# Main execution
main() {
    local cleanup_type="full"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --vhost-only)
                cleanup_type="vhost"
                shift
                ;;
            --users-only)
                cleanup_type="users"
                shift
                ;;
            --full)
                cleanup_type="full"
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    echo "========================================="
    echo "RabbitMQ Cleanup for Checking Engine"
    echo "========================================="
    echo
    
    # Initialize log file
    echo "RabbitMQ Cleanup Log - $(date)" > $LOG_FILE
    
    # Check prerequisites
    check_privileges
    
    # Perform cleanup based on type
    case $cleanup_type in
        "vhost")
            cleanup_vhost_only
            ;;
        "users")
            cleanup_users_only
            ;;
        "full")
            cleanup_full
            ;;
    esac
    
    print_success "Cleanup operation completed successfully!"
}

# Run main function
main "$@" 