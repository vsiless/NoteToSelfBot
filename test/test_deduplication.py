#!/usr/bin/env python3
"""
Test deduplication functionality for the Telegram bot.
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

def test_storage_deduplication():
    """Test deduplication at the storage level."""
    print("🧪 Testing storage-level deduplication...")
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_123"
    
    try:
        # Create first link
        link1 = LinkItem(
            url="https://example.com/job",
            title="Software Engineer Position",
            category=LinkCategory.JOB_APPLICATION,
            deadline=datetime.now() + timedelta(days=7),
            priority=3
        )
        
        # Add first link
        result_link1, is_new1 = storage.add_or_update_link(user_id, link1)
        print(f"✅ First add: is_new={is_new1}, title='{result_link1.title}'")
        assert is_new1 == True, "First link should be new"
        
        # Create second link with same URL but different info
        link2 = LinkItem(
            url="https://example.com/job",  # Same URL
            title="Senior Software Engineer Position",  # Different title
            category=LinkCategory.JOB_APPLICATION,
            deadline=datetime.now() + timedelta(days=5),  # Different deadline
            priority=4,  # Higher priority
            notes="Updated application details"
        )
        
        # Add second link (should update existing)
        result_link2, is_new2 = storage.add_or_update_link(user_id, link2)
        print(f"✅ Second add: is_new={is_new2}, title='{result_link2.title}'")
        assert is_new2 == False, "Second link should update existing"
        assert result_link2.title == "Senior Software Engineer Position", "Title should be updated"
        assert result_link2.priority == 4, "Priority should be updated to higher value"
        assert result_link2.notes == "Updated application details", "Notes should be updated"
        
        # Verify only one link exists
        user_links = storage.get_user_links(user_id)
        print(f"✅ Total links: {len(user_links)}")
        assert len(user_links) == 1, "Should have only one link after deduplication"
        
        # Verify the link has the updated information
        final_link = user_links[0]
        assert final_link.url == "https://example.com/job"
        assert final_link.title == "Senior Software Engineer Position"
        assert final_link.priority == 4
        
        print("✅ Storage deduplication test passed!")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def test_link_processor_deduplication():
    """Test deduplication through the link processor."""
    print("\n🧪 Testing link processor deduplication...")
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_456"
    
    try:
        from bot.link_processor import LinkProcessor
        processor = LinkProcessor()
        
        # Process first message with a link
        message1 = "Check out this job: https://google.com/careers/job123 - Software Engineer position due next week"
        links1 = processor.process_message(message1)
        print(f"✅ First processing found {len(links1)} links")
        
        if links1:
            result_link1, is_new1 = storage.add_or_update_link(user_id, links1[0])
            print(f"✅ First add: is_new={is_new1}, title='{result_link1.title}'")
            assert is_new1 == True, "First link should be new"
        
        # Process second message with same URL
        message2 = "Updated info for https://google.com/careers/job123 - Senior Software Engineer role, higher priority"
        links2 = processor.process_message(message2)
        print(f"✅ Second processing found {len(links2)} links")
        
        if links2:
            result_link2, is_new2 = storage.add_or_update_link(user_id, links2[0])
            print(f"✅ Second add: is_new={is_new2}, title='{result_link2.title}'")
            assert is_new2 == False, "Second link should update existing"
        
        # Verify only one link exists
        user_links = storage.get_user_links(user_id)
        print(f"✅ Total links after processing: {len(user_links)}")
        assert len(user_links) == 1, "Should have only one link after deduplication"
        
        print("✅ Link processor deduplication test passed!")
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def test_notes_merging():
    """Test that notes are properly merged when updating links."""
    print("\n🧪 Testing notes merging...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_789"
    
    try:
        # Create first link with notes
        link1 = LinkItem(
            url="https://example.com/grant",
            title="Research Grant",
            category=LinkCategory.GRANT_APPLICATION,
            notes="Initial application notes"
        )
        
        storage.add_or_update_link(user_id, link1)
        
        # Update with new notes
        link2 = LinkItem(
            url="https://example.com/grant",
            title="Updated Research Grant",
            category=LinkCategory.GRANT_APPLICATION,
            notes="Additional requirements found"
        )
        
        result_link, is_new = storage.add_or_update_link(user_id, link2)
        
        print(f"✅ Notes after update: {result_link.notes}")
        assert "Initial application notes" in result_link.notes, "Should preserve original notes"
        assert "Additional requirements found" in result_link.notes, "Should add new notes"
        assert "Updated" in result_link.notes, "Should include timestamp"
        
        print("✅ Notes merging test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

def test_tag_merging():
    """Test that tags are properly merged when updating links."""
    print("\n🧪 Testing tag merging...")
    
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    user_id = "test_user_abc"
    
    try:
        # Create first link with tags
        link1 = LinkItem(
            url="https://example.com/learning",
            title="Python Course",
            category=LinkCategory.LEARNING,
            tags=["python", "programming"]
        )
        
        storage.add_or_update_link(user_id, link1)
        
        # Update with additional tags
        link2 = LinkItem(
            url="https://example.com/learning",
            title="Advanced Python Course",
            category=LinkCategory.LEARNING,
            tags=["advanced", "python", "web-development"]  # "python" is duplicate
        )
        
        result_link, is_new = storage.add_or_update_link(user_id, link2)
        
        print(f"✅ Tags after update: {result_link.tags}")
        expected_tags = {"python", "programming", "advanced", "web-development"}
        actual_tags = set(result_link.tags)
        assert actual_tags == expected_tags, f"Expected {expected_tags}, got {actual_tags}"
        
        print("✅ Tag merging test passed!")
        
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    print("🚀 Starting deduplication tests...\n")
    
    test_storage_deduplication()
    test_link_processor_deduplication()
    test_notes_merging()
    test_tag_merging()
    
    print("\n🎉 All deduplication tests passed!")
    print("\n📋 **Deduplication Features:**")
    print("• ✅ Prevents duplicate links by URL")
    print("• 🔄 Updates existing links with new information")
    print("• 📝 Merges notes with timestamps")
    print("• 🏷️ Merges tags without duplicates")
    print("• ⬆️ Updates priority to higher values")
    print("• 📅 Updates deadlines when provided")
    print("• 📂 Always updates category classification")
