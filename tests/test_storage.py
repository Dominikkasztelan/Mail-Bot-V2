# tests/test_storage.py
import os
from unittest.mock import patch, mock_open
from src.storage_manager import StorageManager

def test_save_account_creates_file():
    identity = {
        "login": "jan.kowalski",
        "password": "pass",
        "first_name": "Jan",
        "last_name": "Kowalski",
        "domain": "interia.pl"
    }
    
    with patch("builtins.open", mock_open()) as mock_file:
        with patch("os.fsync"):
            mgr = StorageManager("dummy.txt")
            mgr.save_account(identity)
            
            mock_file.assert_called_with("dummy.txt", "a", encoding="utf-8")
            handle = mock_file()
            handle.write.assert_called()
            # Verify content format (roughly)
            args, _ = handle.write.call_args
            assert "jan.kowalski@interia.pl" in args[0]
