#!/usr/bin/env python3
"""
Test script for Caldera RabbitMQ publisher integration
This script simulates the message format that Caldera would send to RabbitMQ
"""

import asyncio
import json
import aio_pika
from datetime import datetime, timezone

def get_password():
    with open('setup/mq_setup/.env', 'r') as f:
        for line in f:
            if 'RABBITMQ_PUBLISHER_PASS' in line:
                return line.split('=')[1].strip()
    return None

async def test_publish_message():
    """Test publishing a message that matches Caldera's format"""
    
    # RabbitMQ connection details (should match your setup)
    connection_config = {
        'host': 'localhost',
        'port': 5672,
        'vhost': '/caldera_checking',
        'username': 'caldera_publisher',
        'password': get_password(),  # You need to fill this from rabbitmq_passwords.txt
        'exchange': 'caldera.checking.exchange',
        'routing_key': 'caldera.execution.result'
    }
    
    # Read password from file if not set
    if not connection_config['password']:
        try:
            with open('setup/mq_setup/rabbitmq_passwords.txt', 'r') as f:
                for line in f:
                    if 'caldera_publisher' in line:
                        connection_config['password'] = line.split('=')[1].strip()
                        break
        except FileNotFoundError:
            print("ERROR: Please set the password manually or ensure rabbitmq_passwords.txt exists")
            return
    
    # Sample message that matches Caldera's format
    test_message = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'message_type': 'link_result',
        'operation': {
            'name': 'test-operation',
            'id': 'op-test-12345',
            'start': datetime.now(timezone.utc).isoformat(),
        },
        'execution': {
            'link_id': 'link-test-67890',
            'agent_host': 'test-machine.local',
            'agent_paw': 'test-paw-abc123',
            'command': 'whoami',
            'pid': 1234,
            'status': 0,
            'state': 'SUCCESS',
            'result_data': json.dumps({
                'stdout': 'administrator',
                'stderr': '',
                'exit_code': 0
            }),
            'agent_reported_time': datetime.now(timezone.utc).isoformat(),
            'detections': {
                'api': {
                    'siem': {
                        'query': 'search index=security user=administrator',
                        'platform': 'splunk'
                    }
                },
                'agent': {
                    'windows': {
                        'command': 'Get-EventLog Security -InstanceId 4624',
                        'platform': 'powershell'
                    }
                }
            }
        }
    }
    
    try:
        print(f"Connecting to RabbitMQ at {connection_config['host']}:{connection_config['port']}")
        print(f"Virtual Host: {connection_config['vhost']}")
        print(f"Username: {connection_config['username']}")
        
        # Connect to RabbitMQ using parameters (handles vhost encoding automatically)
        connection = await aio_pika.connect_robust(
            host=connection_config['host'],
            port=connection_config['port'],
            login=connection_config['username'],
            password=connection_config['password'],
            virtualhost=connection_config['vhost'],  # Include leading slash
            timeout=10.0,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        
        async with connection:
            print("✅ Connected to RabbitMQ successfully")
            
            # Create channel
            channel = await connection.channel()
            print("✅ Channel created")
            
            # Get exchange
            exchange = await channel.get_exchange(connection_config['exchange'])
            print(f"✅ Exchange '{connection_config['exchange']}' found")
            
            # Create message
            message_body = json.dumps(test_message, ensure_ascii=False, indent=2).encode('utf-8')
            message = aio_pika.Message(
                message_body,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                content_type='application/json',
                content_encoding='utf-8',
                timestamp=datetime.now(timezone.utc)
            )
            
            # Publish message
            await exchange.publish(
                message,
                routing_key=connection_config['routing_key']
            )
            
            print(f"✅ Message published successfully!")
            print(f"   Exchange: {connection_config['exchange']}")
            print(f"   Routing Key: {connection_config['routing_key']}")
            print(f"   Link ID: {test_message['execution']['link_id']}")
            print(f"   Message size: {len(message_body)} bytes")
            
    except aio_pika.exceptions.AMQPConnectionError as e:
        print(f"❌ Connection error: {e}")
        print("   Make sure RabbitMQ is running and credentials are correct")
    except aio_pika.exceptions.AMQPChannelError as e:
        print(f"❌ Channel error: {e}")
        print("   Make sure the exchange exists and user has permissions")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


async def verify_queue_count():
    """Check if message was queued successfully"""
    
    try:
        # Check with admin user to see queue stats
        print("\n" + "="*50)
        print("VERIFICATION STEPS:")
        print("="*50)
        print("1. Check queue message count:")
        print("   sudo rabbitmqctl list_queues -p /caldera_checking name messages")
        print("\n2. Peek at message (non-destructive):")
        print("   rabbitmqadmin -u monitor_user -p <password> -V /caldera_checking \\")
        print("     get queue=caldera.checking.instructions ackmode=reject_requeue_true")
        print("\n3. Check if consumer can read:")
        print("   rabbitmqadmin -u checking_consumer -p <password> -V /caldera_checking \\")
        print("     get queue=caldera.checking.instructions ackmode=ack_requeue_false")
        
    except Exception as e:
        print(f"Error in verification: {e}")


if __name__ == "__main__":
    print("🚀 Testing Caldera RabbitMQ Publisher Integration")
    print("="*60)
    
    try:
        # Run the test
        asyncio.run(test_publish_message())
        
        # Show verification steps
        asyncio.run(verify_queue_count())
        
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}") 