#!/usr/bin/env python3
"""
Test the improved listing functionality for the Telegram bot.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.storage import FileStorage
from bot.models import LinkItem, LinkCategory, TaskStatus
from bot.langgraph_agent import LangGraphAgent
from datetime import datetime, timedelta
import tempfile
import shutil

def test_deadline_parameter_parsing():
    """Test that list deadlines accepts day parameters."""
    print("🧪 Testing deadline parameter parsing...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_deadlines"
    
    try:
        # Create a mock agent class to test just the list command method
        class MockAgent:
            def __init__(self, storage):
                self.storage = storage
            
            def _handle_list_command(self, command: str, user_id: str, storage: FileStorage) -> str:
                # Import the method from the real agent
                from bot.langgraph_agent import LangGraphAgent
                real_agent = type('MockAgent', (), {})()
                # Copy the method
                real_agent._handle_list_command = LangGraphAgent._handle_list_command.__get__(real_agent)
                real_agent._format_links_list = LangGraphAgent._format_links_list.__get__(real_agent)
                real_agent._get_links_with_reminders = LangGraphAgent._get_links_with_reminders.__get__(real_agent)
                return real_agent._handle_list_command(command, user_id, storage)
        
        agent = MockAgent(storage)
        
        # Create test links with different deadlines
        links = [
            LinkItem(
                url="https://example.com/job1",
                title="Job Due in 5 Days",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=5)
            ),
            LinkItem(
                url="https://example.com/job2", 
                title="Job Due in 15 Days",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=15)
            ),
            LinkItem(
                url="https://example.com/job3",
                title="Job Due in 45 Days", 
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=45)
            )
        ]
        
        # Add links to storage
        for link in links:
            storage.add_link(user_id, link)
        
        # Test default (7 days)
        response_7 = agent._handle_list_command("list deadlines", user_id, storage)
        print(f"✅ Default 7 days: Found {response_7.count('Job Due')}/3 jobs")
        assert "Job Due in 5 Days" in response_7, "Should include 5-day deadline"
        assert "Job Due in 15 Days" not in response_7, "Should not include 15-day deadline"
        
        # Test 30 days
        response_30 = agent._handle_list_command("list deadlines 30", user_id, storage)
        print(f"✅ 30 days: Found {response_30.count('Job Due')}/3 jobs")
        assert "Job Due in 5 Days" in response_30, "Should include 5-day deadline"
        assert "Job Due in 15 Days" in response_30, "Should include 15-day deadline"
        assert "Job Due in 45 Days" not in response_30, "Should not include 45-day deadline"
        
        # Test 60 days
        response_60 = agent._handle_list_command("list deadlines 60", user_id, storage)
        print(f"✅ 60 days: Found {response_60.count('Job Due')}/3 jobs")
        assert "Job Due in 45 Days" in response_60, "Should include 45-day deadline"
        
        print("✅ Deadline parameter parsing test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

def test_overdue_exclusion():
    """Test that overdue items are excluded from regular lists."""
    print("\n🧪 Testing overdue exclusion...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_overdue"
    
    try:
        agent = LangGraphAgent()
        agent.storage = storage
        
        # Create test links - some overdue, some active
        links = [
            LinkItem(
                url="https://example.com/overdue1",
                title="Overdue Job Application",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() - timedelta(days=5)  # Overdue
            ),
            LinkItem(
                url="https://example.com/active1",
                title="Active Job Application", 
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=5)  # Active
            ),
            LinkItem(
                url="https://example.com/overdue2",
                title="Overdue Grant",
                category=LinkCategory.GRANT_APPLICATION,
                deadline=datetime.now() - timedelta(days=2)  # Overdue
            ),
            LinkItem(
                url="https://example.com/active2",
                title="Active Grant",
                category=LinkCategory.GRANT_APPLICATION,
                deadline=datetime.now() + timedelta(days=10)  # Active
            )
        ]
        
        for link in links:
            storage.add_link(user_id, link)
        
        # Test "list all" excludes overdue
        response_all = agent._handle_list_command("list all", user_id, storage)
        print(f"✅ List all: {response_all.count('Active')}/2 active items shown")
        assert "Active Job Application" in response_all, "Should include active job"
        assert "Active Grant" in response_all, "Should include active grant"
        assert "Overdue Job Application" not in response_all, "Should exclude overdue job"
        assert "Overdue Grant" not in response_all, "Should exclude overdue grant"
        
        # Test "list jobs" excludes overdue
        response_jobs = agent._handle_list_command("list jobs", user_id, storage)
        print(f"✅ List jobs: Only active jobs shown")
        assert "Active Job Application" in response_jobs, "Should include active job"
        assert "Overdue Job Application" not in response_jobs, "Should exclude overdue job"
        
        # Test "list overdue" shows only overdue
        response_overdue = agent._handle_list_command("list overdue", user_id, storage)
        print(f"✅ List overdue: {response_overdue.count('Overdue')}/2 overdue items shown")
        assert "Overdue Job Application" in response_overdue, "Should include overdue job"
        assert "Overdue Grant" in response_overdue, "Should include overdue grant"
        assert "Active Job Application" not in response_overdue, "Should exclude active job"
        
        print("✅ Overdue exclusion test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

def test_reminders_list():
    """Test the new list reminders functionality."""
    print("\n🧪 Testing list reminders...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_reminders"
    
    try:
        agent = LangGraphAgent()
        agent.storage = storage
        
        # Create test links with different states
        links = [
            LinkItem(
                url="https://example.com/reminder1",
                title="Job with Deadline",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=5),
                status=TaskStatus.TODO
            ),
            LinkItem(
                url="https://example.com/reminder2",
                title="Grant with Deadline",
                category=LinkCategory.GRANT_APPLICATION,
                deadline=datetime.now() + timedelta(days=10),
                status=TaskStatus.IN_PROGRESS
            ),
            LinkItem(
                url="https://example.com/no_reminder1",
                title="Job without Deadline",
                category=LinkCategory.JOB_APPLICATION,
                status=TaskStatus.TODO
                # No deadline
            ),
            LinkItem(
                url="https://example.com/no_reminder2",
                title="Completed Job",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() + timedelta(days=3),
                status=TaskStatus.DONE  # Completed
            ),
            LinkItem(
                url="https://example.com/no_reminder3",
                title="Overdue Job",
                category=LinkCategory.JOB_APPLICATION,
                deadline=datetime.now() - timedelta(days=2),  # Overdue
                status=TaskStatus.TODO
            )
        ]
        
        for link in links:
            storage.add_link(user_id, link)
        
        # Test list reminders
        response_reminders = agent._handle_list_command("list reminders", user_id, storage)
        print(f"✅ List reminders response generated")
        
        # Should include items with deadlines that are not done/expired/overdue
        assert "Job with Deadline" in response_reminders, "Should include job with deadline"
        assert "Grant with Deadline" in response_reminders, "Should include grant with deadline"
        
        # Should exclude items without deadlines, completed items, and overdue items
        assert "Job without Deadline" not in response_reminders, "Should exclude job without deadline"
        assert "Completed Job" not in response_reminders, "Should exclude completed job"
        assert "Overdue Job" not in response_reminders, "Should exclude overdue job"
        
        print("✅ List reminders test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

def test_help_command_updated():
    """Test that help command shows updated information."""
    print("\n🧪 Testing updated help command...")
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        agent = LangGraphAgent()
        agent.storage = FileStorage(temp_dir)
        
        # Test help command
        response = agent._handle_special_request({
            "messages": [type('obj', (object,), {'content': 'help'})()],
            "user_id": "test_user",
            "storage": agent.storage
        })
        
        # Check that help includes new functionality
        help_content = response["messages"][-1].content
        assert "list deadlines [days]" in help_content, "Should mention deadline parameter"
        assert "list reminders" in help_content, "Should mention reminders command"
        assert "excludes overdue" in help_content, "Should mention overdue exclusion"
        
        print("✅ Help command test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🚀 Starting listing improvements tests...\n")
    
    test_deadline_parameter_parsing()
    test_overdue_exclusion()
    test_reminders_list()
    test_help_command_updated()
    
    print("\n🎉 All listing improvements tests passed!")
    print("\n📋 **New Listing Features:**")
    print("• ✅ 'list deadlines [days]' - Customizable deadline range")
    print("• 🔄 'list reminders' - Shows active reminders only")
    print("• 🚫 Overdue items excluded from regular lists")
    print("• 📊 'list overdue' - Dedicated overdue items view")
    print("• 🎯 Improved help documentation")
