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
│ (Red Team)  │    │ Message Broker  │    │  Backend        │
└─────────────┘    └─────────────────┘    └─────────────────┘
                            │                       │
                            │                       ▼
                            │              ┌─────────────────┐
                            │              │   Dispatcher    │
                            │              └─────────────────┘
                            │                       │
                            ▼                       ▼
                   ┌─────────────────┐    ┌─────────────────┐
                   │ Detection       │───▶│ Result          │
                   │ Workers         │    │ Consumer        │
                   └─────────────────┘    └─────────────────┘
```

### Design Principles

1. **Loose Coupling**: Components communicate only through messages
2. **Asynchronous Processing**: Non-blocking operations for scalability
3. **Fault Tolerance**: Message persistence and acknowledgment mechanisms
4. **Security Isolation**: Role-based access control with least privilege
5. **Horizontal Scalability**: Support for multiple worker instances
6. **Audit Trail**: Complete message logging and traceability

## Message Flow Design

### Complete Message Flow

```
┌─────────────┐   publish   ┌─────────────────────┐   route   ┌──────────────────────┐
│   Caldera   │────────────▶│ caldera.checking.   │──────────▶│ caldera.checking.    │
│ Publisher   │             │ exchange            │           │ instructions         │
└─────────────┘             └─────────────────────┘           └──────────────────────┘
                                     │                                   │
                                     │                                   │ consume
                                     │                                   ▼
                                     │                        ┌──────────────────────┐
                                     │                        │ Checking Engine      │
                                     │                        │ Backend Consumer     │
                                     │                        └──────────────────────┘
                                     │                                   │
                                     │                                   │ process &
                                     │                                   │ dispatch
                                     │                                   ▼
                                     │                        ┌──────────────────────┐
                                     │                        │ Checking Engine      │
                                     │              ┌─────────│ Dispatcher           │
                                     │              │         └──────────────────────┘
                                     │              │
                                     │              ▼
                   ┌─────────────────────────────────────────────┐
                   │              Task Queues                    │
                   │ ┌─────────────────┐ ┌───────────────────────┐│
                   │ │ api.tasks       │ │ agent.tasks           ││
                   │ └─────────────────┘ └───────────────────────┘│
                   └─────────────────────────────────────────────┘
                                     │
                                     │ consume
                                     ▼
                            ┌─────────────────────┐
                            │ Detection Workers   │
                            │ (consume & execute) │
                            └─────────────────────┘
                                     │
                                     │ publish
                                     ▼
                   ┌─────────────────────────────────────────────┐
                   │              Response Queues                │
                   │ ┌─────────────────┐ ┌───────────────────────┐│
                   │ │ api.responses   │ │ agent.responses       ││
                   │ └─────────────────┘ └───────────────────────┘│
                   └─────────────────────────────────────────────┘
                                     │
                                     │ consume
                                     ▼
                            ┌─────────────────────┐
                            │ Result Consumer     │
                            │ (process results)   │
                            └─────────────────────┘
```

### Message Types and Payloads

#### 1. Execution Result Messages (Caldera → Backend Consumer)

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

#### 2. Detection Task Messages (Dispatcher → Workers)

**Queues**: `caldera.checking.api.tasks`, `caldera.checking.agent.tasks`  
**Routing Keys**: `checking.api.task`, `checking.agent.task`

```json
{
  "task_id": "task-uuid-12345",
  "operation_id": "op-12345",
  "detection_type": "api|agent",
  "platform": "siem|edr|windows|linux",
  "query": {
    "type": "splunk_search|powershell_command|bash_command",
    "content": "search index=security user=administrator",
    "timeout_seconds": 30
  },
  "metadata": {
    "priority": "high|medium|low",
    "created_at": "2024-01-15T10:30:30Z",
    "execution_context": {
      "original_command": "whoami",
      "target_host": "target-machine.local"
    }
  }
}
```

#### 3. Detection Response Messages (Workers → Result Consumer)

**Queues**: `caldera.checking.api.responses`, `caldera.checking.agent.responses`  
**Routing Keys**: `checking.api.response`, `checking.agent.response`

```json
{
  "detection_id": "det-67890",
  "task_id": "task-uuid-12345",
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

## Exchange and Queue Structure

### Exchange: `caldera.checking.exchange`

```yaml
Type: topic
Durable: true
Auto-delete: false
Internal: false
Arguments: {}
```

**Purpose**: Central routing hub for all Checking Engine messages using topic-based routing.

### Queue Structure (5 Queues Total)

#### 1. Instructions Queue: `caldera.checking.instructions`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false
  # Queue arguments applied via policy

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: caldera.execution.result
```

**Purpose**: Receives Red Team execution results from Caldera for processing by the backend consumer.

#### 2. API Tasks Queue: `caldera.checking.api.tasks`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: checking.api.task
```

**Purpose**: Dispatches detection tasks to API-based workers (SIEM, EDR).

#### 3. Agent Tasks Queue: `caldera.checking.agent.tasks`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: checking.agent.task
```

**Purpose**: Dispatches detection tasks to agent-based workers (PowerShell, Bash).

#### 4. API Responses Queue: `caldera.checking.api.responses`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: checking.api.response
```

**Purpose**: Collects detection results from API-based workers.

#### 5. Agent Responses Queue: `caldera.checking.agent.responses`

```yaml
Properties:
  - Durable: true
  - Auto-delete: false

Binding:
  - Exchange: caldera.checking.exchange
  - Routing Key: checking.agent.response
```

**Purpose**: Collects detection results from agent-based workers.

### Routing Key Strategy

| Routing Key | Source | Destination | Purpose |
|-------------|---------|-------------|---------|
| `caldera.execution.result` | Caldera Publisher | instructions queue | Red Team execution results |
| `checking.api.task` | Backend Dispatcher | api.tasks queue | Tasks for API workers |
| `checking.agent.task` | Backend Dispatcher | agent.tasks queue | Tasks for agent workers |
| `checking.api.response` | API Workers | api.responses queue | API detection results |
| `checking.agent.response` | Agent Workers | agent.responses queue | Agent detection results |

## User Roles and Permissions

### Role-Based Access Control Matrix (7 Users)

| User | Virtual Host | Configure | Write | Read | Description |
|------|-------------|-----------|-------|------|-------------|
| `caldera_admin` | `/caldera_checking` | `.*` | `.*` | `.*` | Full administrative access |
| `caldera_publisher` | `/caldera_checking` | `^$` | `^caldera\.checking\.exchange$` | `^$` | Red Team publisher only |
| `checking_consumer` | `/caldera_checking` | `^$` | `^$` | `^caldera\.checking\.instructions$` | Backend consumer |
| `checking_dispatcher` | `/caldera_checking` | `^$` | `^caldera\.checking\.exchange$` | `^$` | Task dispatcher |
| `checking_worker` | `/caldera_checking` | `^$` | `^caldera\.checking\.(exchange\|(api\|agent)\.responses)$` | `^caldera\.checking\.(api\.tasks\|agent\.tasks)$` | Detection workers |
| `checking_result_consumer` | `/caldera_checking` | `^$` | `^$` | `^caldera\.checking\.(api\|agent)\.responses$` | Result processor |
| `monitor_user` | `/caldera_checking` | `^$` | `^$` | `^caldera\.checking\..*$` | Read-only monitoring |

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

#### 2. Checking Consumer (Backend Consumer)
```bash
# Cannot publish anywhere
Write: (none)
# Can only read from instructions queue
Read: ^caldera\.checking\.instructions$
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Backend consumer only processes incoming instructions, doesn't publish directly.

#### 3. Checking Dispatcher (Backend Dispatcher)
```bash
# Can only publish to main exchange
Write: ^caldera\.checking\.exchange$
# Cannot read any queues
Read: (none)
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Dispatcher only sends tasks to workers, doesn't consume responses directly.

#### 4. Checking Worker (Detection Workers)
```bash
# Can publish to exchange and response queues
Write: ^caldera\.checking\.(exchange|(api|agent)\.responses)$
# Can read from task queues only
Read: ^caldera\.checking\.(api\.tasks|agent\.tasks)$
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Workers consume tasks and publish results, following the detection workflow.

#### 5. Checking Result Consumer (Result Processor)
```bash
# Cannot publish anywhere
Write: (none)
# Can only read from response queues
Read: ^caldera\.checking\.(api|agent)\.responses$
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Result consumer only processes detection results, doesn't publish new messages.

#### 6. Monitor User (Monitoring)
```bash
# Cannot publish anywhere
Write: (none)
# Can read all checking queues
Read: ^caldera\.checking\..*$
# Cannot configure topology
Configure: (none)
```

**Security Rationale**: Monitoring user has read-only access for observability.

### Connection Limits

```yaml
caldera_publisher:
  max-connections: 100

checking_consumer:
  max-connections: 100

checking_dispatcher:
  max-connections: 100

checking_worker:
  max-connections: 100

checking_result_consumer:
  max-connections: 100

# monitor_user and caldera_admin: No explicit limits (admin users)
```

### Checking Current Limits and Usage

To verify actual connection limits and current usage:

```bash
# Check user connection limits (all 7 users)
sudo rabbitmqctl list_user_limits --user caldera_publisher
sudo rabbitmqctl list_user_limits --user checking_consumer
sudo rabbitmqctl list_user_limits --user checking_dispatcher
sudo rabbitmqctl list_user_limits --user checking_worker
sudo rabbitmqctl list_user_limits --user checking_result_consumer

# Check current active connections
sudo rabbitmqctl list_connections user state

# Count connections per user
sudo rabbitmqctl list_connections user | grep -c caldera_publisher
sudo rabbitmqctl list_connections user | grep -c checking_consumer
sudo rabbitmqctl list_connections user | grep -c checking_dispatcher
sudo rabbitmqctl list_connections user | grep -c checking_worker
sudo rabbitmqctl list_connections user | grep -c checking_result_consumer

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
  max-length: 10000           # Maximum messages per queue
  message-ttl: 3600000        # 1 hour TTL
  ha-mode: all                # High availability for all nodes
```

**Applied to all 5 queues**: instructions, api.tasks, agent.tasks, api.responses, agent.responses

### Scaling Considerations

#### Horizontal Scaling
- **Multiple Workers**: Each worker type can run multiple instances
- **Multiple Dispatchers**: Dispatcher can be scaled horizontally
- **Multiple Result Consumers**: Result processing can be parallelized
- **Queue Partitioning**: Consider sharding by operation_id for very high throughput
- **Federation**: Multi-datacenter deployment support

#### Vertical Scaling
- **Memory**: Monitor queue depths and message sizes across 5 queues
- **Disk**: Enable lazy queues for large message backlogs
- **CPU**: Monitor exchange routing performance with 5 routing keys

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

#### Queue Metrics (5 Queues)
- **Message Rates**: publish/deliver/ack rates per queue
- **Queue Depths**: Current message counts for all 5 queues
- **Consumer Utilization**: Active consumers per queue
- **Message TTL Expiry**: Expired message counts
- **Task Processing Time**: Time from task dispatch to result

#### System Metrics
- **Memory Usage**: RabbitMQ memory consumption
- **Disk Usage**: Message store and index sizes
- **Network I/O**: Message throughput across all workflows
- **Connection Counts**: Per-user connection usage (7 users)

### Alerting Thresholds

```yaml
Critical:
  - Queue depth > 5000 messages (any of 5 queues)
  - Memory usage > 80%
  - Disk free < 1GB
  - No consumers for > 5 minutes (tasks or responses)
  - Task processing timeout > 5 minutes

Warning:
  - Queue depth > 1000 messages
  - Memory usage > 60%
  - Message TTL expiry rate > 10/min
  - Connection failure rate > 1%
  - Unbalanced task distribution between workers
```

### Operational Tools

#### Management UI
- **URL**: `http://localhost:15672`
- **Users**: Any user with management tag can login
- **Features**: Queue stats, message tracing, topology visualization

#### CLI Monitoring
```bash
# Queue status (all 5 queues)
sudo rabbitmqctl list_queues -p /caldera_checking name messages

# User connections (7 users)
sudo rabbitmqctl list_connections user peer_host

# Memory usage
sudo rabbitmqctl status | grep memory

# Check specific queue depths
sudo rabbitmqctl list_queues -p /caldera_checking name messages | grep -E "(instructions|tasks|responses)"
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
        host="localhost",
        port=5672,
        login="caldera_publisher",
        password=password,
        virtualhost="/caldera_checking"
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
            host="localhost",
            port=5672,
            login="checking_consumer",
            password=password,
            virtualhost="/caldera_checking"
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
            
            # 3. Send to appropriate workers via dispatcher
            await self.notify_dispatcher(detection_tasks)

class CheckingEngineDispatcher:
    async def dispatch_tasks(self, tasks):
        connection = await aio_pika.connect_robust(
            host="localhost",
            port=5672,
            login="checking_dispatcher",
            password=password,
            virtualhost="/caldera_checking"
        )
        
        async with connection:
            channel = await connection.channel()
            exchange = await channel.get_exchange('caldera.checking.exchange')
            
            for task in tasks:
                routing_key = f"checking.{task['detection_type']}.task"
                message = aio_pika.Message(
                    json.dumps(task).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                )
                
                await exchange.publish(message, routing_key=routing_key)

class CheckingEngineResultConsumer:
    async def start_consuming(self):
        connection = await aio_pika.connect_robust(
            host="localhost",
            port=5672,
            login="checking_result_consumer",
            password=password,
            virtualhost="/caldera_checking"
        )
        
        channel = await connection.channel()
        api_queue = await channel.get_queue('caldera.checking.api.responses')
        agent_queue = await channel.get_queue('caldera.checking.agent.responses')
        
        await api_queue.consume(self.process_detection_result)
        await agent_queue.consume(self.process_detection_result)
    
    async def process_detection_result(self, message):
        async with message.process():
            result = json.loads(message.body.decode())
            
            # Store result in PostgreSQL
            await self.store_detection_result(result)
            
            # Update execution status
            await self.update_execution_status(result)
```

### Detection Workers Integration

#### API Worker Pattern
```python
class APIDetectionWorker:
    async def start_working(self):
        connection = await aio_pika.connect_robust(
            host="localhost",
            port=5672,
            login="checking_worker",
            password=password,
            virtualhost="/caldera_checking"
        )
        
        channel = await connection.channel()
        task_queue = await channel.get_queue('caldera.checking.api.tasks')
        
        await task_queue.consume(self.process_detection_task)
    
    async def process_detection_task(self, message):
        async with message.process():
            task = json.loads(message.body.decode())
            
            # Execute detection query
            result = await self.execute_detection(task)
            
            # Publish result
            await self.publish_result(result)
    
    async def publish_result(self, detection_result):
        connection = await aio_pika.connect_robust(
            host="localhost",
            port=5672,
            login="checking_worker",
            password=password,
            virtualhost="/caldera_checking"
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

1. **Dead Letter Queues**: Handle failed message processing for all 5 queues
2. **Message Compression**: Reduce bandwidth for large payloads  
3. **Schema Validation**: JSON Schema validation for all message types
4. **Encryption**: End-to-end message encryption
5. **Federation**: Multi-site deployment support
6. **Streaming**: RabbitMQ Streams for high-throughput scenarios
7. **Priority Queues**: Priority-based task processing

### Operational Improvements

1. **Automated Monitoring**: Prometheus + Grafana integration for all 5 queues
2. **Log Aggregation**: Centralized logging with ELK stack for all 7 users
3. **Backup/Recovery**: Automated message store backups
4. **Performance Testing**: Load testing framework for complete workflow
5. **Blue/Green Deployment**: Zero-downtime updates
6. **Circuit Breakers**: Fault tolerance for worker failures
7. **Auto-scaling**: Dynamic worker scaling based on queue depth

---

**Document Version**: 2.0  
**Last Updated**: 2024-01-15  
**Next Review**: 2024-04-15 