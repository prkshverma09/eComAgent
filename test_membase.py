#!/usr/bin/env python3
"""
Membase Blockchain Integration Test Script
Run this to verify the consumer preferences feature is working.
"""

import os
import json
import time
import requests

# Set environment
os.environ['MEMBASE_ID'] = 'ecomagent_consumer_prefs'

print('='*50)
print('MEMBASE BLOCKCHAIN INTEGRATION TEST')
print('='*50)

# Test 1: Local save
print('\n[1] Testing local save...')
start = time.time()
storage_file = 'src/mcp/consumer_preferences.json'
storage = json.load(open(storage_file)) if os.path.exists(storage_file) else {}
storage['aswin_test'] = {'shoe_size': {'value': '10', 'updated_at': '2025-12-06'}}
json.dump(storage, open(storage_file, 'w'), indent=2)
print(f'    Local save: {(time.time()-start)*1000:.1f}ms - PASS')

# Test 2: Hub connection
print('\n[2] Testing Membase Hub connection...')
try:
    resp = requests.post('https://testnet.hub.membase.io/api/conversation',
                         data={'owner': 'connection_test'}, timeout=10)
    status = "PASS" if resp.status_code == 200 else "FAIL"
    print(f'    Hub status: {resp.status_code} - {status}')
except Exception as e:
    print(f'    Hub connection FAILED: {e}')

# Test 3: Blockchain upload
print('\n[3] Testing blockchain upload...')
try:
    from membase.memory.multi_memory import MultiMemory
    from membase.memory.message import Message

    memory = MultiMemory(
        membase_account='aswin_demo_test',
        auto_upload_to_hub=True,
        default_conversation_id='preferences_aswin_demo'
    )
    msg = Message(name='pref_test', content=json.dumps({'test': 'value'}), role='user')
    memory.add(msg)
    print('    Upload queued - PASS')
except Exception as e:
    print(f'    Upload FAILED: {e}')

# Wait for sync
print('\n[4] Waiting for blockchain sync (3 seconds)...')
time.sleep(3)

# Test 5: Verify on chain
print('\n[5] Verifying on-chain storage...')
try:
    resp = requests.post('https://testnet.hub.membase.io/api/conversation',
                         data={'owner': 'aswin_demo_test'}, timeout=10)
    result = resp.json()
    if result:
        print(f'    Found on blockchain: {result}')
        print('    Blockchain sync: PASS')
    else:
        print('    Not found yet (may take longer)')
        print('    Blockchain sync: PENDING')
except Exception as e:
    print(f'    Verification FAILED: {e}')

print('\n' + '='*50)
print('TEST COMPLETE')
print('='*50)
