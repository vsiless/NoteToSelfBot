#!/usr/bin/env python3
"""
Test script to verify the 5-minute immediate reminder functionality.
"""

import time
import logging
from datetime import datetime, timedelta
from bot.reminder_system import ReminderSystem
from bot.storage import FileStorage
from bot.models import LinkItem, LinkCategory, TaskStatus
import tempfile
import shutil

# Set up logging to see debug messages
logging.basicConfig(level=logging.DEBUG)

def test_immediate_reminder():
    """Test the immediate reminder with actual timing."""
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    
    messages_sent = []
    def mock_send_message(user_id: str, message: str):
        print(f"📱 REMINDER SENT to {user_id}:")
        print(f"   {message}")
        messages_sent.append({"user_id": user_id, "message": message})
    
    # Create reminder system
    reminder_system = ReminderSystem(storage, mock_send_message)
    
    # Create a test link with deadline
    test_link = LinkItem(
        url="https://startup.google.com/programs/gemini-founders-forum/",
        title="Google Gemini Founders Forum Application",
        category=LinkCategory.GRANT_APPLICATION,
        deadline=datetime.now() + timedelta(days=30),
        created_at=datetime.now() - timedelta(minutes=6)  # Created 6 minutes ago
    )
    
    print(f"🧪 Testing immediate reminder for link created {test_link.created_at}")
    print(f"   Current time: {datetime.now()}")
    print(f"   Time since creation: {datetime.now() - test_link.created_at}")
    
    # Add the link
    success = reminder_system.add_link_with_reminders("test_user", test_link)
    print(f"✅ Link added successfully: {success}")
    
    # Manually trigger immediate reminder check
    print("\n🔍 Triggering immediate reminder check...")
    reminder_system.trigger_immediate_reminder_check()
    
    # Check if reminder was sent
    if messages_sent:
        print(f"\n✅ SUCCESS: {len(messages_sent)} reminder(s) sent!")
        for msg in messages_sent:
            print(f"   User: {msg['user_id']}")
            print(f"   Message preview: {msg['message'][:100]}...")
    else:
        print("\n❌ FAILED: No reminders were sent")
        
        # Debug: Check what links exist
        links = storage.get_user_links("test_user")
        print(f"\n🔍 Debug info:")
        print(f"   Found {len(links)} links for test_user")
        for link in links:
            print(f"   Link {link.id[:8]}:")
            print(f"     Created: {link.created_at}")
            print(f"     Deadline: {link.deadline}")
            print(f"     Reminder sent: {link.reminder_sent}")
            print(f"     Status: {link.status}")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    return len(messages_sent) > 0

def test_with_fresh_link():
    """Test with a link created right now to simulate real usage."""
    
    # Create temporary storage
    temp_dir = tempfile.mkdtemp()
    storage = FileStorage(temp_dir)
    
    messages_sent = []
    def mock_send_message(user_id: str, message: str):
        print(f"📱 REMINDER SENT to {user_id}:")
        print(f"   {message}")
        messages_sent.append({"user_id": user_id, "message": message})
    
    # Create reminder system
    reminder_system = ReminderSystem(storage, mock_send_message)
    
    # Create a test link with deadline (created now)
    test_link = LinkItem(
        url="https://cohere.com/research/scholars-program",
        title="Cohere Scholars Program",
        category=LinkCategory.GRANT_APPLICATION,
        deadline=datetime.now() + timedelta(days=45)
    )
    
    print(f"\n🧪 Testing with fresh link created now")
    print(f"   Current time: {datetime.now()}")
    
    # Add the link
    success = reminder_system.add_link_with_reminders("test_user", test_link)
    print(f"✅ Link added successfully: {success}")
    
    print("\n⏰ Waiting 6 minutes for reminder (simulated by changing created_at)...")
    
    # Simulate 6 minutes passing by updating the created_at time
    links = storage.get_user_links("test_user")
    if links:
        link = links[0]
        link.created_at = datetime.now() - timedelta(minutes=6)
        storage.update_link("test_user", link.id, link)
        print(f"   Updated link creation time to: {link.created_at}")
    
    # Trigger immediate reminder check
    print("\n🔍 Triggering immediate reminder check...")
    reminder_system.trigger_immediate_reminder_check()
    
    # Check results
    if messages_sent:
        print(f"\n✅ SUCCESS: {len(messages_sent)} reminder(s) sent!")
    else:
        print("\n❌ FAILED: No reminders were sent")
    
    # Cleanup
    shutil.rmtree(temp_dir)
    
    return len(messages_sent) > 0

def main():
    """Run all tests."""
    print("🧪 Testing 5-Minute Immediate Reminder Functionality\n")
    
    try:
        # Test 1: Link already 6 minutes old
        print("=" * 60)
        print("TEST 1: Link created 6 minutes ago")
        print("=" * 60)
        result1 = test_immediate_reminder()
        
        # Test 2: Fresh link with simulated time passage
        print("\n" + "=" * 60)
        print("TEST 2: Fresh link with simulated time passage")
        print("=" * 60)
        result2 = test_with_fresh_link()
        
        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Test 1 (6-minute old link): {'✅ PASSED' if result1 else '❌ FAILED'}")
        print(f"Test 2 (Fresh link): {'✅ PASSED' if result2 else '❌ FAILED'}")
        
        if result1 and result2:
            print("\n🎉 All tests passed! The 5-minute reminder system is working.")
        else:
            print("\n⚠️  Some tests failed. The reminder system needs debugging.")
            
        return result1 and result2
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
