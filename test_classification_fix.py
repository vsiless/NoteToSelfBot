#!/usr/bin/env python3
"""
Test script to verify the enhanced link classification and reminder system.
"""

from bot.link_processor import LinkProcessor
from bot.models import LinkCategory
from datetime import datetime, timedelta

def test_classification_fixes():
    """Test that the classification fixes work for startup programs."""
    processor = LinkProcessor()
    
    # Test Google Gemini Founders Forum
    google_url = "https://startup.google.com/programs/gemini-founders-forum/"
    google_category = processor.categorize_link(google_url, "")
    print(f"Google Gemini Founders Forum: {google_category}")
    assert google_category == LinkCategory.GRANT_APPLICATION, f"Expected GRANT_APPLICATION, got {google_category}"
    
    # Test Cohere Scholars Program
    cohere_url = "https://cohere.com/research/scholars-program"
    cohere_category = processor.categorize_link(cohere_url, "")
    print(f"Cohere Scholars Program: {cohere_category}")
    assert cohere_category == LinkCategory.GRANT_APPLICATION, f"Expected GRANT_APPLICATION, got {cohere_category}"
    
    # Test with context containing program keywords
    program_context = "This is a great startup accelerator program for founders"
    context_category = processor.categorize_link("https://example.com/program", program_context)
    print(f"Program with context: {context_category}")
    assert context_category == LinkCategory.GRANT_APPLICATION, f"Expected GRANT_APPLICATION, got {context_category}"
    
    print("✅ All classification tests passed!")

def test_reminder_scheduling():
    """Test the reminder scheduling logic."""
    from bot.reminder_system import ReminderSystem
    from bot.storage import FileStorage
    from bot.models import LinkItem, TaskStatus
    import tempfile
    import os
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    
    messages_sent = []
    def mock_send_message(user_id: str, message: str):
        messages_sent.append({"user_id": user_id, "message": message})
    
    reminder_system = ReminderSystem(storage, mock_send_message)
    
    # Create a test link with deadline
    test_link = LinkItem(
        url="https://startup.google.com/programs/gemini-founders-forum/",
        title="Google Gemini Founders Forum Application",
        category=LinkCategory.GRANT_APPLICATION,
        deadline=datetime.now() + timedelta(days=30)  # 30 days from now
    )
    
    # Test adding link with reminders
    success = reminder_system.add_link_with_reminders("test_user", test_link)
    assert success, "Failed to add link with reminders"
    
    # Verify link was stored
    stored_links = storage.get_user_links("test_user")
    assert len(stored_links) == 1, f"Expected 1 link, got {len(stored_links)}"
    assert stored_links[0].category == LinkCategory.GRANT_APPLICATION, "Category not preserved"
    
    print("✅ Reminder scheduling test passed!")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)

def main():
    """Run all tests."""
    print("🧪 Testing Enhanced Classification and Reminders...\n")
    
    try:
        test_classification_fixes()
        print()
        test_reminder_scheduling()
        print("\n🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
