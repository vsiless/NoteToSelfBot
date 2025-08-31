#!/usr/bin/env python3
"""
Test script for the enhanced link processor.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.link_processor import LinkProcessor

def test_cohere_scholars_link():
    """Test the link processor with the Cohere Scholars Program link."""
    
    print("🧪 Testing Enhanced Link Processor")
    print("=" * 50)
    
    # Test message with the Cohere Scholars Program link
    test_message = "Check out this opportunity: https://cohere.com/research/scholars-program"
    
    # Initialize the link processor
    processor = LinkProcessor()
    
    print(f"📝 Test message: {test_message}")
    print()
    
    # Process the message
    link_items = processor.process_message(test_message)
    
    if link_items:
        print("✅ Successfully processed link!")
        print()
        
        for i, item in enumerate(link_items, 1):
            print(f"🔗 Link {i}:")
            print(f"   URL: {item.url}")
            print(f"   Title: {item.title}")
            print(f"   Category: {item.category.value}")
            print(f"   Description: {item.description[:100]}...")
            if item.deadline:
                print(f"   Deadline: {item.deadline.strftime('%Y-%m-%d')}")
                print(f"   Days until deadline: {item.days_until_deadline}")
            else:
                print(f"   Deadline: Not found")
            print()
    else:
        print("❌ No links found in the message")

if __name__ == "__main__":
    test_cohere_scholars_link()
