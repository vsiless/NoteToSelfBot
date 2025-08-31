from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class LinkCategory(str, Enum):
    """Categories for organizing links."""
    JOB_APPLICATION = "job_application"
    GRANT_APPLICATION = "grant_application"
    NOTES_TO_READ = "notes_to_read"
    RESEARCH = "research"
    LEARNING = "learning"
    PERSONAL = "personal"
    OTHER = "other"

class TaskStatus(str, Enum):
    """Status of tasks."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    EXPIRED = "expired"

class LinkItem(BaseModel):
    """Model for storing link information."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: str
    description: Optional[str] = None
    category: LinkCategory
    status: TaskStatus = TaskStatus.TODO
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    priority: int = Field(default=1, ge=1, le=5)  # 1=lowest, 5=highest
    
    def is_overdue(self) -> bool:
        """Check if the task is overdue."""
        if not self.deadline:
            return False
        return datetime.now() > self.deadline and self.status != TaskStatus.DONE
    
    def days_until_deadline(self) -> Optional[int]:
        """Get days until deadline (negative if overdue)."""
        if not self.deadline:
            return None
        delta = self.deadline - datetime.now()
        return delta.days
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "notes": self.notes,
            "priority": self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinkItem':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            url=data["url"],
            title=data["title"],
            description=data.get("description"),
            category=LinkCategory(data["category"]),
            status=TaskStatus(data["status"]),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            priority=data.get("priority", 1)
        )

class UserData(BaseModel):
    """Model for storing user-specific data."""
    user_id: str
    links: List[LinkItem] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_link(self, link: LinkItem) -> None:
        """Add a new link."""
        self.links.append(link)
        self.updated_at = datetime.now()
    
    def get_links_by_category(self, category: LinkCategory) -> List[LinkItem]:
        """Get links by category."""
        return [link for link in self.links if link.category == category]
    
    def get_links_by_status(self, status: TaskStatus) -> List[LinkItem]:
        """Get links by status."""
        return [link for link in self.links if link.status == status]
    
    def get_overdue_links(self) -> List[LinkItem]:
        """Get all overdue links."""
        return [link for link in self.links if link.is_overdue()]
    
    def get_upcoming_deadlines(self, days: int = 7) -> List[LinkItem]:
        """Get links with deadlines in the next N days."""
        now = datetime.now()
        upcoming = []
        for link in self.links:
            if link.deadline and link.status != TaskStatus.DONE:
                days_until = (link.deadline - now).days
                if 0 <= days_until <= days:
                    upcoming.append(link)
        return sorted(upcoming, key=lambda x: x.deadline)
    
    def update_link_status(self, link_id: str, status: TaskStatus) -> bool:
        """Update link status."""
        for link in self.links:
            if link.id == link_id:
                link.status = status
                link.updated_at = datetime.now()
                self.updated_at = datetime.now()
                return True
        return False
    
    def delete_link(self, link_id: str) -> bool:
        """Delete a link."""
        for i, link in enumerate(self.links):
            if link.id == link_id:
                del self.links[i]
                self.updated_at = datetime.now()
                return True
        return False
