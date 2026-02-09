import json
from pathlib import Path
from typing import Any

from loguru import logger


class ProfileManager:
    """
    Manages persistent browser profiles (cookies, localStorage, sessionStorage).
    Mimics returning user behavior for better stealth.
    """

    def __init__(self, profiles_dir: str = "./browser_profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def save_profile(self, profile_name: str, storage_state: Any) -> None:
        """Save browser storage state to disk."""
        profile_path = self.profiles_dir / f"{profile_name}.json"

        try:
            with open(profile_path, "w", encoding="utf-8") as f:
                json.dump(storage_state, f, indent=2)
            logger.info(f"💾 Profile saved: {profile_name}")
        except Exception as e:
            logger.error(f"Failed to save profile: {e}")

    def load_profile(self, profile_name: str) -> Any | None:
        """Load browser storage state from disk."""
        profile_path = self.profiles_dir / f"{profile_name}.json"

        if not profile_path.exists():
            logger.info(f"📂 No existing profile: {profile_name}")
            return None

        try:
            with open(profile_path, encoding="utf-8") as f:
                storage_state = json.load(f)
            logger.info(f"📤 Profile loaded: {profile_name}")
            return storage_state
        except Exception as e:
            logger.error(f"Failed to load profile: {e}")
            return None

    def profile_exists(self, profile_name: str) -> bool:
        """Check if a profile exists."""
        return (self.profiles_dir / f"{profile_name}.json").exists()


# Global instance
profile_manager = ProfileManager()
