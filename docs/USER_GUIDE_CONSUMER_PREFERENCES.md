# Consumer Preferences - User Guide

## What is This?

The Consumer Preferences feature allows Claude to **remember your shopping preferences** and store them on the **blockchain** (BNB Chain). This means:

- Your preferences persist across conversations
- Your data is stored securely on decentralized storage
- You get personalized product recommendations

## Getting Started

### Step 1: Open Claude Desktop

Launch Claude Desktop on your computer. The consumer preferences MCP server will start automatically.

### Step 2: Tell Claude Your Preferences

Just talk naturally! Examples:

```
"I wear size 10 shoes"
"My budget is under £200"
"I prefer black and gray colors"
"I like trail running shoes"
"I prefer Nike and Adidas brands"
```

Or tell multiple preferences at once:
```
"I wear size 10 shoes, my budget is £200, and I prefer black trail running shoes"
```

### Step 3: See Your Saved Preferences

Ask Claude:
```
"What are my saved preferences?"
```

You'll see something like:
```
Shopping Preferences for you:
- Shoe Size: 10
- Max Budget: £200
- Colors: black, gray
- Shoe Type: trail
```

### Step 4: Get Personalized Recommendations

When you search for products, your preferences are automatically applied:

```
"Find me running shoes"
```

Claude will search for: `running shoes trail under £200 in black, gray`

### Step 5: Verify Blockchain Storage

Ask Claude:
```
"Check if my preferences are on the blockchain"
```

You'll see:
```
Local Storage: 3 preferences
  - shoe_size: 10
  - max_budget: 200
  - preferred_colors: ["black", "gray"]

Blockchain (Membase Hub):
  - Found 1 conversation(s) on chain
    - preferences_your_user_id
  - Data synced: Yes
```

## Available Commands

| What to Say | What Happens |
|-------------|--------------|
| "I wear size 10" | Saves your shoe size |
| "My budget is £200" | Saves your max budget |
| "I like black and blue colors" | Saves color preferences |
| "I prefer Nike and Adidas" | Saves brand preferences |
| "I want trail running shoes" | Saves shoe type preference |
| "What are my preferences?" | Shows all saved preferences |
| "Clear my preferences" | Deletes all your preferences |
| "Check blockchain sync" | Verifies on-chain storage |
| "Find me running shoes" | Searches with your preferences applied |

## Preference Types

| Type | Examples |
|------|----------|
| **Shoe Size** | "10", "10.5", "UK 9", "US 11" |
| **Budget** | "under £200", "max £150", "between £100-200" |
| **Colors** | "black", "white", "blue", "gray", "red" |
| **Brands** | "Nike", "Adidas", "ASICS", "New Balance" |
| **Type** | "trail", "road", "track", "cross-training" |
| **Gender** | "men's", "women's", "unisex" |
| **Features** | "waterproof", "lightweight", "cushioned" |
| **Season** | "summer", "winter", "all-season" |

## How It Works

```
You say: "I wear size 10"
           │
           ▼
    ┌──────────────┐
    │ Claude saves │──▶ Local storage (instant)
    │ preference   │──▶ BNB Chain (background)
    └──────────────┘
           │
           ▼
    "Preference saved! ⛓️ (syncing to BNB Chain)"
```

Your preferences are:
1. **Saved locally** - Instant, always available
2. **Synced to blockchain** - Decentralized, persistent storage

## Privacy & Data

- **Your data belongs to you** - Stored with your user ID
- **Decentralized storage** - No central server owns your data
- **Cross-platform** - Access your preferences from any compatible app
- **Deletable** - Say "clear my preferences" anytime

## Troubleshooting

### "Preferences not saving"
- Make sure Claude Desktop is connected to the MCP server
- Check the hammer icon in Claude Desktop - should show "consumer-preferences"

### "Blockchain sync failed"
- The blockchain hub may be temporarily busy
- Your preferences are still saved locally
- Try again later - sync happens automatically

### "Can't find my preferences"
- Ask: "What are my saved preferences?"
- If empty, your user ID may have changed between sessions

## Technical Details

- **Blockchain**: BNB Chain (Testnet)
- **Storage Layer**: Unibase Membase
- **Protocol**: Model Context Protocol (MCP)
- **Hub URL**: https://testnet.hub.membase.io

---

## Quick Start Checklist

- [ ] Open Claude Desktop
- [ ] Tell Claude your shoe size
- [ ] Tell Claude your budget
- [ ] Tell Claude your favorite colors
- [ ] Ask "What are my preferences?"
- [ ] Ask "Check blockchain sync"
- [ ] Search for products and see personalized results!
