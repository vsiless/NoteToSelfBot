#!/usr/bin/env python3
"""
Debug script to see what content is extracted from webpages.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.link_processor import LinkProcessor

def debug_webpage_content():
    """Debug the webpage content extraction."""
    
    print("🔍 Debugging Webpage Content Extraction")
    print("=" * 60)
    
    url = "https://cohere.com/research/scholars-program"
    processor = LinkProcessor()
    
    print(f"📄 Fetching content from: {url}")
    print()
    
    # Fetch webpage content
    content = processor.fetch_webpage_content(url)
    
    if content:
        print("✅ Successfully fetched webpage content!")
        print()
        
        print("📋 Title:")
        print(f"   {content['title']}")
        print()
        
        print("📝 Meta Description:")
        print(f"   {content['description']}")
        print()
        
        print("📄 Main Content (first 500 characters):")
        print(f"   {content['content'][:500]}...")
        print()
        
        # Look for deadline patterns in the content
        print("🔍 Searching for deadline patterns...")
        content_lower = content['content'].lower()
        
        # Look for specific deadline-related text
        deadline_keywords = ['deadline', 'apply by', 'application deadline', 'closes', 'ends']
        for keyword in deadline_keywords:
            if keyword in content_lower:
                # Find the context around the keyword
                index = content_lower.find(keyword)
                start = max(0, index - 50)
                end = min(len(content_lower), index + 100)
                context = content_lower[start:end]
                print(f"   Found '{keyword}' in context: ...{context}...")
        
        # Try to extract deadline
        deadline = processor.extract_deadline_from_content(content['content'])
        if deadline:
            print(f"   ✅ Extracted deadline: {deadline.strftime('%Y-%m-%d')}")
        else:
            print("   ❌ No deadline found")
            
    else:
        print("❌ Failed to fetch webpage content")

if __name__ == "__main__":
    debug_webpage_content()
