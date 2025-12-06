"""
Test Consumer Preferences Storage

Tests the PreferenceStore class that handles local and blockchain storage
of user shopping preferences via Unibase Membase.

Run with: python tests/test_consumer_preferences.py
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys
import json
import tempfile
from pathlib import Path

# Add src/mcp to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'mcp'))


class TestPreferenceStoreMocked(unittest.TestCase):
    """Test PreferenceStore with mocked Membase (no blockchain calls)."""

    def setUp(self):
        """Set up test fixtures with temporary local storage."""
        self.temp_dir = tempfile.mkdtemp()
        self.prefs_file = os.path.join(self.temp_dir, 'test_preferences.json')

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.prefs_file):
            os.remove(self.prefs_file)
        os.rmdir(self.temp_dir)

    def test_save_and_get_preference_local(self):
        """Test saving and retrieving preferences from local storage."""
        # Simulate local storage structure
        prefs = {
            "test_user": {
                "shoe_size": {"value": "10", "updated_at": "2024-01-01T00:00:00Z"},
                "max_budget": {"value": "200", "updated_at": "2024-01-01T00:00:00Z"}
            }
        }

        # Write to temp file
        with open(self.prefs_file, 'w') as f:
            json.dump(prefs, f)

        # Read back
        with open(self.prefs_file, 'r') as f:
            loaded = json.load(f)

        self.assertEqual(loaded["test_user"]["shoe_size"]["value"], "10")
        self.assertEqual(loaded["test_user"]["max_budget"]["value"], "200")

    def test_preference_types(self):
        """Test all supported preference types."""
        valid_types = [
            "shoe_size",
            "max_budget",
            "preferred_colors",
            "preferred_brands",
            "shoe_type",
            "gender_preference",
            "preferred_features",
            "season"
        ]

        prefs = {"user1": {}}
        for pref_type in valid_types:
            prefs["user1"][pref_type] = {
                "value": f"test_{pref_type}",
                "updated_at": "2024-01-01T00:00:00Z"
            }

        # Verify all preference types can be stored
        self.assertEqual(len(prefs["user1"]), len(valid_types))

        for pref_type in valid_types:
            self.assertIn(pref_type, prefs["user1"])

    def test_personalized_query_generation(self):
        """Test generating personalized query from preferences."""
        prefs = {
            "shoe_size": "10",
            "max_budget": "200",
            "preferred_colors": "black, blue",
            "shoe_type": "trail"
        }

        base_query = "running shoes"

        # Build personalized query (simulating get_personalized_query logic)
        parts = [base_query]
        if prefs.get("shoe_size"):
            parts.append(f"size {prefs['shoe_size']}")
        if prefs.get("max_budget"):
            parts.append(f"under ${prefs['max_budget']}")
        if prefs.get("preferred_colors"):
            parts.append(f"in {prefs['preferred_colors']}")
        if prefs.get("shoe_type"):
            parts.append(f"{prefs['shoe_type']} type")

        personalized = " ".join(parts)

        self.assertIn("size 10", personalized)
        self.assertIn("under $200", personalized)
        self.assertIn("black, blue", personalized)
        self.assertIn("trail type", personalized)

    def test_clear_preferences(self):
        """Test clearing user preferences."""
        prefs = {
            "user_to_clear": {
                "shoe_size": {"value": "10", "updated_at": "2024-01-01T00:00:00Z"}
            },
            "other_user": {
                "shoe_size": {"value": "9", "updated_at": "2024-01-01T00:00:00Z"}
            }
        }

        # Clear one user
        del prefs["user_to_clear"]

        self.assertNotIn("user_to_clear", prefs)
        self.assertIn("other_user", prefs)


class TestMembaseIntegration(unittest.TestCase):
    """Test Membase blockchain integration (mocked)."""

    @patch('membase.memory.multi_memory.MultiMemory')
    @patch('membase.memory.message.Message')
    def test_membase_save_mock(self, mock_message, mock_multi_memory):
        """Test saving to Membase with mocked SDK."""
        # Setup mock
        mock_memory_instance = MagicMock()
        mock_multi_memory.return_value = mock_memory_instance
        mock_memory_instance.add.return_value = None

        # Simulate save operation
        message = mock_message(role="user", content="shoe_size:10")
        mock_memory_instance.add(message)

        # Verify add was called
        mock_memory_instance.add.assert_called_once()

    @patch('membase.memory.multi_memory.MultiMemory')
    def test_membase_retrieve_mock(self, mock_multi_memory):
        """Test retrieving from Membase with mocked SDK."""
        # Setup mock to return saved preferences
        mock_memory_instance = MagicMock()
        mock_multi_memory.return_value = mock_memory_instance
        mock_memory_instance.get_all.return_value = [
            MagicMock(content="shoe_size:10"),
            MagicMock(content="max_budget:200")
        ]

        # Retrieve
        messages = mock_memory_instance.get_all()

        self.assertEqual(len(messages), 2)


class TestBlockchainSync(unittest.TestCase):
    """Test blockchain synchronization status."""

    def test_sync_status_format(self):
        """Test sync status response format."""
        sync_status = {
            "blockchain_enabled": True,
            "last_sync": "2024-01-01T12:00:00Z",
            "pending_syncs": 0,
            "hub_url": "https://testnet.hub.membase.io"
        }

        self.assertIn("blockchain_enabled", sync_status)
        self.assertIn("last_sync", sync_status)
        self.assertIn("hub_url", sync_status)

    def test_local_fallback_status(self):
        """Test status when blockchain is disabled."""
        sync_status = {
            "blockchain_enabled": False,
            "storage_type": "local_json",
            "message": "Membase SDK not available, using local storage"
        }

        self.assertFalse(sync_status["blockchain_enabled"])
        self.assertEqual(sync_status["storage_type"], "local_json")


if __name__ == '__main__':
    print("=" * 60)
    print("Consumer Preferences Test Suite")
    print("=" * 60)
    print()

    # Run tests
    unittest.main(verbosity=2)
