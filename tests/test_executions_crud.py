#!/usr/bin/env python3
"""
Test script for Execution Results CRUD endpoints
Tests all CRUD operations for the execution_results table
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4
import httpx



class ExecutionResultsCRUDTest:
    """Test class for Execution Results CRUD operations"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:1337/api/v1"
        self.test_operation_id = uuid4()
        self.test_link_id = uuid4()
        self.test_execution_data = {
            "operation_id": str(self.test_operation_id),
            "agent_host": "test-host.local",
            "agent_paw": "test-paw-123",
            "link_id": str(self.test_link_id),
            "command": "whoami",
            "pid": 12345,
            "status": 0,
            "result_data": {
                "stdout": "testuser",
                "stderr": "",
                "exit_code": 0
            },
            "agent_reported_time": datetime.now(timezone.utc).isoformat(),
            "link_state": "SUCCESS",
            "raw_message": {
                "test": True,
                "description": "Test execution result"
            }
        }
        self.created_execution_id = None
        self.created_operation_id = None
    
    async def test_create_operation_first(self):
        """Create a test operation first (required for foreign key)"""
        print("Creating test operation for foreign key...")
        
        operation_data = {
            "name": "Test Operation for Executions",
            "operation_id": str(self.test_operation_id),
            "operation_start": datetime.now(timezone.utc).isoformat(),
            "operation_metadata": {
                "test": True,
                "description": "Test operation for execution testing"
            }
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.post("/operations/", json=operation_data)
            
            if response.status_code == 201:
                result = response.json()
                self.created_operation_id = result["id"]
                print(f"Created test operation: {self.created_operation_id}")
            else:
                print(f"Error creating operation: {response.text}")
                return False
        
        return True
    
    async def test_create_execution_result(self):
        """Test creating a new execution result"""
        print("\nTesting CREATE execution result...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.post("/executions/", json=self.test_execution_data)
            
            print(f"CREATE response: {response.status_code}")
            if response.status_code == 201:
                result = response.json()
                self.created_execution_id = result["id"]
                print(f"Created execution ID: {self.created_execution_id}")
                print(f"Link ID: {result['link_id']}")
                print(f"Command: {result['command']}")
                print(f"Status: {result['status']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_execution_by_id(self):
        """Test getting execution result by ID"""
        if not self.created_execution_id:
            print("Skipping GET test - no execution created")
            return
            
        print("\nTesting GET execution by ID...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/executions/{self.created_execution_id}")
            
            print(f"GET by ID response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Retrieved execution: {result['command']}")
                print(f"Agent: {result['agent_host']}")
                print(f"Created at: {result['created_at']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_execution_by_link_id(self):
        """Test getting execution result by Caldera link_id"""
        print("\nTesting GET execution by link ID...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/executions/by-link-id/{self.test_link_id}")
            
            print(f"GET by link ID response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Retrieved by link ID: {result['command']}")
                print(f"Link ID: {result['link_id']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_executions_by_operation(self):
        """Test getting execution results by operation"""
        print("\nTesting GET executions by operation...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/executions/by-operation/{self.test_operation_id}")
            
            print(f"GET by operation response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total executions for operation: {result['total']}")
                print(f"Returned executions: {len(result['execution_results'])}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_execution_with_operation(self):
        """Test getting execution result with related operation data"""
        if not self.created_execution_id:
            print("Skipping GET with operation test - no execution created")
            return
            
        print("\nTesting GET execution with operation...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/executions/with-operation/{self.created_execution_id}")
            
            print(f"GET with operation response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Retrieved with operation: {result['command']}")
                print(f"Operation ID: {result['operation_id']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_list_executions(self):
        """Test listing execution results with filters"""
        print("\nTesting LIST executions...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            # Test basic list
            response = await client.get("/executions/")
            print(f"LIST response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total executions: {result['total']}")
                print(f"Returned executions: {len(result['execution_results'])}")
            
            # Test filter by operation
            response = await client.get(f"/executions/?operation_id={self.test_operation_id}")
            print(f"LIST by operation response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Filtered by operation: {len(result['execution_results'])} results")
            
            # Test filter by agent
            response = await client.get("/executions/?agent_paw=test-paw-123")
            print(f"LIST by agent response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Filtered by agent: {len(result['execution_results'])} results")
    
    async def test_update_execution(self):
        """Test updating an execution result"""
        if not self.created_execution_id:
            print("Skipping UPDATE test - no execution created")
            return
            
        print("\nTesting UPDATE execution...")
        
        update_data = {
            "command": "whoami && pwd",
            "status": 0,
            "link_state": "SUCCESS",
            "result_data": {
                "stdout": "testuser\n/home/testuser",
                "stderr": "",
                "exit_code": 0
            }
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.put(f"/executions/{self.created_execution_id}", json=update_data)
            
            print(f"UPDATE response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Updated command: {result['command']}")
                print(f"Updated result data: {result['result_data']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_recent_executions(self):
        """Test getting recent executions"""
        print("\nTesting recent executions...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get("/executions/recent/24")
            
            print(f"Recent executions response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Recent executions (24h): {len(result['execution_results'])} results")
            else:
                print(f"Error: {response.text}")
    
    async def test_failed_executions(self):
        """Test getting failed executions"""
        print("\nTesting failed executions...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get("/executions/failed/list")
            
            print(f"Failed executions response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Failed executions: {len(result['execution_results'])} results")
            else:
                print(f"Error: {response.text}")
    
    async def test_delete_execution(self):
        """Test deleting an execution result"""
        if not self.created_execution_id:
            print("Skipping DELETE test - no execution created")
            return
            
        print("\nTesting DELETE execution...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.delete(f"/executions/{self.created_execution_id}")
            
            print(f"DELETE response: {response.status_code}")
            if response.status_code == 204:
                print("Execution deleted successfully")
                
                # Verify deletion
                get_response = await client.get(f"/executions/{self.created_execution_id}")
                print(f"GET after DELETE: {get_response.status_code}")
                if get_response.status_code == 404:
                    print("Deletion verified - execution not found")
            else:
                print(f"Error: {response.text}")
    
    async def run_all_tests(self):
        """Run all CRUD tests"""
        print("Starting Execution Results CRUD Tests")
        print("=" * 50)
        
        # Create operation first
        if not await self.test_create_operation_first():
            print("Failed to create test operation. Exiting.")
            return
        
        # Run CRUD tests
        await self.test_create_execution_result()
        await self.test_get_execution_by_id()
        await self.test_get_execution_by_link_id()
        await self.test_get_executions_by_operation()
        await self.test_get_execution_with_operation()
        await self.test_list_executions()
        await self.test_update_execution()
        await self.test_recent_executions()
        await self.test_failed_executions()
        await self.test_delete_execution()
        
        print("\n" + "=" * 50)
        print("Execution Results CRUD Tests Completed")


async def main():
    """Main test runner"""
    test = ExecutionResultsCRUDTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 