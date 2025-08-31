#!/usr/bin/env python3
"""
Debug script to manually trigger reminders for existing user data.
"""

import logging
from bot.reminder_system import ReminderSystem
from bot.storage import FileStorage

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def debug_reminders():
    """Debug the reminder system with actual user data."""
    
    # Use the real storage directory
    storage = FileStorage("data")
    
    messages_sent = []
    def mock_send_message(user_id: str, message: str):
        print(f"📱 REMINDER SENT to {user_id}:")
        print(f"   {message[:200]}...")
        print()
        messages_sent.append({"user_id": user_id, "message": message})
    
    # Create reminder system
    reminder_system = ReminderSystem(storage, mock_send_message)
    
    print("🔍 Manually triggering immediate reminder check...")
    reminder_system.trigger_immediate_reminder_check()
    
    print(f"\n📊 Results: {len(messages_sent)} reminders sent")
    
    if not messages_sent:
        print("❌ No reminders sent. Debugging...")
        
        # Check users
        users = reminder_system._get_all_users()
        print(f"Found {len(users)} users: {users}")
        
        for user_id in users:
            links = storage.get_user_links(user_id)
            print(f"\nUser {user_id}: {len(links)} links")
            
            for i, link in enumerate(links):
                if link.deadline:
                    print(f"  Link {i}: {link.title[:50]}")
                    print(f"    Created: {link.created_at}")
                    print(f"    Deadline: {link.deadline}")
                    print(f"    Reminder sent: {link.reminder_sent}")
                    print(f"    Status: {link.status}")

if __name__ == "__main__":
    debug_reminders()
