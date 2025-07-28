# RabbitMQ Setup for Checking Engine

This directory contains RabbitMQ setup scripts and documentation for the Checking Engine message broker infrastructure.

## Overview

The Checking Engine uses RabbitMQ as a message broker to facilitate communication between:
- **Caldera (Red Team)**: Publishes execution results
- **Checking Engine Backend**: Consumes instructions and processes detection tasks  
- **Detection Workers**: Execute detection queries and publish results

## Architecture

```
Caldera → RabbitMQ Exchange → Checking Engine → Detection Workers → Results
```

### Message Flow

1. **Caldera Publisher** → `caldera.checking.exchange` → `caldera.checking.instructions` queue
2. **Checking Engine** consumes from `caldera.checking.instructions`
3. **Detection Workers** publish to:
   - `caldera.checking.api.responses` (for API-based detections)
   - `caldera.checking.agent.responses` (for agent-based detections)

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Root or sudo access
- PostgreSQL database already configured (see `../db_setup/`)

## Quick Setup

### Option 1: Phase-by-Phase Setup (Recommended)

Execute each phase in sequence for better control and debugging:

```bash
cd setup/mq_setup/

# Phase 1: Install RabbitMQ
sudo ./01_install_rabbitmq.sh

# Phase 2: Setup virtual host and users
sudo ./02_setup_vhost_users.sh

# Phase 3: Setup exchanges and queues
sudo ./03_setup_exchanges_queues.sh

# Phase 4: Configure limits and security
sudo ./04_configure_limits_security.sh

# Phase 5: Final verification
sudo ./05_final_verification.sh

# Phase 6: Interactive Purple Team test (optional)
sudo ./06_interactive_purple_team_test.sh
```

### Option 2: Manual Setup

Follow the step-by-step instructions below for manual installation.

## Setup Files Overview

| File | Description | Purpose |
|------|-------------|---------|
| `01_install_rabbitmq.sh` | Install RabbitMQ server and management plugin | Phase 1: Basic installation |
| `02_setup_vhost_users.sh` | Create virtual host and users with permissions | Phase 2: Security setup |
| `03_setup_exchanges_queues.sh` | Create exchanges, queues, and bindings | Phase 3: Message routing |
| `04_configure_limits_security.sh` | Set resource limits and security policies | Phase 4: Production config |
| `05_final_verification.sh` | Comprehensive testing of the setup | Phase 5: Verification |
| `06_interactive_purple_team_test.sh` | Interactive Purple Team workflow test | Phase 6: End-to-end testing |
| `cleanup_rabbitmq.sh` | Remove RabbitMQ setup completely | Cleanup utility |
| `flush_all_queues.sh` | Clear all messages from queues | Testing utility |

Generated files after setup:
- `rabbitmq_passwords.txt` - Secure passwords for all users
- `rabbitmq_setup_report.txt` - Complete setup status report
- `rabbitmq_phase*.log` - Detailed logs from each phase

## Manual Installation Steps

### Step 1: Install RabbitMQ Server

```bash
# Update package list
sudo apt update

# Install RabbitMQ server
sudo apt install rabbitmq-server

# Enable service to start on boot
sudo systemctl enable rabbitmq-server

# Start RabbitMQ service
sudo systemctl start rabbitmq-server
```

**✅ Verify Step 1:**
```bash
# Check service status
sudo systemctl status rabbitmq-server

# Should show "active (running)"
# Check if service is enabled
sudo systemctl is-enabled rabbitmq-server

# Should return "enabled"
```

### Step 2: Enable Management Plugin

```bash
# Enable web management interface
sudo rabbitmq-plugins enable rabbitmq_management

# Install management admin tool
sudo apt install rabbitmq-server rabbitmqadmin

# Restart service
sudo systemctl restart rabbitmq-server
```

**✅ Verify Step 2:**
```bash
# Check if management plugin is enabled
sudo rabbitmq-plugins list | grep rabbitmq_management

# Should show [E*] indicating enabled
# Test management interface access
curl -s http://localhost:15672 | grep RabbitMQ

# Should return HTML containing "RabbitMQ Management"
# Or open browser to http://localhost:15672 (login with guest/guest initially)
```

### Step 3: Create Virtual Host

```bash
# Create dedicated virtual host for checking engine
sudo rabbitmqctl add_vhost /caldera_checking
```

**✅ Verify Step 3:**
```bash
# List all virtual hosts
sudo rabbitmqctl list_vhosts

# Should show /caldera_checking in the list
```

### Step 4: Create Users with Role-Based Access

```bash
# 1. Admin user (for initial setup and management)
sudo rabbitmqctl add_user caldera_admin $(openssl rand -base64 32)
sudo rabbitmqctl set_user_tags caldera_admin administrator
sudo rabbitmqctl set_permissions -p /caldera_checking caldera_admin ".*" ".*" ".*"

# 2. Caldera publisher (publishes execution results)
sudo rabbitmqctl add_user caldera_publisher $(openssl rand -base64 24)
sudo rabbitmqctl set_user_tags caldera_publisher management
sudo rabbitmqctl set_permissions -p /caldera_checking caldera_publisher \
  "^$" \
  "^caldera\.checking\.exchange$" \
  "^$"

# 3. Checking engine consumer (consumes instructions)
sudo rabbitmqctl add_user checking_consumer $(openssl rand -base64 24)
sudo rabbitmqctl set_user_tags checking_consumer management
sudo rabbitmqctl set_permissions -p /caldera_checking checking_consumer \
  "^$" \
  "^$" \
  "^caldera\.checking\.instructions$"

# 4. Detection workers (publish results)
sudo rabbitmqctl add_user checking_worker $(openssl rand -base64 24)
sudo rabbitmqctl set_user_tags checking_worker management
sudo rabbitmqctl set_permissions -p /caldera_checking checking_worker \
  "^$" \
  "^caldera\.checking\.(exchange|(api|agent)\.responses)$" \
  "^$"

# 5. Monitor user (read-only access for monitoring)
sudo rabbitmqctl add_user monitor_user $(openssl rand -base64 24)
sudo rabbitmqctl set_user_tags monitor_user monitoring
sudo rabbitmqctl set_permissions -p /caldera_checking monitor_user \
  "^$" \
  "^$" \
  "^caldera\.checking\..*$"
```

**✅ Verify Step 4:**
```bash
# List all users
sudo rabbitmqctl list_users

# Should show all 5 users with their roles
# Check user permissions for virtual host
sudo rabbitmqctl list_permissions -p /caldera_checking

# Should show permissions for all users
# Save passwords for later use (IMPORTANT!)
echo "Save these passwords securely:"
sudo rabbitmqctl list_users
```

### Step 5: Create Exchange and Queues

```bash
# Get admin password (replace with actual password from step 4)
ADMIN_PASS="<your_admin_password_from_step_4>"

# Create main exchange
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare exchange \
  name=caldera.checking.exchange type=topic durable=true

# Create queues
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare queue \
  name=caldera.checking.instructions durable=true

rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare queue \
  name=caldera.checking.api.responses durable=true

rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare queue \
  name=caldera.checking.agent.responses durable=true

# Bind queues to exchange
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare binding \
  source=caldera.checking.exchange \
  destination=caldera.checking.instructions \
  routing_key=caldera.execution.result

rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare binding \
  source=caldera.checking.exchange \
  destination=caldera.checking.api.responses \
  routing_key=checking.api.response

rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare binding \
  source=caldera.checking.exchange \
  destination=caldera.checking.agent.responses \
  routing_key=checking.agent.response
```

**✅ Verify Step 5:**
```bash
# List exchanges in the virtual host
sudo rabbitmqctl list_exchanges -p /caldera_checking

# Should show caldera.checking.exchange
# List queues in the virtual host
sudo rabbitmqctl list_queues -p /caldera_checking

# Should show all 3 queues with 0 messages initially
# List bindings to verify routing
sudo rabbitmqctl list_bindings -p /caldera_checking

# Should show 3 bindings from exchange to queues
# Test message publishing and routing
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking publish \
  exchange=caldera.checking.exchange \
  routing_key=caldera.execution.result \
  payload='{"test": "verification"}'

# Check if message was routed to instructions queue
sudo rabbitmqctl list_queues -p /caldera_checking name messages

# instructions queue should show 1 message
```

### Step 6: Configure Resource Limits

```bash
# Set connection limits per user
sudo rabbitmqctl set_user_limits -p /caldera_checking caldera_publisher '{"max-connections": 100}'
sudo rabbitmqctl set_user_limits -p /caldera_checking checking_consumer '{"max-connections": 100}'
sudo rabbitmqctl set_user_limits -p /caldera_checking checking_worker '{"max-connections": 100}'

# Set queue policies
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking declare policy \
  name=caldera-checking-limits \
  pattern="^caldera\.checking\..*" \
  definition='{"max-length": 10000, "message-ttl": 3600000, "ha-mode": "all"}'
```

**✅ Verify Step 6:**
```bash
# Check user connection limits (check each user individually)
sudo rabbitmqctl list_user_limits --user caldera_publisher
sudo rabbitmqctl list_user_limits --user checking_consumer  
sudo rabbitmqctl list_user_limits --user checking_worker

# Should show connection limits for each user
# Check queue policies
sudo rabbitmqctl list_policies -p /caldera_checking

# Should show caldera-checking-limits policy
# Verify policy is applied to queues
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking list queues policy

# Should show policy applied to all checking queues
```

### Step 7: Firewall Configuration

```bash
# Allow RabbitMQ ports
sudo ufw allow 5672/tcp   # AMQP port
sudo ufw allow 15672/tcp  # Management UI port

# Reload firewall
sudo ufw reload
```

**✅ Verify Step 7:**
```bash
# Check firewall status
sudo ufw status | grep -E "(5672|15672)"

# Should show ALLOW rules for both ports
# Test port accessibility
nc -z localhost 5672 && echo "AMQP port accessible" || echo "AMQP port not accessible"
nc -z localhost 15672 && echo "Management port accessible" || echo "Management port not accessible"

# Both should show "accessible"
# Test external connectivity (if needed)
telnet localhost 5672  # Should connect (press Ctrl+C to exit)
```

### Step 8: Security Cleanup and Final Verification

```bash
# Remove default guest user for security
sudo rabbitmqctl delete_user guest

# Create password file for reference
cat > rabbitmq_passwords_manual.txt << EOF
# RabbitMQ Passwords - Created $(date)
# SAVE THESE PASSWORDS SECURELY!

CALDERA_ADMIN_PASSWORD=<password_from_step_4>
CALDERA_PUBLISHER_PASSWORD=<password_from_step_4>
CHECKING_CONSUMER_PASSWORD=<password_from_step_4>
CHECKING_WORKER_PASSWORD=<password_from_step_4>
MONITOR_USER_PASSWORD=<password_from_step_4>
EOF

chmod 600 rabbitmq_passwords_manual.txt
```

**✅ Final Verification: End-to-End Purple Team Workflow**
```bash
# === SYSTEM HEALTH CHECK ===
echo "=== System Health and Readiness ==="
sudo rabbitmqctl status | grep -E "(Status|Uptime|Memory|Disk)"
sudo rabbitmqctl node_health_check
echo "✓ RabbitMQ server is healthy and ready for production"

# === AUTHENTICATION VERIFICATION ===
echo "=== Testing User Authentication ==="
sudo rabbitmqctl authenticate_user caldera_admin "your_admin_password"
echo "✓ All users can authenticate successfully"

# === COMPLETE PURPLE TEAM SIMULATION ===
echo "=== SIMULATION: Complete Purple Team Exercise ==="

# 1. RED TEAM: Caldera publishes execution result
echo "🔴 RED TEAM: Caldera agent executes command and reports result"
rabbitmqadmin -u caldera_publisher -p "your_publisher_password" -V /caldera_checking publish \
  exchange=caldera.checking.exchange \
  routing_key=caldera.execution.result \
  payload='{
    "operation": "Purple Team Exercise",
    "agent": "target-server-01", 
    "command": "net user administrator /domain",
    "result": {"stdout": "User found", "exit_code": 0},
    "timestamp": "'$(date -Iseconds)'",
    "detections": {
      "api": {"splunk": {"query": "index=windows EventCode=4624 User=administrator"}},
      "agent": {"windows": {"cmd": "Get-WinEvent -FilterHashtable @{LogName=Security;ID=4624}"}}
    }
  }'
echo "→ Message published: Red Team execution result sent to Blue Team"

# 2. BLUE TEAM BACKEND: Process execution and create detection tasks  
echo "🔵 BLUE TEAM BACKEND: Processing Red Team execution"
EXECUTION_MSG=$(rabbitmqadmin -u checking_consumer -p "your_consumer_password" -V /caldera_checking get \
  queue=caldera.checking.instructions ackmode=ack_requeue_false)
echo "$EXECUTION_MSG" | head -3
echo "→ Message consumed: Backend creates detection tasks for SIEM and Windows agent"

# 3. API WORKER: Execute SIEM detection
echo "🔍 API WORKER: Executing SIEM detection query"
rabbitmqadmin -u checking_worker -p "your_worker_password" -V /caldera_checking publish \
  exchange=caldera.checking.exchange \
  routing_key=checking.api.response \
  payload='{
    "detection_type": "api",
    "platform": "splunk", 
    "detected": true,
    "events_found": 5,
    "rule_triggered": "Suspicious Admin Activity",
    "confidence": 0.85,
    "timestamp": "'$(date -Iseconds)'"
  }'
echo "→ SIEM Detection: DETECTED suspicious admin activity (5 events found)"

# 4. AGENT WORKER: Execute Windows agent detection
echo "🔍 AGENT WORKER: Executing Windows agent detection"
rabbitmqadmin -u checking_worker -p "your_worker_password" -V /caldera_checking publish \
  exchange=caldera.checking.exchange \
  routing_key=checking.agent.response \
  payload='{
    "detection_type": "agent",
    "platform": "windows",
    "detected": false, 
    "events_found": 0,
    "error": null,
    "note": "Activity may have been cleaned or evaded detection",
    "timestamp": "'$(date -Iseconds)'"
  }'
echo "→ Agent Detection: NOT DETECTED (possible evasion technique used)"

# 5. MONITORING: View complete exercise results
echo "📊 MONITORING: Purple Team Exercise Summary"
rabbitmqadmin -u monitor_user -p "your_monitor_password" -V /caldera_checking list queues name messages

echo ""
echo "🎯 PURPLE TEAM EXERCISE RESULTS:"
echo "   ✅ Red Team: Successfully executed command and bypassed agent detection"
echo "   ✅ Blue Team: SIEM detected activity, but endpoint agent missed it"  
echo "   📈 Learning: Need to improve endpoint detection coverage"
echo "   🔄 Feedback Loop: Red Team techniques vs Blue Team detection capabilities"

echo ""
echo "🎉 ✅ MANUAL SETUP COMPLETED SUCCESSFULLY!"
echo "🚀 Ready for production Purple Team operations!"
echo ""
echo "Next Steps:"
echo "1. 📝 Update application configs with saved passwords"
echo "2. 🔧 Deploy Checking Engine backend to consume instructions"  
echo "3. 👥 Deploy detection workers for API and agent platforms"
echo "4. 📊 Setup monitoring dashboards using monitor_user"
echo "5. 🔄 Configure Caldera to publish to caldera.checking.exchange"
```

## Configuration Files

### RabbitMQ Server Configuration

Create `/etc/rabbitmq/rabbitmq.conf`:

```ini
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

# SSL (optional - recommended for production)
# listeners.ssl.default = 5671
# ssl_options.cacertfile = /etc/rabbitmq/ssl/ca_certificate.pem
# ssl_options.certfile = /etc/rabbitmq/ssl/server_certificate.pem  
# ssl_options.keyfile = /etc/rabbitmq/ssl/server_key.pem
```

### Environment Configuration

Create `.env` file in your project root:

```bash
# RabbitMQ Connection Settings
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_VHOST=/caldera_checking
RABBITMQ_MANAGEMENT_PORT=15672

# User Credentials (replace with actual generated passwords)
RABBITMQ_ADMIN_USER=caldera_admin
RABBITMQ_ADMIN_PASS=<generated_password>

RABBITMQ_PUBLISHER_USER=caldera_publisher
RABBITMQ_PUBLISHER_PASS=<generated_password>

RABBITMQ_CONSUMER_USER=checking_consumer
RABBITMQ_CONSUMER_PASS=<generated_password>

RABBITMQ_WORKER_USER=checking_worker
RABBITMQ_WORKER_PASS=<generated_password>

RABBITMQ_MONITOR_USER=monitor_user
RABBITMQ_MONITOR_PASS=<generated_password>

# Exchange and Queue Names
RABBITMQ_EXCHANGE=caldera.checking.exchange
RABBITMQ_INSTRUCTIONS_QUEUE=caldera.checking.instructions
RABBITMQ_API_RESPONSES_QUEUE=caldera.checking.api.responses
RABBITMQ_AGENT_RESPONSES_QUEUE=caldera.checking.agent.responses

# Routing Keys
ROUTING_KEY_EXECUTION_RESULT=caldera.execution.result
ROUTING_KEY_API_RESPONSE=checking.api.response
ROUTING_KEY_AGENT_RESPONSE=checking.agent.response
```

## Security Considerations

### User Permission Matrix

| User | Role | Tags | Configure | Write | Read | Purpose |
|------|------|------|-----------|-------|------|---------|
| `caldera_admin` | Administrator | `administrator` | `.*` | `.*` | `.*` | Resource management |
| `caldera_publisher` | Publisher | `management` | `^$` | `^caldera\.checking\.exchange$` | `^$` | Publish execution results |
| `checking_consumer` | Consumer | `management` | `^$` | `^$` | `^caldera\.checking\.instructions$` | Consume instructions |
| `checking_worker` | Worker | `management` | `^$` | `^caldera\.checking\.(exchange\|(api\|agent)\.responses)$` | `^$` | Publish detection results |
| `monitor_user` | Monitor | `monitoring` | `^$` | `^$` | `^caldera\.checking\..*$` | Read-only monitoring |

### Security Best Practices

1. **Change Default Passwords**: Always generate strong passwords for all users
2. **Remove Guest User**: Delete the default guest user for security
3. **Use SSL/TLS**: Enable SSL for production deployments
4. **Firewall Rules**: Only open necessary ports
5. **Regular Updates**: Keep RabbitMQ server updated
6. **Monitor Access**: Use monitor_user for logging and alerting

## Verification

### Basic Health Check

```bash
# Check RabbitMQ status
sudo systemctl status rabbitmq-server

# Check users
sudo rabbitmqctl list_users

# Check virtual hosts
sudo rabbitmqctl list_vhosts

# Check queues
sudo rabbitmqctl list_queues -p /caldera_checking

# Check exchanges
sudo rabbitmqctl list_exchanges -p /caldera_checking
```

### Test Message Publishing

```bash
# Test with admin user
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking publish \
  exchange=caldera.checking.exchange \
  routing_key=caldera.execution.result \
  payload='{"test": "message", "timestamp": "'$(date -Iseconds)'"}'

# Verify message was queued
rabbitmqadmin -u caldera_admin -p "$ADMIN_PASS" -V /caldera_checking get \
  queue=caldera.checking.instructions
```

### Web Management Interface

1. Open browser to `http://localhost:15672`
2. Login with `caldera_admin` credentials
3. Navigate to:
   - **Virtual Hosts** → `/caldera_checking`
   - **Exchanges** → `caldera.checking.exchange`
   - **Queues** → Verify all queues exist
   - **Admin** → **Users** → Verify all users with correct permissions

## Troubleshooting

### Common Issues

**Connection Refused**
```bash
# Check if service is running
sudo systemctl status rabbitmq-server

# Check logs
sudo journalctl -u rabbitmq-server -f

# Restart service
sudo systemctl restart rabbitmq-server
```

**Permission Denied**
```bash
# Check user permissions
sudo rabbitmqctl list_user_permissions <username>

# Check virtual host permissions
sudo rabbitmqctl list_permissions -p /caldera_checking
```

**Management Plugin Not Available**
```bash
# Enable management plugin
sudo rabbitmq-plugins enable rabbitmq_management
sudo systemctl restart rabbitmq-server
```

**Memory Warnings**
```bash
# Check memory usage
sudo rabbitmqctl status | grep memory

# Adjust memory limits in rabbitmq.conf
sudo nano /etc/rabbitmq/rabbitmq.conf
```

## Additional Tools

### Flush All Queue Messages

To remove all messages from queues for testing:

```bash
sudo ./flush_all_queues.sh
```

## Cleanup

To completely remove RabbitMQ setup:

```bash
sudo ./cleanup_rabbitmq.sh
```

Or manually:

```bash
# Stop service
sudo systemctl stop rabbitmq-server

# Remove virtual host (removes all queues, exchanges, bindings)
sudo rabbitmqctl delete_vhost /caldera_checking

# Remove users
sudo rabbitmqctl delete_user caldera_admin
sudo rabbitmqctl delete_user caldera_publisher  
sudo rabbitmqctl delete_user checking_consumer
sudo rabbitmqctl delete_user checking_worker
sudo rabbitmqctl delete_user monitor_user

# Optionally remove RabbitMQ completely
sudo apt remove --purge rabbitmq-server
sudo rm -rf /var/lib/rabbitmq
sudo rm -rf /etc/rabbitmq
```

## Next Steps

After successful RabbitMQ setup:

1. **Configure Caldera Integration**: Update `app/service/contact_svc.py` with RabbitMQ publisher
2. **Develop Checking Engine Backend**: Create message consumer and detection orchestrator
3. **Implement Detection Workers**: API workers and agent workers
4. **Setup Monitoring**: Configure dashboards and alerting

For more information, see:
- `../db_setup/README.md` - Database configuration
- `../../docs/architecture.md` - Overall system design
- `../../src/` - Implementation code (when available)

---

**Note**: This setup creates a production-ready RabbitMQ configuration with proper security and resource limits. Always test in a development environment first. 