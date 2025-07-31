# Caldera RabbitMQ Integration

This document describes how to integrate Caldera with RabbitMQ for the Checking Engine Purple Team platform.

## Overview

The integration adds a message publishing hook to Caldera's contact service that forwards execution results to RabbitMQ for Blue Team processing. When a Red Team agent reports execution results, Caldera automatically publishes these results to the `caldera.checking.instructions` queue for the Checking Engine to process.

## Integration Components

### 1. Modified Files

#### `app/service/contact_svc.py`
- **Method**: `_publish_to_queue()` - New method to publish messages to RabbitMQ
- **Hook Location**: `_save()` method - Called after each link execution result
- **Message Format**: JSON with operation details, execution results, and detection configurations

#### `conf/default.yml` 
- **Keys**: `checking_engine.*` (flattened) - RabbitMQ connection settings

#### `requirements.txt`
- **Dependency**: `aio-pika==9.4.3` - Async RabbitMQ client for Python

### 2. Message Flow

```
┌─────────────┐    ┌─────────────────────┐    ┌──────────────────────┐
│ Caldera     │───▶│ RabbitMQ Exchange   │───▶│ Instructions Queue   │
│ Red Team    │    │ caldera.checking.   │    │ caldera.checking.    │
│ Agent       │    │ exchange            │    │ instructions         │
└─────────────┘    └─────────────────────┘    └──────────────────────┘
                                                        │
                                                        ▼
                                               ┌──────────────────────┐
                                               │ Checking Engine      │
                                               │ Blue Team Backend    │
                                               └──────────────────────┘
```

## Setup Instructions

### Prerequisites

1. **RabbitMQ Setup Complete**: Ensure you've completed all phases from `expand/checking-engine/setup/mq_setup/README.md`
2. **Password Available**: Have the `caldera_publisher` password from `rabbitmq_passwords.txt`

### Step 1: Install Dependencies

```bash
# Install aio-pika for Caldera
cd /path/to/caldera
pip install aio-pika==9.4.3

# Or install from requirements
pip install -r requirements.txt
```

### Step 2: Configure RabbitMQ Connection

Edit `conf/default.yml` and set the RabbitMQ password:

```yaml
checking_engine.rabbitmq_host: localhost
checking_engine.rabbitmq_port: 5672
checking_engine.rabbitmq_vhost: /caldera_checking
checking_engine.rabbitmq_username: caldera_publisher
checking_engine.rabbitmq_password: 'YOUR_ACTUAL_PASSWORD_HERE'  # From rabbitmq_passwords.txt
checking_engine.rabbitmq_exchange: caldera.checking.exchange
checking_engine.rabbitmq_routing_key: caldera.execution.result
```

**To get the password:**
```bash
cd expand/checking-engine/setup/mq_setup/
grep caldera_publisher rabbitmq_passwords.txt
```

### Step 3: Test the Integration

#### Option A: Standalone Test
```bash
cd expand/checking-engine
python test_caldera_publisher.py
```

#### Option B: Test with Running Caldera
1. Start Caldera with the new configuration
2. Run a simple operation with an agent
3. Check RabbitMQ queues for messages

### Step 4: Verify Message Publishing

Check that messages are being published:

```bash
# Check queue message count
sudo rabbitmqctl list_queues -p /caldera_checking name messages

# Peek at message content (non-destructive)
rabbitmqadmin -u monitor_user -p <password> -V /caldera_checking \
  get queue=caldera.checking.instructions ackmode=reject_requeue_true

# Consume message (destructive)
rabbitmqadmin -u checking_consumer -p <password> -V /caldera_checking \
  get queue=caldera.checking.instructions ackmode=ack_requeue_false
```

## Message Format

### Published Message Structure

```json
{
  "timestamp": "2024-01-15T10:30:00.123456+00:00",
  "message_type": "link_result",
  "operation": {
    "name": "operation-name",
    "id": "op-uuid-12345",
    "start": "2024-01-15T10:00:00.000000+00:00"
  },
  "execution": {
    "link_id": "link-uuid-67890",
    "agent_host": "target-machine.local",
    "agent_paw": "agent-paw-abc123",
    "command": "whoami",
    "pid": 1234,
    "status": 0,
    "state": "SUCCESS",
    "result_data": "{\"stdout\":\"administrator\",\"stderr\":\"\",\"exit_code\":0}",
    "agent_reported_time": "2024-01-15T10:30:00.123456+00:00",
    "detections": {
      "api": {
        "siem": {
          "query": "search index=security user=administrator",
          "platform": "splunk"
        }
      },
      "agent": {
        "windows": {
          "command": "Get-EventLog Security -InstanceId 4624",
          "platform": "powershell"
        }
      }
    }
  }
}
```

### Detection Configuration

The `detections` field contains Blue Team detection instructions that are defined in the ability's `additional_info` section. These tell the Checking Engine how to search for evidence of the Red Team action.

**Example in ability YAML:**
```yaml
name: Discovery - Local Users
description: Enumerate local users
platforms:
  windows:
    command: net user
additional_info:
  detections:
    api:
      siem:
        query: "search index=security EventID=4798"
        platform: "splunk"
    agent:
      windows:
        command: "Get-EventLog Security -InstanceId 4798"
        platform: "powershell"
```

## Configuration Options

### RabbitMQ Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `rabbitmq_host` | `localhost` | RabbitMQ server hostname |
| `rabbitmq_port` | `5672` | RabbitMQ server port |
| `rabbitmq_vhost` | `/caldera_checking` | Virtual host for isolation |
| `rabbitmq_username` | `caldera_publisher` | Publisher user account |
| `rabbitmq_password` | `''` | **Required**: Publisher password |
| `rabbitmq_exchange` | `caldera.checking.exchange` | Topic exchange name |
| `rabbitmq_routing_key` | `caldera.execution.result` | Routing key for messages |

### Connection Parameters

The integration uses these `aio-pika` connection settings:
- **Timeout**: 5 seconds for initial connection
- **Heartbeat**: 600 seconds (10 minutes)
- **Blocked Connection Timeout**: 300 seconds (5 minutes)
- **Connection Type**: `connect_robust` (auto-reconnect)

## Error Handling

### Graceful Degradation

The integration is designed to **NOT** break Caldera if RabbitMQ is unavailable:

1. **ImportError**: If `aio-pika` is not installed, logs error and continues
2. **Connection Error**: If RabbitMQ is down, logs error and continues  
3. **Permission Error**: If user lacks permissions, logs error and continues
4. **Channel Error**: If exchange doesn't exist, logs error and continues

### Error Scenarios

| Error Type | Behavior | Log Level | Caldera Impact |
|------------|----------|-----------|----------------|
| Missing `aio-pika` | Continue without publishing | ERROR | None |
| RabbitMQ down | Continue without publishing | ERROR | None |
| Wrong credentials | Continue without publishing | ERROR | None |
| Missing exchange | Continue without publishing | ERROR | None |
| Empty password | Skip publishing with warning | WARNING | None |

### Troubleshooting

#### Common Issues

1. **"aio-pika library not installed"**
   ```bash
   pip install aio-pika==9.4.3
   ```

2. **"Failed to connect to RabbitMQ"**
   - Check if RabbitMQ is running: `sudo systemctl status rabbitmq-server`
   - Verify credentials in `conf/default.yml`
   - Test connection manually with `test_caldera_publisher.py`

3. **"RabbitMQ password not configured"**
   - Set the password in `conf/default.yml` from `rabbitmq_passwords.txt`

4. **"Access refused" errors**
   - Verify user permissions: `sudo rabbitmqctl list_user_permissions -p /caldera_checking caldera_publisher`
   - Ensure user has `management` tag: `sudo rabbitmqctl list_users`

#### Debug Steps

1. **Test RabbitMQ setup:**
   ```bash
   cd expand/checking-engine/setup/mq_setup
   ./05_final_verification.sh
   ```

2. **Test publisher independently:**
   ```bash
   cd expand/checking-engine
   python test_caldera_publisher.py
   ```

3. **Check Caldera logs:**
   - Look for "Successfully published message to RabbitMQ" (success)
   - Look for "Failed to connect to RabbitMQ" (connection issues)
   - Look for "RabbitMQ password not configured" (config issues)

## Security Considerations

### Least Privilege Access

The `caldera_publisher` user has minimal permissions:
- **Configure**: None (cannot create/delete exchanges or queues)
- **Write**: Only to `caldera.checking.exchange` 
- **Read**: None (fire-and-forget publishing)

### Credential Security

- Store RabbitMQ password in `conf/default.yml` with restricted file permissions
- Consider using environment variables in production
- Rotate passwords regularly (recommended: every 90 days)

### Network Security

- RabbitMQ management interface (port 15672) should be firewalled
- Consider TLS/SSL for production deployments
- Monitor connection attempts and failed authentications

## Performance Impact

### Minimal Overhead

The integration adds minimal overhead to Caldera:
- **Async Publishing**: Non-blocking message publishing
- **Connection Pooling**: `connect_robust` maintains persistent connections
- **Error Isolation**: RabbitMQ issues don't affect Red Team operations

### Scaling Considerations

- Each Caldera operation can generate hundreds of messages
- Monitor RabbitMQ queue depths during large operations
- Consider message batching for very high-throughput scenarios

---
