#!/usr/bin/env python3
"""
Test script for Checking Engine FastAPI app
"""
import asyncio
import uvicorn
from checking_engine.main import app
from checking_engine.database.connection import test_connection

async def test_database():
    """Test database connection"""
    print("Testing database connection...")
    await test_connection()

def test_app():
    """Test FastAPI app startup"""
    print("Testing FastAPI app...")
    print(f"App title: {app.title}")
    print(f"App version: {app.version}")
    print(f"Debug mode: {app.debug}")
    print("FastAPI app created successfully")

if __name__ == "__main__":
    print("Testing Checking Engine Backend...")
    
    # Test database connection
    asyncio.run(test_database())
    
    # Test app creation
    test_app()
    
    print("\nAll tests passed! Ready to run with:")
    print("uvicorn checking_engine.main:app --host 127.0.0.1 --port 1337 --reload") 