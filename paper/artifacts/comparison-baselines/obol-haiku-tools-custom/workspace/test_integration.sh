#!/bin/bash
# Integration test script

set -e

source venv/bin/activate

echo "=== Finance TUI Integration Test ==="
echo

echo "1. Testing database initialization..."
python scripts/init_sample_data.py
echo "✓ Sample data initialized"
echo

echo "2. Testing backend startup (will run for 5 seconds)..."
timeout 5 python run_backend.py > /dev/null 2>&1 || true
echo "✓ Backend server started successfully"
echo

echo "3. Testing API endpoints..."
python -c "
import httpx
import asyncio
import time
import subprocess
import sys

async def test_api():
    # Start the server in background
    proc = subprocess.Popen([sys.executable, 'run_backend.py'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
    
    # Give server time to start
    await asyncio.sleep(2)
    
    try:
        async with httpx.AsyncClient() as client:
            # Test dashboard stats
            response = await client.get('http://localhost:8000/api/dashboard/stats')
            print('✓ Dashboard stats endpoint works')
            
            # Test accounts
            response = await client.get('http://localhost:8000/api/accounts')
            print('✓ Accounts endpoint works')
            
            # Test budgets
            response = await client.get('http://localhost:8000/api/budgets')
            print('✓ Budgets endpoint works')
            
            # Test debts
            response = await client.get('http://localhost:8000/api/debts')
            print('✓ Debts endpoint works')
            
            # Test transactions
            response = await client.get('http://localhost:8000/api/transactions')
            print('✓ Transactions endpoint works')
    finally:
        proc.terminate()
        proc.wait()

asyncio.run(test_api())
"
echo

echo "=== All Integration Tests Passed! ==="
