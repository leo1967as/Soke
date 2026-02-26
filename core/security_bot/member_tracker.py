"""Member tracking system for verified members."""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class MemberTracker:
    """Track verified members and their verification status."""
    
    def __init__(self, data_file: Optional[Path] = None):
        if data_file is None:
            data_file = Path(__file__).parent.parent.parent / "logs" / "verified_members.json"
        
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(exist_ok=True)
        self._data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Load member data from file."""
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load member data: {e}")
                return {"members": {}, "last_updated": None}
        return {"members": {}, "last_updated": None}
    
    def _save_data(self):
        """Save member data to file."""
        try:
            self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved member data to {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to save member data: {e}")
    
    def add_member(self, user_id: int, username: str, verified_at: Optional[str] = None):
        """Add or update a verified member."""
        if verified_at is None:
            verified_at = datetime.now(timezone.utc).isoformat()
        
        user_id_str = str(user_id)
        
        if user_id_str in self._data["members"]:
            # Update existing member
            self._data["members"][user_id_str]["username"] = username
            self._data["members"][user_id_str]["last_verified"] = verified_at
            self._data["members"][user_id_str]["verification_count"] = \
                self._data["members"][user_id_str].get("verification_count", 1) + 1
        else:
            # Add new member
            self._data["members"][user_id_str] = {
                "username": username,
                "first_verified": verified_at,
                "last_verified": verified_at,
                "verification_count": 1
            }
        
        self._save_data()
        logger.info(f"Tracked verified member: {username} ({user_id})")
    
    def is_tracked(self, user_id: int) -> bool:
        """Check if member is already tracked."""
        return str(user_id) in self._data["members"]
    
    def get_member(self, user_id: int) -> Optional[Dict]:
        """Get member data."""
        return self._data["members"].get(str(user_id))
    
    def get_all_members(self) -> Dict[str, Dict]:
        """Get all tracked members."""
        return self._data["members"]
    
    def get_stats(self) -> Dict:
        """Get tracking statistics."""
        return {
            "total_members": len(self._data["members"]),
            "last_updated": self._data.get("last_updated"),
            "data_file": str(self.data_file)
        }
    
    def remove_member(self, user_id: int):
        """Remove a member from tracking."""
        user_id_str = str(user_id)
        if user_id_str in self._data["members"]:
            del self._data["members"][user_id_str]
            self._save_data()
            logger.info(f"Removed member from tracking: {user_id}")
    
    def sync_with_guild(self, guild_members: List[tuple]) -> Dict:
        """
        Sync tracked members with actual guild members.
        
        Args:
            guild_members: List of (user_id, username, has_member_role) tuples
        
        Returns:
            Dict with sync results
        """
        added = []
        removed = []
        verified = []
        
        # Check current tracked members
        tracked_ids = set(self._data["members"].keys())
        guild_member_ids = {str(uid) for uid, _, has_role in guild_members if has_role}
        
        # Find members to remove (no longer have role)
        for user_id_str in tracked_ids:
            if user_id_str not in guild_member_ids:
                removed.append(user_id_str)
                self.remove_member(int(user_id_str))
        
        # Find members to add (have role but not tracked)
        for user_id, username, has_role in guild_members:
            user_id_str = str(user_id)
            if has_role:
                if user_id_str not in tracked_ids:
                    self.add_member(user_id, username)
                    added.append(user_id_str)
                else:
                    verified.append(user_id_str)
        
        return {
            "added": len(added),
            "removed": len(removed),
            "verified": len(verified),
            "total": len(self._data["members"])
        }
