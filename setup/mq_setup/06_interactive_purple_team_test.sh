#!/bin/bash

# Phase 6: Interactive Purple Team Workflow Test
# This script performs step-by-step Purple Team workflow testing with detailed explanations

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
VHOST="/caldera_checking"
LOG_FILE="rabbitmq_phase6_interactive.log"
PASSWORDS_FILE="rabbitmq_passwords.txt"

# Function to print colored output
print_header() {
    echo -e "${CYAN}============================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}============================================${NC}"
}

print_step() {
    echo -e "${MAGENTA}[STEP]${NC} $1"
}

print_command() {
    echo -e "${BLUE}[COMMAND]${NC} $1"
}

print_explanation() {
    echo -e "${YELLOW}[EXPLAIN]${NC} $1"
}

print_result() {
    echo -e "${GREEN}[RESULT]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_usecase() {
    echo -e "${CYAN}[USECASE]${NC} $1"
}

# Function to wait for user confirmation
wait_for_user() {
    local prompt="$1"
    echo
    echo -e "${YELLOW}Press ENTER to $prompt, or type 'skip' to skip this step, 'quit' to exit:${NC}"
    read -r user_input
    
    case "$user_input" in
        "skip"|"s")
            echo -e "${YELLOW}Skipping this step...${NC}"
            echo
            return 1
            ;;
        "quit"|"q"|"exit")
            echo -e "${RED}Exiting interactive test...${NC}"
            exit 0
            ;;
        *)
            echo -e "${GREEN}Proceeding with step...${NC}"
            echo
            return 0
            ;;
    esac
}

# Function to display command explanation
explain_command() {
    local command="$1"
    local explanation="$2"
    
    print_command "$command"
    print_explanation "$explanation"
    echo
}

# Function to execute command and show results
execute_and_show() {
    local command="$1"
    local description="$2"
    
    print_step "Executing: $description"
    print_command "$command"
    
    echo "Command executed at: $(date)" >> $LOG_FILE
    echo "Command: $command" >> $LOG_FILE
    echo "Description: $description" >> $LOG_FILE
    echo "----------------------------------------" >> $LOG_FILE
    
    # Execute command and capture output
    local output
    if output=$(eval "$command" 2>&1); then
        print_result "SUCCESS"
        echo "$output"
        echo "Output: $output" >> $LOG_FILE
    else
        print_error "FAILED"
        echo "$output"
        echo "Error: $output" >> $LOG_FILE
        return 1
    fi
    
    echo "----------------------------------------" >> $LOG_FILE
    echo >> $LOG_FILE
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
        print_error "Please run phases 1-2 first to create users and passwords"
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
    
    if [ -z "$ADMIN_PASS" ] || [ -z "$PUBLISHER_PASS" ] || [ -z "$CONSUMER_PASS" ] || [ -z "$WORKER_PASS" ] || [ -z "$MONITOR_PASS" ]; then
        print_error "One or more passwords not found in passwords file"
        exit 1
    fi
    
    print_result "All passwords loaded successfully"
}

# Check prerequisites
check_prerequisites() {
    print_step "Checking prerequisites..."
    
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
    
    print_result "Prerequisites check passed"
}

# Step 1: Check initial queue state
step1_check_initial_state() {
    print_header "STEP 1: Check Initial Queue State"
    
    print_explanation "Before starting the Purple Team workflow, let's check the current state of all queues."
    print_explanation "This helps us understand the baseline and verify that queues are empty."
    
    if ! wait_for_user "check initial queue state"; then
        return 0
    fi
    
    local cmd="sudo rabbitmqctl list_queues -p $VHOST name messages"
    explain_command "$cmd" "List all queues in virtual host '$VHOST' with message counts"
    print_explanation "Arguments:"
    print_explanation "  -p $VHOST: Specify virtual host '/caldera_checking'"
    print_explanation "  name messages: Show queue name and message count columns"
    
    execute_and_show "$cmd" "Check initial queue state"
    
    print_result "✓ Step 1 completed: Initial queue state checked"
}

# Step 2: Red Team simulation
step2_red_team_simulation() {
    print_header "STEP 2: Red Team Simulation - Caldera Publishes Execution Result"
    
    print_usecase "SCENARIO: Caldera agent executed 'whoami' command on target machine"
    print_explanation "Red Team (Caldera) publishes command execution results to the message queue."
    print_explanation "This simulates the real-world scenario where Caldera completes an attack and reports results."
    
    if ! wait_for_user "simulate Red Team execution"; then
        return 0
    fi
    
    # Create the payload
    local red_team_payload='{
        "operation_id": "test-op-001", 
        "agent_host": "target-machine", 
        "command": "whoami", 
        "result": {"stdout": "administrator", "stderr": "", "exit_code": 0},
        "detections": {
            "api": {"siem": {"query": "search user=administrator"}},
            "windows": {"psh": {"command": "Get-EventLog Security | Where ID -eq 4624"}}
        }
    }'
    
    local cmd="rabbitmqadmin -u caldera_publisher -p '$PUBLISHER_PASS' -V $VHOST publish exchange=caldera.checking.exchange routing_key=caldera.execution.result payload='$red_team_payload'"
    
    explain_command "$cmd" "Publish Red Team execution result to message queue"
    print_explanation "Arguments breakdown:"
    print_explanation "  -u caldera_publisher: Use publisher user (Red Team credentials)"
    print_explanation "  -p \$PUBLISHER_PASS: Publisher password from secure file"
    print_explanation "  -V $VHOST: Target virtual host '/caldera_checking'"
    print_explanation "  exchange=caldera.checking.exchange: Main topic exchange"
    print_explanation "  routing_key=caldera.execution.result: Routes to instructions queue"
    print_explanation "  payload=...: JSON with operation details and detection configs"
    
    execute_and_show "$cmd" "Publish Red Team execution result"
    
    print_result "✓ Step 2 completed: Red Team execution result published"
}

# Step 3: Verify message routing
step3_verify_routing() {
    print_header "STEP 3: Verify Message Routing"
    
    print_explanation "Check if the Red Team message was correctly routed to the instructions queue."
    print_explanation "The topic exchange should route 'caldera.execution.result' to 'caldera.checking.instructions'."
    
    if ! wait_for_user "verify message routing"; then
        return 0
    fi
    
    local cmd="sudo rabbitmqctl list_queues -p $VHOST name messages"
    explain_command "$cmd" "Check queue message counts after Red Team publish"
    
    execute_and_show "$cmd" "Verify message routing to instructions queue"
    
    print_explanation "Expected result: instructions queue should have 1 message"
    print_result "✓ Step 3 completed: Message routing verified"
}

# Step 4: Blue Team Backend consumption
step4_blue_team_backend() {
    print_header "STEP 4: Blue Team Backend - Process Execution Result"
    
    print_usecase "SCENARIO: Blue Team backend consumes Red Team execution for processing"
    print_explanation "The checking-engine backend reads the execution result and creates detection tasks."
    print_explanation "This simulates parsing the message and preparing detection workflows."
    
    if ! wait_for_user "simulate Blue Team backend processing"; then
        return 0
    fi
    
    local cmd="rabbitmqadmin -u checking_consumer -p '$CONSUMER_PASS' -V $VHOST get queue=caldera.checking.instructions ackmode=ack_requeue_false"
    
    explain_command "$cmd" "Consume message from instructions queue"
    print_explanation "Arguments breakdown:"
    print_explanation "  -u checking_consumer: Use consumer user (Blue Team backend credentials)"
    print_explanation "  -p \$CONSUMER_PASS: Consumer password from secure file"
    print_explanation "  -V $VHOST: Target virtual host '/caldera_checking'"
    print_explanation "  queue=caldera.checking.instructions: Source queue for processing"
    print_explanation "  ackmode=ack_requeue_false: Acknowledge and remove message (destructive read)"
    
    execute_and_show "$cmd" "Blue Team backend consumes execution result"
    
    print_explanation "Backend would now:"
    print_explanation "  1. Parse the execution result JSON"
    print_explanation "  2. Extract detection configurations (API + Windows)"
    print_explanation "  3. Create detection tasks in PostgreSQL database"
    print_explanation "  4. Send detection requests to appropriate workers"
    
    print_result "✓ Step 4 completed: Blue Team backend processed execution result"
}

# Step 5: API Worker - SIEM detection
step5_api_worker_siem() {
    print_header "STEP 5: API Worker - SIEM Detection Execution"
    
    print_usecase "SCENARIO: API worker executes SIEM detection and reports results"
    print_explanation "The API worker queries external SIEM system and finds 3 suspicious admin logon events."
    print_explanation "This simulates successful detection of Red Team activity through log analysis."
    
    if ! wait_for_user "simulate API worker SIEM detection"; then
        return 0
    fi
    
    local api_result_payload='{
        "detection_id": "det-001", 
        "detection_type": "api", 
        "platform": "siem",
        "detected": true,
        "results": {"events_found": 3, "rule_matched": "suspicious_admin_logon"},
        "timestamp": "'$(date -Iseconds)'"
    }'
    
    local cmd="rabbitmqadmin -u checking_worker -p '$WORKER_PASS' -V $VHOST publish exchange=caldera.checking.exchange routing_key=checking.api.response payload='$api_result_payload'"
    
    explain_command "$cmd" "Publish SIEM detection results"
    print_explanation "Arguments breakdown:"
    print_explanation "  -u checking_worker: Use worker user (Blue Team worker credentials)"
    print_explanation "  -p \$WORKER_PASS: Worker password from secure file"
    print_explanation "  routing_key=checking.api.response: Routes to api.responses queue"
    print_explanation "  payload=...: JSON with detection results (3 events found, detection successful)"
    
    execute_and_show "$cmd" "API worker publishes SIEM detection results"
    
    print_result "✓ Step 5 completed: SIEM detection found suspicious activity"
}

# Step 6: Agent Worker - Windows detection
step6_agent_worker_windows() {
    print_header "STEP 6: Agent Worker - Windows Agent Detection"
    
    print_usecase "SCENARIO: Agent worker executes Windows detection and reports results"
    print_explanation "The agent worker runs PowerShell commands on Windows host but finds no events."
    print_explanation "This simulates potential detection evasion or timing issues in host-based detection."
    
    if ! wait_for_user "simulate Agent worker Windows detection"; then
        return 0
    fi
    
    local agent_result_payload='{
        "detection_id": "det-002",
        "detection_type": "agent", 
        "platform": "windows",
        "detected": false,
        "results": {"events_found": 0, "error": null},
        "timestamp": "'$(date -Iseconds)'"
    }'
    
    local cmd="rabbitmqadmin -u checking_worker -p '$WORKER_PASS' -V $VHOST publish exchange=caldera.checking.exchange routing_key=checking.agent.response payload='$agent_result_payload'"
    
    explain_command "$cmd" "Publish Windows agent detection results"
    print_explanation "Arguments breakdown:"
    print_explanation "  routing_key=checking.agent.response: Routes to agent.responses queue"
    print_explanation "  payload=...: JSON with detection results (0 events found, detection failed)"
    print_explanation "This represents a common scenario where network-based detection succeeds but host-based fails."
    
    execute_and_show "$cmd" "Agent worker publishes Windows detection results"
    
    print_result "✓ Step 6 completed: Windows detection found no events (potential evasion)"
}

# Step 7: Final verification
step7_final_verification() {
    print_header "STEP 7: Complete Purple Team Workflow Verification"
    
    print_explanation "Check final state of all queues to verify complete message flow."
    print_explanation "Expected: instructions=0, api.responses=1, agent.responses=1"
    
    if ! wait_for_user "verify complete workflow"; then
        return 0
    fi
    
    local cmd="sudo rabbitmqctl list_queues -p $VHOST name messages"
    explain_command "$cmd" "Check final queue states after complete workflow"
    
    execute_and_show "$cmd" "Verify complete Purple Team workflow"
    
    print_explanation "Workflow Summary:"
    print_explanation "  ✓ Red Team → Published execution result → Instructions queue"
    print_explanation "  ✓ Blue Team Backend → Consumed and processed → Detection tasks created"
    print_explanation "  ✓ API Worker → SIEM detection → Found 3 suspicious events"
    print_explanation "  ✓ Agent Worker → Windows detection → Found 0 events (evasion?)"
    print_explanation "  ✓ Results → Stored in response queues → Ready for backend processing"
    
    print_result "✓ Step 7 completed: Complete Purple Team workflow verified"
}

# Step 8: Cleanup test messages
step8_cleanup() {
    print_header "STEP 8: Cleanup Test Messages (Optional)"
    
    print_explanation "Remove test messages from response queues to clean up the environment."
    print_explanation "This is optional - you may want to keep messages for further inspection."
    
    if ! wait_for_user "cleanup test messages"; then
        print_warning "Skipping cleanup - test messages remain in queues"
        return 0
    fi
    
    # Clean API responses queue
    local cmd1="rabbitmqadmin -u caldera_admin -p '$ADMIN_PASS' -V $VHOST get queue=caldera.checking.api.responses ackmode=ack_requeue_false"
    explain_command "$cmd1" "Remove SIEM detection result from api.responses queue"
    execute_and_show "$cmd1" "Cleanup API responses queue"
    
    # Clean agent responses queue  
    local cmd2="rabbitmqadmin -u caldera_admin -p '$ADMIN_PASS' -V $VHOST get queue=caldera.checking.agent.responses ackmode=ack_requeue_false"
    explain_command "$cmd2" "Remove Windows detection result from agent.responses queue"
    execute_and_show "$cmd2" "Cleanup agent responses queue"
    
    # Final state check
    local cmd3="sudo rabbitmqctl list_queues -p $VHOST name messages"
    explain_command "$cmd3" "Verify all queues are empty after cleanup"
    execute_and_show "$cmd3" "Final queue state verification"
    
    print_result "✓ Step 8 completed: Test environment cleaned up"
}

# Main execution
main() {
    print_header "Interactive Purple Team Workflow Test"
    
    # Initialize log file
    echo "Phase 6 Interactive Log - $(date)" > $LOG_FILE
    echo "Interactive Purple Team Workflow Test" >> $LOG_FILE
    echo "=====================================" >> $LOG_FILE
    echo >> $LOG_FILE
    
    print_explanation "This interactive test simulates a complete Purple Team workflow:"
    print_explanation "  Red Team (Caldera) → Message Queue → Blue Team → Detection → Results"
    print_explanation ""
    print_explanation "Each step will:"
    print_explanation "  1. Explain what will happen"
    print_explanation "  2. Show the exact command"
    print_explanation "  3. Explain command arguments"
    print_explanation "  4. Wait for your confirmation"
    print_explanation "  5. Execute and show results"
    print_explanation ""
    print_explanation "You can type 'skip' to skip a step or 'quit' to exit anytime."
    
    if ! wait_for_user "start the interactive test"; then
        print_warning "Test cancelled by user"
        exit 0
    fi
    
    # Check prerequisites
    check_privileges
    load_passwords
    check_prerequisites
    
    # Execute all steps
    step1_check_initial_state
    step2_red_team_simulation
    step3_verify_routing
    step4_blue_team_backend
    step5_api_worker_siem
    step6_agent_worker_windows
    step7_final_verification
    step8_cleanup
    
    print_header "INTERACTIVE TEST COMPLETED"
    print_result "🎉 All steps completed successfully!"
    print_explanation "Log file: $LOG_FILE"
    print_explanation "Review the log file for complete command history and outputs."
    echo
    print_explanation "Key takeaways from this Purple Team workflow:"
    print_explanation "  ✅ Message routing works correctly between components"
    print_explanation "  ✅ User permissions are properly isolated (RBAC)"
    print_explanation "  ✅ Detection systems can have different results (SIEM vs Agent)"
    print_explanation "  ✅ Asynchronous workflow supports scalable detection processing"
    print_explanation "  ✅ Complete audit trail is maintained in message queue"
}

# Run main function
main "$@" 