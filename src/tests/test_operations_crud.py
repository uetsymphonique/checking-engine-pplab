#!/usr/bin/env python3
"""
Test script for Operations CRUD endpoints
Tests all CRUD operations for the operations table
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4
import httpx

# Add src to path to import checking_engine
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from checking_engine.main import app


class OperationsCRUDTest:
    """Test class for Operations CRUD operations"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:1337/api/v1"
        self.test_operation_id = uuid4()
        self.test_operation_data = {
            "name": "Test Operation",
            "operation_id": str(self.test_operation_id),
            "operation_start": datetime.now(timezone.utc).isoformat(),
            "operation_metadata": {
                "test": True,
                "description": "Test operation for CRUD testing"
            }
        }
        self.created_operation_id = None
    
    async def test_health_endpoints(self):
        """Test health check endpoints"""
        print("Testing health endpoints...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            # Test basic health
            response = await client.get("/health/")
            print(f"Health check: {response.status_code}")
            if response.status_code == 200:
                try:
                    print(f"Response: {response.json()}")
                except Exception as e:
                    print(f"Response text: {response.text}")
            else:
                print(f"Error: {response.text}")
            
            # Test database health
            response = await client.get("/health/db/")
            print(f"DB health check: {response.status_code}")
            if response.status_code == 200:
                try:
                    print(f"Response: {response.json()}")
                except Exception as e:
                    print(f"Response text: {response.text}")
            else:
                print(f"Error: {response.text}")
    
    async def test_create_operation(self):
        """Test creating a new operation"""
        print("\nTesting CREATE operation...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.post("/operations/", json=self.test_operation_data)
            
            print(f"CREATE response: {response.status_code}")
            if response.status_code == 201:
                result = response.json()
                self.created_operation_id = result["id"]
                print(f"Created operation ID: {self.created_operation_id}")
                print(f"Operation name: {result['name']}")
                print(f"Caldera operation ID: {result['operation_id']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_operation_by_id(self):
        """Test getting operation by ID"""
        if not self.created_operation_id:
            print("Skipping GET test - no operation created")
            return
            
        print("\nTesting GET operation by ID...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/operations/{self.created_operation_id}")
            
            print(f"GET by ID response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Retrieved operation: {result['name']}")
                print(f"Created at: {result['created_at']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_get_operation_by_caldera_id(self):
        """Test getting operation by Caldera operation_id"""
        print("\nTesting GET operation by Caldera ID...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get(f"/operations/by-caldera-id/{self.test_operation_id}")
            
            print(f"GET by Caldera ID response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Retrieved operation by Caldera ID: {result['name']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_list_operations(self):
        """Test listing operations"""
        print("\nTesting LIST operations...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.get("/operations/")
            
            print(f"LIST response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Total operations: {result['total']}")
                print(f"Page: {result['page']}")
                print(f"Size: {result['size']}")
                print(f"Operations count: {len(result['operations'])}")
            else:
                print(f"Error: {response.text}")
    
    async def test_update_operation(self):
        """Test updating an operation"""
        if not self.created_operation_id:
            print("Skipping UPDATE test - no operation created")
            return
            
        print("\nTesting UPDATE operation...")
        
        update_data = {
            "name": "Updated Test Operation",
            "operation_metadata": {
                "test": True,
                "updated": True,
                "description": "Updated test operation"
            }
        }
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.put(f"/operations/{self.created_operation_id}", json=update_data)
            
            print(f"UPDATE response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"Updated operation name: {result['name']}")
                print(f"Updated at: {result['updated_at']}")
            else:
                print(f"Error: {response.text}")
    
    async def test_delete_operation(self):
        """Test deleting an operation"""
        if not self.created_operation_id:
            print("Skipping DELETE test - no operation created")
            return
            
        print("\nTesting DELETE operation...")
        
        async with httpx.AsyncClient(base_url=self.base_url, follow_redirects=True) as client:
            response = await client.delete(f"/operations/{self.created_operation_id}")
            
            print(f"DELETE response: {response.status_code}")
            if response.status_code == 204:
                print("Operation deleted successfully")
            else:
                print(f"Error: {response.text}")
    

    
    async def run_all_tests(self):
        """Run all CRUD tests"""
        print("Starting Operations CRUD Tests")
        print("=" * 50)
        
        try:
            await self.test_health_endpoints()
            await self.test_create_operation()
            await self.test_get_operation_by_id()
            await self.test_get_operation_by_caldera_id()
            await self.test_list_operations()
            await self.test_update_operation()
            await self.test_delete_operation()
            
            print("\n" + "=" * 50)
            print("All tests completed!")
            
        except Exception as e:
            print(f"Test failed with error: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Main test function"""
    test = OperationsCRUDTest()
    await test.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main()) 