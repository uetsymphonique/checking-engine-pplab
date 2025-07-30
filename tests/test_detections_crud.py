#!/usr/bin/env python3
"""
Test script for Detection Executions and Results CRUD endpoints
Tests all CRUD operations for the detection_executions and detection_results tables
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4
import httpx



class DetectionsCRUDTest:
    """Test class for Detection Executions and Results CRUD operations"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:1337/api/v1"
        self.test_operation_id = uuid4()
        self.test_execution_result_id = uuid4()
        self.test_detection_execution_id = None
        self.test_detection_result_id = None
        
        # Test data for detection execution
        self.test_detection_execution_data = {
            "execution_result_id": str(self.test_execution_result_id),
            "operation_id": str(self.test_operation_id),
            "detection_type": "api",
            "detection_platform": "cym",
            "detection_config": {
                "endpoint": "https://api.example.com/detect",
                "timeout": 30,
                "headers": {"Authorization": "Bearer test-token"}
            },
            "status": "pending",
            "retry_count": 0,
            "max_retries": 3,
            "execution_metadata": {
                "test": True,
                "description": "Test detection execution"
            }
        }
        
        # Test data for detection result
        self.test_detection_result_data = {
            "detection_execution_id": None,  # Will be set after creating detection execution
            "detected": True,
            "raw_response": {
                "status_code": 200,
                "response": "Activity detected",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            "parsed_results": {
                "detected": True,
                "confidence": 0.85,
                "severity": "medium",
                "rules_matched": ["rule_001", "rule_002"]
            },
            "result_source": "api.example.com",
            "result_metadata": {
                "confidence": 0.85,
                "severity": "medium",
                "test": True
            }
        }
    
    async def test_create_operation_first(self):
        """Create a test operation first (required for foreign key)"""
        print("Creating test operation for foreign key...")
        
        operation_data = {
            "name": "Test Operation for Detections",
            "operation_id": str(self.test_operation_id),
            "operation_start": datetime.now(timezone.utc).isoformat(),
            "operation_metadata": {
                "test": True,
                "description": "Test operation for detection testing"
            }
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.post("/operations/", json=operation_data)
            
            if response.status_code == 201:
                result = response.json()
                print(f"Created test operation: {result['id']}")
            else:
                print(f"Error creating operation: {response.text}")
                return False
        
        return True
    
    async def test_create_execution_result_first(self):
        """Create a test execution result first (required for foreign key)"""
        print("Creating test execution result for foreign key...")
        
        execution_data = {
            "operation_id": str(self.test_operation_id),
            "agent_host": "test-host.local",
            "agent_paw": "test-paw-456",
            "link_id": str(uuid4()),
            "command": "netstat -an",
            "pid": 12346,
            "status": 0,
            "result_data": {
                "stdout": "Active connections",
                "stderr": "",
                "exit_code": 0
            },
            "agent_reported_time": datetime.now(timezone.utc).isoformat(),
            "link_state": "SUCCESS",
            "raw_message": {
                "test": True,
                "description": "Test execution for detection testing"
            }
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.post("/executions/", json=execution_data)
            
            if response.status_code == 201:
                result = response.json()
                self.test_execution_result_id = result["id"]
                print(f"Created test execution result: {self.test_execution_result_id}")
            else:
                print(f"Error creating execution result: {response.text}")
                return False
        
        return True
    
    async def test_create_detection_execution(self):
        """Test creating a new detection execution"""
        print("\nTesting CREATE detection execution...")
        
        # Update execution_result_id with actual ID
        self.test_detection_execution_data["execution_result_id"] = str(self.test_execution_result_id)
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.post("/detections/executions/", json=self.test_detection_execution_data)
            
            print(f"CREATE detection execution response: {response.status_code}")
            if response.status_code == 201:
                result = response.json()
                self.test_detection_execution_id = result["id"]
                print(f"Created detection execution ID: {self.test_detection_execution_id}")
                print(f"Detection type: {result['detection_type']}")
                print(f"Platform: {result['detection_platform']}")
                print(f"Status: {result['status']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_detection_execution_by_id(self):
        """Test getting detection execution by ID"""
        if not self.test_detection_execution_id:
            print("Skipping GET detection execution test - no detection execution created")
            return
            
        print("\nTesting GET detection execution by ID...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/detections/executions/{self.test_detection_execution_id}")
            
            print(f"GET detection execution by ID response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Retrieved detection execution: {result['detection_type']}")
                print(f"Platform: {result['detection_platform']}")
                print(f"Created at: {result['created_at']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_detection_executions_by_execution_result(self):
        """Test getting detection executions by execution result"""
        print("\nTesting GET detection executions by execution result...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/detections/executions/by-execution-result/{self.test_execution_result_id}")
            
            print(f"GET by execution result response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total detection executions for execution result: {result['total']}")
                print(f"Returned detection executions: {len(result['detection_executions'])}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_detection_executions_by_operation(self):
        """Test getting detection executions by operation"""
        print("\nTesting GET detection executions by operation...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/detections/executions/by-operation/{self.test_operation_id}")
            
            print(f"GET by operation response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total detection executions for operation: {result['total']}")
                print(f"Returned detection executions: {len(result['detection_executions'])}")
            else:
                print(f"Error: {response.text}")
    
    async def test_list_detection_executions(self):
        """Test listing detection executions with filters"""
        print("\nTesting LIST detection executions...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            # Test basic list
            response = await client.get("/detections/executions/")
            print(f"LIST response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total detection executions: {result['total']}")
                print(f"Returned detection executions: {len(result['detection_executions'])}")
            
            # Test filter by detection type
            response = await client.get("/detections/executions/?detection_type=api")
            print(f"LIST by detection type response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Filtered by detection type: {len(result['detection_executions'])} results")
            
            # Test filter by platform
            response = await client.get("/detections/executions/?detection_platform=cym")
            print(f"LIST by platform response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Filtered by platform: {len(result['detection_executions'])} results")
    
    async def test_update_detection_execution(self):
        """Test updating a detection execution"""
        if not self.test_detection_execution_id:
            print("Skipping UPDATE detection execution test - no detection execution created")
            return
            
        print("\nTesting UPDATE detection execution...")
        
        update_data = {
            "status": "running",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "execution_metadata": {
                "test": True,
                "description": "Updated detection execution",
                "started_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.put(f"/detections/executions/{self.test_detection_execution_id}", json=update_data)
            
            print(f"UPDATE detection execution response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Updated status: {result['status']}")
                print(f"Updated started_at: {result['started_at']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_create_detection_result(self):
        """Test creating a new detection result"""
        print("\nTesting CREATE detection result...")
        
        # Update detection_execution_id with actual ID
        self.test_detection_result_data["detection_execution_id"] = str(self.test_detection_execution_id)
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.post("/detections/results/", json=self.test_detection_result_data)
            
            print(f"CREATE detection result response: {response.status_code}")
            if response.status_code == 201:
                result = response.json()
                self.test_detection_result_id = result["id"]
                print(f"Created detection result ID: {self.test_detection_result_id}")
                print(f"Detected: {result['detected']}")
                print(f"Source: {result['result_source']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_detection_result_by_id(self):
        """Test getting detection result by ID"""
        if not self.test_detection_result_id:
            print("Skipping GET detection result test - no detection result created")
            return
            
        print("\nTesting GET detection result by ID...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/detections/results/{self.test_detection_result_id}")
            
            print(f"GET detection result by ID response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Retrieved detection result: {result['detected']}")
                print(f"Source: {result['result_source']}")
                print(f"Created at: {result['created_at']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_detection_results_by_execution(self):
        """Test getting detection results by detection execution"""
        print("\nTesting GET detection results by execution...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/detections/results/by-execution/{self.test_detection_execution_id}")
            
            print(f"GET by execution response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total detection results for execution: {result['total']}")
                print(f"Returned detection results: {len(result['detection_results'])}")
            else:
                print(f"Error: {response.text}")
    
    async def test_list_detection_results(self):
        """Test listing detection results with filters"""
        print("\nTesting LIST detection results...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            # Test basic list
            response = await client.get("/detections/results/")
            print(f"LIST response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total detection results: {result['total']}")
                print(f"Returned detection results: {len(result['detection_results'])}")
            
            # Test filter by detected
            response = await client.get("/detections/results/?detected=true")
            print(f"LIST by detected response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Filtered by detected: {len(result['detection_results'])} results")
    
    async def test_get_detection_statistics(self):
        """Test getting detection statistics"""
        print("\nTesting GET detection statistics...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get("/detections/results/stats/summary")
            
            print(f"Statistics response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total detections: {result['total_detections']}")
                print(f"Detected count: {result['detected_count']}")
                print(f"Not detected count: {result['not_detected_count']}")
                print(f"Detection rate: {result['detection_rate']}%")
            else:
                print(f"Error: {response.text}")
    
    async def test_update_detection_result(self):
        """Test updating a detection result"""
        if not self.test_detection_result_id:
            print("Skipping UPDATE detection result test - no detection result created")
            return
            
        print("\nTesting UPDATE detection result...")
        
        update_data = {
            "detected": True,
            "parsed_results": {
                "detected": True,
                "confidence": 0.95,
                "severity": "high",
                "rules_matched": ["rule_001", "rule_002", "rule_003"]
            },
            "result_metadata": {
                "confidence": 0.95,
                "severity": "high",
                "updated": True
            }
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.put(f"/detections/results/{self.test_detection_result_id}", json=update_data)
            
            print(f"UPDATE detection result response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Updated detected: {result['detected']}")
                print(f"Updated confidence: {result['parsed_results']['confidence']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_delete_detection_result(self):
        """Test deleting a detection result"""
        if not self.test_detection_result_id:
            print("Skipping DELETE detection result test - no detection result created")
            return
            
        print("\nTesting DELETE detection result...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.delete(f"/detections/results/{self.test_detection_result_id}")
            
            print(f"DELETE detection result response: {response.status_code}")
            if response.status_code == 204:
                print("Detection result deleted successfully")
                
                # Verify deletion
                get_response = await client.get(f"/detections/results/{self.test_detection_result_id}")
                print(f"GET after DELETE: {get_response.status_code}")
                if get_response.status_code == 404:
                    print("Deletion verified - detection result not found")
            else:
                print(f"Error: {response.text}")
    
    async def test_delete_detection_execution(self):
        """Test deleting a detection execution"""
        if not self.test_detection_execution_id:
            print("Skipping DELETE detection execution test - no detection execution created")
            return
            
        print("\nTesting DELETE detection execution...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.delete(f"/detections/executions/{self.test_detection_execution_id}")
            
            print(f"DELETE detection execution response: {response.status_code}")
            if response.status_code == 204:
                print("Detection execution deleted successfully")
                
                # Verify deletion
                get_response = await client.get(f"/detections/executions/{self.test_detection_execution_id}")
                print(f"GET after DELETE: {get_response.status_code}")
                if get_response.status_code == 404:
                    print("Deletion verified - detection execution not found")
            else:
                print(f"Error: {response.text}")
    
    async def run_all_tests(self):
        """Run all CRUD tests"""
        print("Starting Detection Executions and Results CRUD Tests")
        print("=" * 60)
        
        # Create dependencies first
        if not await self.test_create_operation_first():
            print("Failed to create test operation. Exiting.")
            return
        
        if not await self.test_create_execution_result_first():
            print("Failed to create test execution result. Exiting.")
            return
        
        # Run detection execution tests
        await self.test_create_detection_execution()
        await self.test_get_detection_execution_by_id()
        await self.test_get_detection_executions_by_execution_result()
        await self.test_get_detection_executions_by_operation()
        await self.test_list_detection_executions()
        await self.test_update_detection_execution()
        
        # Run detection result tests
        await self.test_create_detection_result()
        await self.test_get_detection_result_by_id()
        await self.test_get_detection_results_by_execution()
        await self.test_list_detection_results()
        await self.test_get_detection_statistics()
        await self.test_update_detection_result()
        await self.test_delete_detection_result()
        await self.test_delete_detection_execution()
        
        print("\n" + "=" * 60)
        print("Detection Executions and Results CRUD Tests Completed")


async def main():
    """Main test runner"""
    test = DetectionsCRUDTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 