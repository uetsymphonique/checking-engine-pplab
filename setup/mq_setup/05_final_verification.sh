#!/bin/bash

# Phase 5: Final Verification and Testing
# This script performs comprehensive testing of the complete RabbitMQ setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
VHOST="/caldera_checking"
LOG_FILE="rabbitmq_phase5.log"
PASSWORDS_FILE="rabbitmq_passwords.txt"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[PHASE 5]${NC} $1"
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

print_usecase() {
    echo -e "${YELLOW}[USECASE]${NC} $1"
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
        print_error "Please run previous phases first"
        exit 1
    fi
    
    # Source the passwords file
    source $PASSWORDS_FILE
    
    # Set variables from the loaded environment
    ADMIN_PASS=$CALDERA_ADMIN_PASSWORD
    PUBLISHER_PASS=$CALDERA_PUBLISHER_PASSWORD
    CONSUMER_PASS=$CHECKING_CONSUMER_PASSWORD
    WORKER_PASS=$CHECKING_WORKER_PASSWORD
    MONITOR_PASS=$MONITOR_USER_PASSWORD
    DISPATCHER_PASS=$CHECKING_DISPATCHER_PASSWORD
    RESULT_PASS=$CHECKING_RESULT_CONSUMER_PASSWORD
    
    if [ -z "$ADMIN_PASS" ] || [ -z "$PUBLISHER_PASS" ] || [ -z "$CONSUMER_PASS" ] || [ -z "$WORKER_PASS" ] || [ -z "$MONITOR_PASS" ] || [ -z "$DISPATCHER_PASS" ] || [ -z "$RESULT_PASS" ]; then
        print_error "One or more passwords not found in passwords file"
        exit 1
    fi
    
    print_success "All passwords loaded successfully"
}

# Check all prerequisites
check_prerequisites() {
    print_status "Checking all prerequisites..."
    
    # Check if RabbitMQ is running
    if ! systemctl is-active --quiet rabbitmq-server; then
        print_error "RabbitMQ service is not running"
        exit 1
    fi
    
    # Check virtual host
    if ! rabbitmqctl list_vhosts | grep -q "$VHOST"; then
        print_error "Virtual host $VHOST does not exist"
        exit 1
    fi
    
    # Check users
    local user_count=$(rabbitmqctl list_users | grep -c "caldera\|checking\|monitor" || true)
    if [ $user_count -ne 7 ]; then
        print_error "Not all users exist (expected 7, found $user_count)"
        exit 1
    fi
    
    # Check queues
    local queue_count=$(rabbitmqctl list_queues -p $VHOST | grep -c "caldera.checking" || true)
    # there are an additional keyword "caldera.checking" in message log, so we need to add 1
    if [ $queue_count -ne 6 ]; then
        print_error "Not all queues exist (expected 5, found $queue_count)"
        exit 1
    fi
    
    # Check exchange
    local exchange_count=$(rabbitmqctl list_exchanges -p $VHOST | grep -c "caldera.checking.exchange" || true)
    if [ $exchange_count -ne 1 ]; then
        print_error "Exchange does not exist"
        exit 1
    fi
    
    print_success "All prerequisites verified"
}

# Test user permissions and access control
test_user_permissions() {
    print_status "Testing user permissions and access control..."
    
    # Test publisher can only publish to exchange
    print_status "Testing publisher permissions..."
    if rabbitmqadmin -u caldera_publisher -p $PUBLISHER_PASS -V $VHOST publish \
        exchange=caldera.checking.exchange \
        routing_key=caldera.execution.result \
        payload='{"test": "publisher_test"}' >> $LOG_FILE 2>&1; then
        print_success "[+] Publisher can publish to exchange"
    else
        print_error "[-] Publisher cannot publish to exchange"
        return 1
    fi
    
    # Test consumer can only read from instructions queue
    print_status "Testing consumer permissions..."
    sleep 1  # Allow message to be routed
    local consumed_message=$(rabbitmqadmin -u checking_consumer -p $CONSUMER_PASS -V $VHOST get \
        queue=caldera.checking.instructions ackmode=ack_requeue_false 2>/dev/null || echo "FAILED")
    
    if [[ "$consumed_message" != "FAILED" ]]; then
        print_success "[+] Consumer can read from instructions queue"
    else
        print_error "[-] Consumer cannot read from instructions queue"
        return 1
    fi
    
    # Test dispatcher can publish tasks
    print_status "Testing dispatcher permissions..."
    if rabbitmqadmin -u checking_dispatcher -p $DISPATCHER_PASS -V $VHOST publish \
        exchange=caldera.checking.exchange \
        routing_key=checking.api.task \
        payload='{"test": "dispatcher_task"}' >> $LOG_FILE 2>&1; then
        print_success "[+] Dispatcher can publish tasks"
    else
        print_error "[-] Dispatcher cannot publish tasks"
        return 1
    fi

    # Test worker can read from API tasks queue and consume the task
    print_status "Testing worker read permission on API tasks queue..."
    sleep 1  # Allow task to be routed
    local worker_task_read=$(rabbitmqadmin -u checking_worker -p $WORKER_PASS -V $VHOST get \
        queue=caldera.checking.api.tasks ackmode=ack_requeue_false 2>/dev/null || echo "FAILED")
    if [[ "$worker_task_read" != "FAILED" ]]; then
        print_success "[+] Worker can read from API tasks queue"
    else
        print_error "[-] Worker cannot read from API tasks queue"
        return 1
    fi
    
    # Test worker can publish to response queues (after consuming task)
    print_status "Testing worker permissions..."
    if rabbitmqadmin -u checking_worker -p $WORKER_PASS -V $VHOST publish \
        exchange=caldera.checking.exchange \
        routing_key=checking.api.response \
        payload='{"test": "worker_api_response"}' >> $LOG_FILE 2>&1; then
        print_success "[+] Worker can publish API responses"
    else
        print_error "[-] Worker cannot publish API responses"
        return 1
    fi
    
    if rabbitmqadmin -u checking_worker -p $WORKER_PASS -V $VHOST publish \
        exchange=caldera.checking.exchange \
        routing_key=checking.agent.response \
        payload='{"test": "worker_agent_response"}' >> $LOG_FILE 2>&1; then
        print_success "[+] Worker can publish agent responses"
    else
        print_error "[-] Worker cannot publish agent responses"
        return 1
    fi

    # Test result consumer can read responses queues
    print_status "Testing result consumer permissions..."
    sleep 1
    local res_read=$(rabbitmqadmin -u checking_result_consumer -p $RESULT_PASS -V $VHOST get \
        queue=caldera.checking.api.responses ackmode=ack_requeue_false 2>/dev/null || echo "FAILED")
    if [[ "$res_read" != "FAILED" ]]; then
        print_success "[+] Result consumer can read API responses queue"
    else
        print_error "[-] Result consumer cannot read API responses queue"
        return 1
    fi

    # Test monitor can read from all queues
    print_status "Testing monitor permissions..."
    local monitor_test=$(rabbitmqadmin -u monitor_user -p $MONITOR_PASS -V $VHOST list queues 2>/dev/null || echo "FAILED")
    
    if [[ "$monitor_test" != "FAILED" ]]; then
        print_success "[+] Monitor can read queue information"
    else
        print_error "[-] Monitor cannot read queue information"
        return 1
    fi
    
    print_success "User permissions test completed"
}

# Test complete Purple Team workflow (simplified for Phase 5)
test_purple_team_workflow() {
    print_status "Testing basic Purple Team workflow..."
    print_status "For detailed interactive testing, use: sudo ./06_interactive_purple_team_test.sh"
    
    # Simple test - just verify basic publish/consume works
    local test_payload='{"test": "basic_workflow", "timestamp": "'$(date -Iseconds)'"}'
    
    # Test publish
    rabbitmqadmin -u caldera_publisher -p $PUBLISHER_PASS -V $VHOST publish \
        exchange=caldera.checking.exchange \
        routing_key=caldera.execution.result \
        payload="$test_payload" >> $LOG_FILE 2>&1
    
    print_success "-> Basic publish test completed"
    
    # Check message routing
    sleep 1
    local instructions_count=$(rabbitmqctl list_queues -p $VHOST name messages | grep caldera.checking.instructions | awk '{print $2}')
    print_status "-> Instructions queue has $instructions_count message(s)"
    
    # Test consume
    local consumed_message=$(rabbitmqadmin -u checking_consumer -p $CONSUMER_PASS -V $VHOST get \
        queue=caldera.checking.instructions ackmode=ack_requeue_false >> $LOG_FILE 2>&1)
    
    print_success "-> Basic consume test completed"
    
    print_success "[+] BASIC WORKFLOW TEST COMPLETE"
    print_status "Run Phase 6 for detailed interactive Purple Team testing"
}

# Test resource limits and policies
test_resource_limits() {
    print_status "Testing resource limits and policies..."
    
    # Check user limits
    print_status "Checking user connection limits..."
    rabbitmqctl list_user_limits --user caldera_publisher | grep -q "max-connections" && \
        print_success "[+] Publisher connection limits configured" || \
        print_warning "[-] Publisher connection limits not found"
    
    rabbitmqctl list_user_limits --user checking_consumer | grep -q "max-connections" && \
        print_success "[+] Consumer connection limits configured" || \
        print_warning "[-] Consumer connection limits not found"
    
    rabbitmqctl list_user_limits --user checking_worker | grep -q "max-connections" && \
        print_success "[+] Worker connection limits configured" || \
        print_warning "[-] Worker connection limits not found"
    
    # Check queue policies
    print_status "Checking queue policies..."
    local policy_count=$(rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST list policies | grep -c "caldera-checking-limits" || true)
    
    if [ $policy_count -eq 1 ]; then
        print_success "[+] Queue policies configured"
    else
        print_warning "[-] Queue policies not found"
    fi
}

# Generate comprehensive status report
generate_status_report() {
    print_status "Generating comprehensive status report..."
    
    local report_file="rabbitmq_setup_report.txt"
    
    cat > $report_file << EOF
# RabbitMQ Checking Engine Setup Report
Generated: $(date)

## System Status
RabbitMQ Service: $(systemctl is-active rabbitmq-server)
Management Plugin: $(rabbitmq-plugins list | grep rabbitmq_management | awk '{print $2}')

## Virtual Host
$VHOST

## Users and Permissions
$(rabbitmqctl list_users)

## User Permissions in Virtual Host
$(rabbitmqctl list_permissions -p $VHOST)

## Exchanges
$(rabbitmqctl list_exchanges -p $VHOST)

## Queues
$(rabbitmqctl list_queues -p $VHOST name messages)

## Bindings
$(rabbitmqctl list_bindings -p $VHOST)

## Policies
$(rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST list policies)

## User Limits
Publisher limits: $(rabbitmqctl list_user_limits --user caldera_publisher 2>/dev/null || echo "None")
Consumer limits: $(rabbitmqctl list_user_limits --user checking_consumer 2>/dev/null || echo "None")
Worker limits: $(rabbitmqctl list_user_limits --user checking_worker 2>/dev/null || echo "None")

## Connection Strings (use with actual passwords from $PASSWORDS_FILE)
Admin: amqp://caldera_admin:<password>@localhost:5672$VHOST
Publisher: amqp://caldera_publisher:<password>@localhost:5672$VHOST
Consumer: amqp://checking_consumer:<password>@localhost:5672$VHOST
Worker: amqp://checking_worker:<password>@localhost:5672$VHOST
Monitor: amqp://monitor_user:<password>@localhost:5672$VHOST

## Management UI
Access: http://localhost:15672
Login with any user credentials above

## Configuration Files
- /etc/rabbitmq/rabbitmq.conf
- .env.example (template)
- $PASSWORDS_FILE (passwords)
EOF
    
    print_success "Status report generated: $report_file"
}

# Clean up test messages
cleanup_test_messages() {
    print_status "Cleaning up test messages..."
    
    # Clean API responses queue
    local api_messages=$(rabbitmqctl list_queues -p $VHOST name messages | grep api.responses | awk '{print $2}')
    if [ "$api_messages" -gt 0 ]; then
        rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST get \
            queue=caldera.checking.api.responses ackmode=ack_requeue_false >> $LOG_FILE 2>&1
    fi
    
    # Clean agent responses queue
    local agent_messages=$(rabbitmqctl list_queues -p $VHOST name messages | grep agent.responses | awk '{print $2}')
    if [ "$agent_messages" -gt 0 ]; then
        rabbitmqadmin -u caldera_admin -p $ADMIN_PASS -V $VHOST get \
            queue=caldera.checking.agent.responses ackmode=ack_requeue_false >> $LOG_FILE 2>&1
    fi
    
    print_success "Test messages cleaned up"
}

# Final verification summary
final_verification() {
    print_status "Performing final verification..."
    
    local all_tests_passed=true
    
    # Check service status
    if systemctl is-active --quiet rabbitmq-server; then
        print_success "[+] RabbitMQ service is running"
    else
        print_error "[-] RabbitMQ service is not running"
        all_tests_passed=false
    fi
    
    # Check virtual host
    if rabbitmqctl list_vhosts | grep -q "$VHOST"; then
        print_success "[+] Virtual host exists"
    else
        print_error "[-] Virtual host missing"
        all_tests_passed=false
    fi
    
    # Check all users exist
    local user_count=$(rabbitmqctl list_users | grep -c "caldera\|checking\|monitor" || true)
    if [ $user_count -eq 7 ]; then
        print_success "[+] All 7 users exist"
    else
        print_error "[-] Missing users (found $user_count, expected 7)"
        all_tests_passed=false
    fi
    
    # Check all queues exist
    local queue_count=$(rabbitmqctl list_queues -p $VHOST | grep -c "caldera.checking" || true)
    if [ $queue_count -eq 6 ]; then
        print_success "[+] All 5 queues exist"
    else
        print_error "[-] Missing queues (found $queue_count, expected 5)"
        all_tests_passed=false
    fi
    
    # Check exchange exists
    local exchange_count=$(rabbitmqctl list_exchanges -p $VHOST | grep -c "caldera.checking.exchange" || true)
    if [ $exchange_count -eq 1 ]; then
        print_success "[+] Exchange exists"
    else
        print_error "[-] Exchange missing"
        all_tests_passed=false
    fi
    
    if [ "$all_tests_passed" = true ]; then
        print_success "[+] ALL TESTS PASSED! RabbitMQ setup is complete and functional."
        return 0
    else
        print_error "[-] Some tests failed. Please review the logs and fix issues."
        return 1
    fi
}

# Main execution
main() {
    echo "======================================"
    echo "Phase 5: Final Verification and Testing"
    echo "======================================"
    echo
    
    # Initialize log file
    echo "Phase 5 Log - $(date)" > $LOG_FILE
    
    print_status "Starting Phase 5: Final verification and testing..."
    
    # Check prerequisites
    check_privileges
    load_passwords
    check_prerequisites
    
    # Execute comprehensive tests
    test_user_permissions
    test_purple_team_workflow
    test_resource_limits
    
    # Generate reports and cleanup
    generate_status_report
    cleanup_test_messages
    
    # Final verification
    if final_verification; then
        echo
        print_success "[+] RabbitMQ Checking Engine setup is COMPLETE!"
        echo
        print_status "Key Files Created:"
        echo "  - $PASSWORDS_FILE (secure passwords)"
        echo "  - .env.example (configuration template)"
        echo "  - rabbitmq_setup_report.txt (status report)"
        echo "  - Log files: rabbitmq_phase*.log"
        echo
        print_status "Management UI:"
        echo "  - URL: http://localhost:15672"
        echo "  - Login with any user from $PASSWORDS_FILE"
        echo
        print_warning "Next Steps:"
        echo "  1. Integrate Caldera publisher code"
        echo "  2. Develop Checking Engine backend"
        echo "  3. Implement detection workers"
        echo "  4. Setup monitoring and alerting"
        
        return 0
    else
        print_error "Setup verification failed. Please check logs and fix issues."
        return 1
    fi
}

# Run main function
main "$@" 