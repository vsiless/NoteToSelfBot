import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from .models import UserData, LinkItem, TaskStatus, LinkCategory

class FileStorage:
    """Simple file-based storage for user data."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def _get_user_file(self, user_id: str) -> str:
        """Get the file path for a user's data."""
        return os.path.join(self.data_dir, f"user_{user_id}.json")
    
    def save_user_data(self, user_data: UserData) -> bool:
        """Save user data to file."""
        try:
            file_path = self._get_user_file(user_data.user_id)
            
            # Convert to serializable format
            data = {
                "user_id": user_data.user_id,
                "links": [link.to_dict() for link in user_data.links],
                "preferences": user_data.preferences,
                "created_at": user_data.created_at.isoformat(),
                "updated_at": user_data.updated_at.isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error saving user data: {e}")
            return False
    
    def load_user_data(self, user_id: str) -> Optional[UserData]:
        """Load user data from file."""
        try:
            file_path = self._get_user_file(user_id)
            
            if not os.path.exists(file_path):
                return UserData(user_id=user_id)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct UserData object
            user_data = UserData(
                user_id=data["user_id"],
                preferences=data.get("preferences", {}),
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
            
            # Reconstruct LinkItem objects
            for link_data in data.get("links", []):
                link = LinkItem.from_dict(link_data)
                user_data.links.append(link)
            
            return user_data
        except Exception as e:
            print(f"Error loading user data: {e}")
            return UserData(user_id=user_id)
    
    def add_link(self, user_id: str, link: LinkItem) -> bool:
        """Add a link to user's data."""
        user_data = self.load_user_data(user_id)
        user_data.add_link(link)
        return self.save_user_data(user_data)
    
    def update_link_status(self, user_id: str, link_id: str, status: TaskStatus) -> bool:
        """Update link status."""
        user_data = self.load_user_data(user_id)
        if user_data.update_link_status(link_id, status):
            return self.save_user_data(user_data)
        return False
    
    def delete_link(self, user_id: str, link_id: str) -> bool:
        """Delete a link."""
        user_data = self.load_user_data(user_id)
        if user_data.delete_link(link_id):
            return self.save_user_data(user_data)
        return False
    
    def get_user_links(self, user_id: str) -> List[LinkItem]:
        """Get all links for a user."""
        user_data = self.load_user_data(user_id)
        return user_data.links
    
    def get_overdue_links(self, user_id: str) -> List[LinkItem]:
        """Get overdue links for a user."""
        user_data = self.load_user_data(user_id)
        return user_data.get_overdue_links()
    
    def get_upcoming_deadlines(self, user_id: str, days: int = 7) -> List[LinkItem]:
        """Get upcoming deadlines for a user."""
        user_data = self.load_user_data(user_id)
        return user_data.get_upcoming_deadlines(days)
    
    def update_link(self, user_id: str, link_id: str, updated_link: LinkItem) -> bool:
        """Update an existing link."""
        user_data = self.load_user_data(user_id)
        
        # Find and update the link
        for i, link in enumerate(user_data.links):
            if link.id == link_id:
                user_data.links[i] = updated_link
                return self.save_user_data(user_data)
        
        return False
