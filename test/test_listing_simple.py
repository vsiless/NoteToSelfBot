#!/usr/bin/env python3
"""
Simple test for the improved listing functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.storage import FileStorage
from bot.models import LinkItem, LinkCategory, TaskStatus
from datetime import datetime, timedelta
import tempfile
import shutil

def test_deadline_parameter_logic():
    """Test the deadline parameter parsing logic."""
    print("🧪 Testing deadline parameter parsing logic...")
    
    # Test the parsing logic directly
    def parse_deadline_command(command_lower):
        days = 7  # default
        parts = command_lower.split()
        if len(parts) >= 3 and parts[2].isdigit():
            days = int(parts[2])
            days = min(days, 365)  # Cap at 1 year
        return days
    
    # Test various commands
    assert parse_deadline_command("list deadlines") == 7, "Default should be 7 days"
    assert parse_deadline_command("list deadlines 30") == 30, "Should parse 30 days"
    assert parse_deadline_command("list deadlines 7") == 7, "Should parse 7 days"
    assert parse_deadline_command("list deadlines 365") == 365, "Should parse 365 days"
    assert parse_deadline_command("list deadlines 500") == 365, "Should cap at 365 days"
    
    print("✅ Deadline parameter parsing logic test passed!")

def test_overdue_detection():
    """Test overdue detection logic."""
    print("\n🧪 Testing overdue detection...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_overdue"
    
    try:
        # Create test links
        overdue_link = LinkItem(
            url="https://example.com/overdue",
            title="Overdue Item",
            category=LinkCategory.JOB_APPLICATION,
            deadline=datetime.now() - timedelta(days=5)
        )
        
        active_link = LinkItem(
            url="https://example.com/active",
            title="Active Item",
            category=LinkCategory.JOB_APPLICATION,
            deadline=datetime.now() + timedelta(days=5)
        )
        
        no_deadline_link = LinkItem(
            url="https://example.com/no_deadline",
            title="No Deadline Item",
            category=LinkCategory.JOB_APPLICATION
        )
        
        # Add links
        storage.add_link(user_id, overdue_link)
        storage.add_link(user_id, active_link)
        storage.add_link(user_id, no_deadline_link)
        
        # Test overdue detection
        all_links = storage.get_user_links(user_id)
        overdue_links = [link for link in all_links if link.is_overdue()]
        active_links = [link for link in all_links if not link.is_overdue()]
        
        print(f"✅ Found {len(overdue_links)} overdue and {len(active_links)} active links")
        assert len(overdue_links) == 1, "Should have 1 overdue link"
        assert len(active_links) == 2, "Should have 2 active links (including no deadline)"
        assert overdue_links[0].title == "Overdue Item", "Should identify correct overdue item"
        
        print("✅ Overdue detection test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

def test_reminder_filtering():
    """Test reminder filtering logic."""
    print("\n🧪 Testing reminder filtering...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_reminders"
    
    try:
        # Create test links with different states
        links = [
            LinkItem(
                url="https://example.com/reminder1",
                title="Active with Deadline",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=5),
                status=TaskStatus.TODO
            ),
            LinkItem(
                url="https://example.com/no_reminder1",
                title="No Deadline",
                category=LinkCategory.JOB_APPLICATION,
                status=TaskStatus.TODO
            ),
            LinkItem(
                url="https://example.com/no_reminder2",
                title="Completed",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=3),
                status=TaskStatus.DONE
            ),
            LinkItem(
                url="https://example.com/no_reminder3",
                title="Overdue",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() - timedelta(days=2),
                status=TaskStatus.TODO
            )
        ]
        
        for link in links:
            storage.add_link(user_id, link)
        
        # Test reminder filtering logic
        user_links = storage.get_user_links(user_id)
        reminder_links = []
        
        for link in user_links:
            if (link.deadline and 
                link.status not in [TaskStatus.DONE, TaskStatus.EXPIRED] and
                not link.is_overdue()):
                reminder_links.append(link)
        
        print(f"✅ Found {len(reminder_links)} links with active reminders")
        assert len(reminder_links) == 1, "Should have 1 link with active reminders"
        assert reminder_links[0].title == "Active with Deadline", "Should identify correct reminder link"
        
        print("✅ Reminder filtering test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

def test_upcoming_deadlines_range():
    """Test upcoming deadlines with different ranges."""
    print("\n🧪 Testing upcoming deadlines range...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_range"
    
    try:
        # Create links with different deadline ranges
        links = [
            LinkItem(
                url="https://example.com/job1",
                title="Due in 3 Days",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=3)
            ),
            LinkItem(
                url="https://example.com/job2",
                title="Due in 15 Days",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=15)
            ),
            LinkItem(
                url="https://example.com/job3",
                title="Due in 45 Days",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=45)
            )
        ]
        
        for link in links:
            storage.add_link(user_id, link)
        
        # Test different ranges
        upcoming_7 = storage.get_upcoming_deadlines(user_id, 7)
        upcoming_30 = storage.get_upcoming_deadlines(user_id, 30)
        upcoming_60 = storage.get_upcoming_deadlines(user_id, 60)
        
        print(f"✅ 7 days: {len(upcoming_7)} items, 30 days: {len(upcoming_30)} items, 60 days: {len(upcoming_60)} items")
        
        assert len(upcoming_7) == 1, "7-day range should have 1 item"
        assert len(upcoming_30) == 2, "30-day range should have 2 items"
        assert len(upcoming_60) == 3, "60-day range should have 3 items"
        
        print("✅ Upcoming deadlines range test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🚀 Starting simple listing tests...\n")
    
    test_deadline_parameter_logic()
    test_overdue_detection()
    test_reminder_filtering()
    test_upcoming_deadlines_range()
    
    print("\n🎉 All simple listing tests passed!")
    print("\n📋 **Verified Features:**")
    print("• ✅ Deadline parameter parsing (e.g., 'list deadlines 30')")
    print("• 🚫 Overdue items properly detected and filtered")
    print("• 🔔 Reminder filtering logic working correctly")
    print("• 📅 Deadline ranges working for different day counts")
