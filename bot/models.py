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
    PAUSED = "paused"
    WAITING = "waiting"

class ProgressMilestone(BaseModel):
    """Progress milestone for tracking task completion."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    target_date: Optional[datetime] = None

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
    milestones: List[ProgressMilestone] = Field(default_factory=list)
    progress_percentage: int = Field(default=0, ge=0, le=100)
    last_activity: Optional[datetime] = None
    reminder_sent: Optional[datetime] = None
    
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
    
    def add_milestone(self, title: str, description: Optional[str] = None, target_date: Optional[datetime] = None) -> ProgressMilestone:
        """Add a new milestone."""
        milestone = ProgressMilestone(title=title, description=description, target_date=target_date)
        self.milestones.append(milestone)
        self.updated_at = datetime.now()
        return milestone
    
    def complete_milestone(self, milestone_id: str) -> bool:
        """Mark a milestone as completed."""
        for milestone in self.milestones:
            if milestone.id.startswith(milestone_id):
                milestone.completed = True
                milestone.completed_at = datetime.now()
                self.last_activity = datetime.now()
                self.updated_at = datetime.now()
                self._update_progress()
                return True
        return False
    
    def _update_progress(self):
        """Update progress percentage based on completed milestones."""
        if not self.milestones:
            return
        completed = sum(1 for m in self.milestones if m.completed)
        self.progress_percentage = int((completed / len(self.milestones)) * 100)
    
    def get_progress_summary(self) -> str:
        """Get a summary of progress."""
        if not self.milestones:
            return f"Progress: {self.progress_percentage}%"
        
        completed = sum(1 for m in self.milestones if m.completed)
        total = len(self.milestones)
        return f"Progress: {self.progress_percentage}% ({completed}/{total} milestones)"
    
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
            "priority": self.priority,
            "milestones": [
                {
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "completed": m.completed,
                    "completed_at": m.completed_at.isoformat() if m.completed_at else None,
                    "target_date": m.target_date.isoformat() if m.target_date else None
                } for m in self.milestones
            ],
            "progress_percentage": self.progress_percentage,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "reminder_sent": self.reminder_sent.isoformat() if self.reminder_sent else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LinkItem':
        """Create from dictionary."""
        link = cls(
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
            priority=data.get("priority", 1),
            progress_percentage=data.get("progress_percentage", 0),
            last_activity=datetime.fromisoformat(data["last_activity"]) if data.get("last_activity") else None,
            reminder_sent=datetime.fromisoformat(data["reminder_sent"]) if data.get("reminder_sent") else None
        )
        
        # Reconstruct milestones
        for milestone_data in data.get("milestones", []):
            milestone = ProgressMilestone(
                id=milestone_data["id"],
                title=milestone_data["title"],
                description=milestone_data.get("description"),
                completed=milestone_data["completed"],
                completed_at=datetime.fromisoformat(milestone_data["completed_at"]) if milestone_data.get("completed_at") else None,
                target_date=datetime.fromisoformat(milestone_data["target_date"]) if milestone_data.get("target_date") else None
            )
            link.milestones.append(milestone)
        
        return link

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
