# RabbitMQ Architecture for Checking Engine

This document provides a comprehensive analysis of the RabbitMQ message broker architecture designed for the Checking Engine Purple Team platform.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Message Flow Design](#message-flow-design)
3. [Security Model](#security-model)
4. [Exchange and Queue Structure](#exchange-and-queue-structure)
5. [User Roles and Permissions](#user-roles-and-permissions)
6. [Performance and Scalability](#performance-and-scalability)
7. [Monitoring and Operations](#monitoring-and-operations)
8. [Integration Points](#integration-points)

## Architecture Overview

### High-Level Design

The Checking Engine uses RabbitMQ as the central message broker to orchestrate Purple Team operations, enabling asynchronous communication between Red Team activities (Caldera) and Blue Team detection systems.

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Caldera   │───▶│   RabbitMQ      │───▶│ Checking Engine │
│ (Red Team)  │    │ Message Broker  │    │  (Blue Team)    │
└─────────────┘    └─────────────────┘    └─────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Detection       │
                   │ Workers         │
                   └─────────────────┘
```

### Design Principles

1. **Loose Coupling**: Components communicate only through messages
2. **Asynchronous Processing**: Non-blocking operations for scalability
3. **Fault Tolerance**: Message persistence and acknowledgment mechanisms
4. **Security Isolation**: Role-based access control with least privilege
5. **Horizontal Scalability**: Support for multiple worker instances
6. **Audit Trail**: Complete message logging and traceability

## Message Flow Design

### Core Message Flow

```
┌─────────────┐   publish   ┌─────────────────────┐   route   ┌──────────────────────┐
│   Caldera   │────────────▶│ caldera.checking.   │──────────▶│ caldera.checking.    │
│ Publisher   │             │ exchange            │           │ instructions         │
└─────────────┘             └─────────────────────┘           └──────────────────────┘
                                     │                                   │
                                     │                                   │ consume
                                     │                                   ▼
                            ┌─────────────────────┐           ┌──────────────────────┐
                            │ Detection Workers   │           │ Checking Engine      │
                            │ (publish results)   │           │ Backend              │
                            └─────────────────────┘           └──────────────────────┘
                                     │
                                     ▼
                   ┌─────────────────────────────────────────────┐
                   │              Response Queues                │
                   │ ┌─────────────────┐ ┌───────────────────────┐│
                   │ │ api.responses   │ │ agent.responses       ││
                   │ └─────────────────┘ └───────────────────────┘│
                   └─────────────────────────────────────────────┘
```

### Message Types and Payloads

#### 1. Execution Result Messages (Caldera → Checking Engine)

**Queue**: `caldera.checking.instructions`  
**Routing Key**: `caldera.execution.result`

```json
{
  "operation_id": "op-12345",
  "agent_host": "target-machine.local",
  "agent_paw": "abc123def456",
  "command": "whoami",
  "result": {
    "stdout": "administrator",
    "stderr": "",
    "exit_code": 0
  },
  "timestamp": "2024-01-15T10:30:00Z",
  "detections": {
    "api": {
      "siem": {
        "query": "search index=security user=administrator",
        "platform": "splunk"
      },
      "edr": {
        "query": "process_name:whoami.exe",
        "platform": "crowdstrike"
      }
    },
    "agent": {
      "windows": {
        "command": "Get-EventLog Security -InstanceId 4624",
        "platform": "powershell"
      },
      "linux": {
        "command": "grep 'sudo' /var/log/auth.log",
        "platform": "bash"
      }
    }
  }
}
```

#### 2. Detection Response Messages (Workers → Checking Engine)

**Queues**: `caldera.checking.api.responses`, `caldera.checking.agent.responses`  
**Routing Keys**: `checking.api.response`, `checking.agent.response`

```json
{
  "detection_id": "det-67890",
  "execution_id": "exec-12345",
  "detection_type": "api|agent",
  "platform": "siem|edr|windows|linux",
  "detected": true,
  "confidence": 0.85,
  "results": {
    "events_found": 3,
    "rule_matched": "suspicious_admin_logon",
    "raw_output": "...",
    "execution_time_ms": 1500
  },
  "timestamp": "2024-01-15T10:31:15Z",
  "metadata": {
    "worker_id": "api-worker-01",
    "query_hash": "sha256:...",
    "version": "1.0.0"
  }
}
```

## Security Model

### Virtual Host Isolation

- **Virtual Host**: `/caldera_checking`
- **Purpose**: Complete isolation from default RabbitMQ setup
- **Benefits**: Security boundary, resource isolation, easier management

### Authentication and Authorization

#### Password Security
- **Generation**: Cryptographically secure random passwords (32 characters)
- **Storage**: `rabbitmq_passwords.txt` with restricted permissions (600)
- **Rotation**: Manual rotation recommended every 90 days

#### TLS/SSL (Production Consideration)
```
# Future enhancement for production
ssl_options.cacertfile = /etc/rabbitmq/ca_certificate.pem
ssl_options.certfile = /etc/rabbitmq/server_certificate.pem
ssl_options.keyfile = /etc/rabbitmq/server_key.pem
```

## Exchange and Queue Structure

### Exchange Design

#### Main Topic Exchange: `caldera.checking.exchange`

- **Type**: `topic`
- **Durability**: `true` (survives broker restart)
- **Auto-delete**: `false`
- **Arguments**: None

**Why Topic Exchange?**
- Flexible routing based on routing keys
- Supports future message types without reconfiguration
- Pattern-based routing: `caldera.*`, `checking.*`
- Extensible for new detection platforms

### Queue Design

#### 1. Instructions Queue: `caldera.checking.instructions`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false
  # Queue arguments applied via policy, not at creation

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: caldera.execution.result  # Specific routing key from scripts
```

**Purpose**: Receives execution results from Caldera for processing

#### 2. API Responses Queue: `caldera.checking.api.responses`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false
  # Queue arguments applied via policy, not at creation

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: checking.api.response  # Specific routing key from scripts
```

**Purpose**: Collects detection results from API-based workers (SIEM, EDR APIs)

#### 3. Agent Responses Queue: `caldera.checking.agent.responses`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false  
  # Queue arguments applied via policy, not at creation

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: checking.agent.response  # Specific routing key from scripts
```

**Purpose**: Collects detection results from agent-based workers (host commands)

### Routing Key Strategy

| Routing Key | Source | Destination | Purpose |
|-------------|---------|-------------|---------|
| `caldera.execution.result` | Caldera Publisher | instructions queue | Red Team execution results |
| `checking.api.response` | API Workers | api.responses queue | SIEM/EDR detection results |
| `checking.agent.response` | Agent Workers | agent.responses queue | Host-based detection results |

## User Roles and Permissions

### Role-Based Access Control Matrix

| User | Virtual Host | Configure | Write | Read | Description |
|------|-------------|-----------|-------|------|-------------|
| `caldera_admin` | `/caldera_checking` | `.*` | `.*` | `.*` | Full administrative access |
| `caldera_publisher` | `/caldera_checking` | `` | `^caldera\.checking\.exchange$` | `` | Red Team publisher only |
| `checking_consumer` | `/caldera_checking` | `` | `` | `^caldera\.checking\.instructions$` | Blue Team backend consumer |
| `checking_worker` | `/caldera_checking` | `` | `^caldera\.checking\.(exchange\|(api\|agent)\.responses)$` | `` | Detection workers publisher |
| `monitor_user` | `/caldera_checking` | `` | `` | `.*` | Read-only monitoring access |

### Permission Analysis

#### 1. Caldera Publisher (Red Team)
```bash
# Can only publish to main exchange
Write: ^caldera\.checking\.exchange$
# Cannot read any queues (fire-and-forget)
Read: (none)
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Red Team should only send execution results, not access Blue Team data.

#### 2. Checking Consumer (Blue Team Backend)
```bash
# Cannot publish anywhere
Write: (none)
# Can only read from instructions queue
Read: ^caldera\.checking\.instructions$
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Backend only processes incoming instructions, doesn't publish results directly.

#### 3. Checking Worker (Detection Workers)
```bash
# Can publish to exchange and response queues
Write: ^caldera\.checking\.(exchange|(api|agent)\.responses)$
# Cannot read any queues
Read: (none)
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Workers receive tasks through backend, only publish results.

### Connection Limits

```yaml
caldera_publisher:
  max-connections: 100
  # max-channels: Not configured in current setup

checking_consumer:
  max-connections: 100
  # max-channels: Not configured in current setup

checking_worker:
  max-connections: 100
  # max-channels: Not configured in current setup
```

### Checking Current Limits and Usage

To verify actual connection limits and current usage:

```bash
# Check user connection limits
sudo rabbitmqctl list_user_limits --user caldera_publisher
sudo rabbitmqctl list_user_limits --user checking_consumer
sudo rabbitmqctl list_user_limits --user checking_worker

# Check current active connections
sudo rabbitmqctl list_connections user state

# Count connections per user
sudo rabbitmqctl list_connections user | grep -c caldera_publisher

# Check current channels
sudo rabbitmqctl list_channels user connection state

# Count channels per user  
sudo rabbitmqctl list_channels user | grep -c caldera_publisher
```

## Performance and Scalability

### Queue Policies

#### Current Queue Policy (from `04_configure_limits_security.sh`)
```yaml
Policy: caldera-checking-limits
Pattern: ^caldera\.checking\..*
Definition:
  max-length: 10000           # Actual value from scripts
  message-ttl: 3600000        # 1 hour (actual value)
  ha-mode: all                # High availability for all nodes
```

**Note**: The setup scripts configure basic policies. Production may need additional tuning for `max-length-bytes` and `overflow` behavior.

### Scaling Considerations

#### Horizontal Scaling
- **Multiple Workers**: Each worker type can run multiple instances
- **Queue Partitioning**: Consider sharding by operation_id for very high throughput
- **Federation**: Multi-datacenter deployment support

#### Vertical Scaling
- **Memory**: Monitor queue depths and message sizes
- **Disk**: Enable lazy queues for large message backlogs
- **CPU**: Monitor exchange routing performance

### Performance Tuning

#### Memory Management
```erlang
# /etc/rabbitmq/rabbitmq.conf
vm_memory_high_watermark.relative = 0.6
disk_free_limit.absolute = 2GB
```

#### Lazy Queues (Large Backlogs)
```bash
sudo rabbitmqctl set_policy lazy-queues "^caldera\.checking\." \
  '{"queue-mode":"lazy"}' \
  --apply-to queues
```

## Monitoring and Operations

### Key Metrics

#### Queue Metrics
- **Message Rates**: publish/deliver/ack rates per queue
- **Queue Depths**: Current message counts
- **Consumer Utilization**: Active consumers per queue
- **Message TTL Expiry**: Expired message counts

#### System Metrics
- **Memory Usage**: RabbitMQ memory consumption
- **Disk Usage**: Message store and index sizes
- **Network I/O**: Message throughput
- **Connection Counts**: Per-user connection usage

### Alerting Thresholds

```yaml
Critical:
  - Queue depth > 5000 messages
  - Memory usage > 80%
  - Disk free < 1GB
  - No consumers for > 5 minutes

Warning:
  - Queue depth > 1000 messages
  - Memory usage > 60%
  - Message TTL expiry rate > 10/min
  - Connection failure rate > 1%
```

### Operational Tools

#### Management UI
- **URL**: `http://localhost:15672`
- **Users**: Any user can login with monitoring capabilities
- **Features**: Queue stats, message tracing, topology visualization

#### CLI Monitoring
```bash
# Queue status
sudo rabbitmqctl list_queues -p /caldera_checking name messages

# User connections  
sudo rabbitmqctl list_connections user peer_host

# Memory usage
sudo rabbitmqctl status | grep memory
```

## Integration Points

### Caldera Integration

#### Publisher Hook Location
**File**: `app/service/contact_svc.py`  
**Method**: `_save_result()` → `_publish_to_queue()`

```python
async def _publish_to_queue(self, fwd_messages):
    """Publish execution results to RabbitMQ"""
    connection = await aio_pika.connect_robust(
        f"amqp://caldera_publisher:{password}@localhost:5672/caldera_checking"
    )
    
    async with connection:
        channel = await connection.channel()
        exchange = await channel.get_exchange('caldera.checking.exchange')
        
        message = aio_pika.Message(
            json.dumps(fwd_messages).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
        
        await exchange.publish(
            message,
            routing_key='caldera.execution.result'
        )
```

### Checking Engine Backend Integration

#### Consumer Implementation
```python
import aio_pika
import asyncio
import json

class CheckingEngineConsumer:
    async def start_consuming(self):
        connection = await aio_pika.connect_robust(
            f"amqp://checking_consumer:{password}@localhost:5672/caldera_checking"
        )
        
        channel = await connection.channel()
        queue = await channel.get_queue('caldera.checking.instructions')
        
        await queue.consume(self.process_execution_result)
    
    async def process_execution_result(self, message):
        async with message.process():
            data = json.loads(message.body.decode())
            
            # 1. Store execution in PostgreSQL
            await self.store_execution(data)
            
            # 2. Create detection tasks
            detection_tasks = await self.create_detection_tasks(data)
            
            # 3. Send to appropriate workers
            await self.dispatch_detection_tasks(detection_tasks)
```

### Detection Workers Integration

#### API Worker Pattern
```python
class APIDetectionWorker:
    async def publish_result(self, detection_result):
        connection = await aio_pika.connect_robust(
            f"amqp://checking_worker:{password}@localhost:5672/caldera_checking"
        )
        
        async with connection:
            channel = await connection.channel()
            exchange = await channel.get_exchange('caldera.checking.exchange')
            
            message = aio_pika.Message(
                json.dumps(detection_result).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            await exchange.publish(
                message,
                routing_key='checking.api.response'
            )
```

## Future Enhancements

### Phase 2 Considerations

1. **Dead Letter Queues**: Handle failed message processing
2. **Message Compression**: Reduce bandwidth for large payloads  
3. **Schema Validation**: JSON Schema validation for messages
4. **Encryption**: End-to-end message encryption
5. **Federation**: Multi-site deployment support
6. **Streaming**: RabbitMQ Streams for high-throughput scenarios

### Operational Improvements

1. **Automated Monitoring**: Prometheus + Grafana integration
2. **Log Aggregation**: Centralized logging with ELK stack
3. **Backup/Recovery**: Automated message store backups
4. **Performance Testing**: Load testing framework
5. **Blue/Green Deployment**: Zero-downtime updates

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15 