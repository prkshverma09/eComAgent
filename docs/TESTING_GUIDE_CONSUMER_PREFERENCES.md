# Testing Guide - Consumer Preferences with Membase

This guide walks you through testing the Membase blockchain integration step by step.

---

## Prerequisites

Before testing, ensure you have:
- [x] Python 3.9+ installed
- [x] Virtual environment set up
- [x] Claude Desktop installed
- [x] Membase SDK installed (`pip install membase`)

---

## Part 1: Test Without Claude Desktop (Terminal)

### Step 1.1: Activate Virtual Environment

```bash
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent
source venv/bin/activate
```

### Step 1.2: Verify Membase SDK is Installed

```bash
python -c "import membase; print('Membase SDK:', membase.__name__)"
```

Expected output:
```
Membase SDK: membase
```

### Step 1.3: Test Local Preference Save (Fast Test)

```bash
python -c "
import os
import json
import time

os.environ['MEMBASE_ID'] = 'test_membase_id'

# Test the preference store
from datetime import datetime, timezone

start = time.time()

# Save to local file
storage_file = 'src/mcp/consumer_preferences.json'
storage = {}
if os.path.exists(storage_file):
    with open(storage_file, 'r') as f:
        storage = json.load(f)

test_user = 'terminal_test_user'
if test_user not in storage:
    storage[test_user] = {}

storage[test_user]['shoe_size'] = {
    'value': '10',
    'updated_at': datetime.now(timezone.utc).isoformat()
}

with open(storage_file, 'w') as f:
    json.dump(storage, f, indent=2)

elapsed = time.time() - start
print(f'Local save completed in {elapsed*1000:.1f}ms')
print(f'Saved: shoe_size = 10 for {test_user}')
"
```

Expected output:
```
Local save completed in 5.2ms
Saved: shoe_size = 10 for terminal_test_user
```

### Step 1.4: Test Membase Hub Connection

```bash
python -c "
import requests

hub_url = 'https://testnet.hub.membase.io'
print(f'Testing connection to {hub_url}...')

try:
    response = requests.post(
        f'{hub_url}/api/conversation',
        data={'owner': 'test_connection'},
        timeout=10
    )
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text[:100]}')
    print('Hub connection: SUCCESS')
except Exception as e:
    print(f'Hub connection: FAILED - {e}')
"
```

Expected output:
```
Testing connection to https://testnet.hub.membase.io...
Status: 200
Response: null
Hub connection: SUCCESS
```

### Step 1.5: Test Blockchain Upload

```bash
python -c "
import os
import json
import time

os.environ['MEMBASE_ID'] = 'ecomagent_test'

from membase.memory.multi_memory import MultiMemory
from membase.memory.message import Message

print('Creating Membase memory...')
memory = MultiMemory(
    membase_account='blockchain_test_user',
    auto_upload_to_hub=True,
    default_conversation_id='test_preferences'
)

print('Saving preference...')
msg = Message(
    name='pref_shoe_size',
    content=json.dumps({'key': 'shoe_size', 'value': '11', 'timestamp': '2025-12-06'}),
    role='user'
)
memory.add(msg)

print('Preference saved to memory!')
print('Waiting for hub sync...')
time.sleep(3)

# Verify on hub
import requests
response = requests.post(
    'https://testnet.hub.membase.io/api/conversation',
    data={'owner': 'blockchain_test_user'},
    timeout=10
)
print(f'Hub response: {response.json()}')
"
```

Expected output:
```
Creating Membase memory...
Saving preference...
Preference saved to memory!
Waiting for hub sync...
Hub response: ['test_preferences']
```

---

## Part 2: Test MCP Server Directly

### Step 2.1: Start MCP Server Manually

Open a terminal and run:

```bash
cd /mnt/e/Hackathon/UK\ AI\ Agent\ Hackathon\ Ep3/eComAgent
source venv/bin/activate
python src/mcp/consumer_mcp_server.py
```

You should see:
```
[timestamp] ============================================================
[timestamp] Consumer Preferences MCP Server Starting...
[timestamp] ============================================================
[timestamp] Membase ENABLED - ID: ecomagent_consumer_prefs
[timestamp] Membase Hub: https://testnet.hub.membase.io
[timestamp] Local fallback: .../consumer_preferences.json
[timestamp] Preference store initialized
[timestamp] Creating MCP server...
[timestamp] ============================================================
[timestamp] Consumer Preferences MCP Server READY
[timestamp] Tools: save_preference, get_preferences, clear_preferences,
[timestamp]        get_personalized_query, save_multiple_preferences,
[timestamp]        check_blockchain_sync
[timestamp] ============================================================
[timestamp] Waiting for requests from Claude Desktop...
```

Press `Ctrl+C` to stop the server.

---

## Part 3: Test in Claude Desktop

### Step 3.1: Restart Claude Desktop

1. **Close** Claude Desktop completely (check system tray)
2. **Reopen** Claude Desktop
3. Wait for it to fully load

### Step 3.2: Verify MCP Server Connected

1. Look for the **hammer icon** (🔨) in Claude Desktop
2. Click it to see connected MCP servers
3. You should see:
   - `consumer-preferences` (6 tools)
   - `product-search` (if configured)

### Step 3.3: Test Saving a Preference

Type in Claude Desktop:
```
I wear size 10 shoes and my budget is under £200
```

Expected response:
```
Preference saved! ⛓️ (syncing to BNB Chain in background)

**shoe_size**: 10

**All preferences for [your_user_id]:**
- Shoe Size: 10
- Max Budget: £200
```

### Step 3.4: Test Retrieving Preferences

Type:
```
What are my saved preferences?
```

Expected response:
```
Shopping Preferences for [your_user_id]:

- Shoe Size: 10
- Max Budget: £200
```

### Step 3.5: Test Blockchain Verification

Type:
```
Check if my preferences are synced to the blockchain
```

Expected response:
```
**Local Storage:** 2 preferences
  - shoe_size: 10
  - max_budget: 200

**Blockchain (Membase Memories):**
  - ✅ Found 2 preference(s) on blockchain!
  - Bucket: `preferences_Aswin`
  - Synced preferences:
    - shoe_size: 10
    - max_budget: 200

**Hub URL:** https://testnet.hub.membase.io
**Membase ID:** ecomagent_consumer_prefs

**Verify on Blockchain (Manual):**
  - Memories: https://testnet.hub.membase.io/needle.html?owner=Aswin
  - Look for: `preferences_Aswin`
```

### Step 3.6: Test Personalized Search

Type:
```
Find me running shoes
```

Claude should use your preferences to enhance the search query.

---

## Part 4: Verify On-Chain Storage (Browser)

### Step 4.1: Check Your Data on Membase Hub

After saving preferences in Claude Desktop, verify in browser:

1. Open: `https://testnet.hub.membase.io/needle.html?owner=YOUR_USER_ID`
   - Replace `YOUR_USER_ID` with your user ID (e.g., `Aswin`)

2. Look for `preferences_YOUR_USER_ID` entry:
   ```
   preferences_Aswin
   Aswin
   preferences_Aswin
   [block_number]
   [size] bytes
   [timestamp]
   ```

3. Click `[click to show]` to see the stored preference data

### Step 4.2: Check MCP Server Logs

View the logs:

**Windows (PowerShell):**
```powershell
Get-Content "C:\Users\$env:USERNAME\AppData\Roaming\Claude\logs\mcp-server-consumer-preferences.log" -Tail 50
```

**WSL/Linux:**
```bash
tail -50 /mnt/c/Users/aswin/AppData/Roaming/Claude/logs/mcp-server-consumer-preferences.log
```

Look for:
```
>>> save_preference: user=xxx, type=shoe_size, value=10
Saved to local: xxx/shoe_size
Queued blockchain upload: xxx/shoe_size
Background upload queued: xxx/shoe_size
```

---

## Part 5: Test Edge Cases

### Test 5.1: Save Invalid Budget

Type in Claude Desktop:
```
My budget is "not a number"
```

Expected: Error message about invalid budget format.

### Test 5.2: Clear All Preferences

Type:
```
Clear all my preferences
```

Then verify:
```
What are my preferences?
```

Expected: "No preferences saved"

### Test 5.3: Save Multiple Preferences at Once

Type:
```
Save these preferences: size 11, budget £300, colors blue and green, brand Nike
```

---

## Troubleshooting

### MCP Server Not Connected

1. Check Claude Desktop logs:
   ```
   C:\Users\<username>\AppData\Roaming\Claude\logs\mcp-server-consumer-preferences.log
   ```

2. Try running MCP server manually to see errors:
   ```bash
   python src/mcp/consumer_mcp_server.py
   ```

### Blockchain Sync Failed

1. Check if hub is accessible:
   ```bash
   curl https://testnet.hub.membase.io/api/conversation -X POST -d "owner=test"
   ```

2. Look for 599 errors in logs (hub overloaded, try later)

### Preferences Not Persisting

1. Check local file exists:
   ```bash
   cat src/mcp/consumer_preferences.json
   ```

2. Verify MEMBASE_ID is set in .env:
   ```bash
   grep MEMBASE_ID .env
   ```

---

## Test Checklist

- [ ] Virtual environment activated
- [ ] Membase SDK installed
- [ ] Local save works (< 10ms)
- [ ] Hub connection works (200 status)
- [ ] MCP server starts without errors
- [ ] Claude Desktop shows consumer-preferences server
- [ ] Can save preference in Claude Desktop
- [ ] Can retrieve preferences
- [ ] Can check blockchain sync
- [ ] Data appears on Membase hub

---

## Success Criteria

Your testing is complete when:

1. **Local storage works**: Preferences save in < 10ms
2. **MCP integration works**: Claude Desktop can save/retrieve preferences
3. **Blockchain sync works**: Data appears on `testnet.hub.membase.io`
4. **Verification works**: `check_blockchain_sync` shows data on chain
