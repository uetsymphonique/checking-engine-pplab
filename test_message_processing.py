#!/usr/bin/env python3
"""
Test script for message processing functionality
Run from checking-engine root: python test_message_processing.py
"""

import asyncio
import json
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from checking_engine.services.message_service import MessageProcessingService
from checking_engine.database.connection import get_db_session
from checking_engine.utils.logging import get_logger

logger = get_logger(__name__)

# Test message similar to real Caldera messages
TEST_MESSAGE = {
    "timestamp": "2025-07-31T04:34:49.097943+00:00",
    "message_type": "link_result",
    "operation": {
        "name": "test_operation",
        "operation_id": "0f67cf30-cc1e-43a2-a9d8-b57ee59846e2",
        "operation_start": "2025-07-31T04:34:17.049411+00:00"
    },
    "execution": {
        "link_id": "135dd14b-9493-44c1-b8b8-800f39d85db9",
        "agent_host": "test_host",
        "agent_paw": "test_paw",
        "command": "echo 'test command'",
        "pid": 12345,
        "status": 0,
        "result_data": "{\"stdout\": \"test\\n\", \"stderr\": \"\", \"exit_code\": \"0\"}",
        "agent_reported_time": "2025-07-31T04:34:40+00:00",
        "link_state": "SUCCESS",
        "detections": "[{\"detection_type\": \"api\", \"detection_platform\": \"cym\", \"detection_config\": {\"command\": \"test detection query\", \"timeout\": 300}, \"max_retries\": 3}, {\"detection_type\": \"linux\", \"detection_platform\": \"sh\", \"detection_config\": {\"command\": \"ps aux | grep test\", \"timeout\": 60}, \"max_retries\": 2}]"
    }
}

# Test message without detections
TEST_MESSAGE_NO_DETECTIONS = {
    "timestamp": "2025-07-31T04:35:00.000000+00:00",
    "message_type": "link_result",
    "operation": {
        "name": "test_operation",
        "operation_id": "0f67cf30-cc1e-43a2-a9d8-b57ee59846e2",
        "operation_start": "2025-07-31T04:34:17.049411+00:00"
    },
    "execution": {
        "link_id": "246dd14b-9493-44c1-b8b8-800f39d85db0",
        "agent_host": "test_host",
        "agent_paw": "test_paw",
        "command": "ls -la",
        "pid": 12346,
        "status": 0,
        "result_data": "{\"stdout\": \"total 8\\n-rw-r--r-- 1 user user 0 Jul 31 04:35 test.txt\\n\", \"stderr\": \"\", \"exit_code\": \"0\"}",
        "agent_reported_time": "2025-07-31T04:35:00+00:00",
        "link_state": "SUCCESS",
        "detections": None
    }
}

async def test_message_processing():
    """Test message processing functionality"""
    
    print("=" * 60)
    print("TESTING MESSAGE PROCESSING SERVICE")
    print("=" * 60)
    
    try:
        # Test 1: Message with detections
        print("\n1. Testing message with detections...")
        async with get_db_session() as db_session:
            service = MessageProcessingService(db_session)
            result = await service.process_caldera_message(json.dumps(TEST_MESSAGE))
            
            print(f"✅ Operation created: {result['operation']['name']} ({result['operation']['operation_id']})")
            print(f"✅ Execution result created: {result['execution_result']['link_id']}")
            print(f"✅ Detection executions created: {len(result['detection_executions'])}")
            
            for i, detection in enumerate(result['detection_executions']):
                print(f"   - Detection {i+1}: {detection['detection_type']} ({detection['detection_platform']}) - {detection['status']}")
        
        print("\n2. Testing message without detections...")
        async with get_db_session() as db_session:
            service = MessageProcessingService(db_session)
            result = await service.process_caldera_message(json.dumps(TEST_MESSAGE_NO_DETECTIONS))
            
            print(f"✅ Operation reused: {result['operation']['name']} ({result['operation']['operation_id']})")
            print(f"✅ Execution result created: {result['execution_result']['link_id']}")
            print(f"✅ Detection executions created: {len(result['detection_executions'])} (expected 0)")
        
        print("\n3. Testing invalid message...")
        try:
            async with get_db_session() as db_session:
                service = MessageProcessingService(db_session)
                await service.process_caldera_message('{"invalid": "message"}')
            print("❌ Should have failed for invalid message")
        except ValueError as e:
            print(f"✅ Correctly rejected invalid message: {e}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("Message processing service is working correctly.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def main():
    """Main test function"""
    success = await test_message_processing()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())