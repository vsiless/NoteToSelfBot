#!/usr/bin/env python3
"""
Test regex patterns directly.
"""

import re

def test_deadline_patterns():
    """Test deadline extraction patterns."""
    
    # The actual text from the Cohere page
    test_text = "apply by august 29th"
    
    print(f"🧪 Testing deadline patterns with: '{test_text}'")
    print("=" * 50)
    
    # Test the new pattern we're using
    pattern = r'apply\s+by\s+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\s+\d{2,4})'
    
    print(f"Pattern: {pattern}")
    print()
    
    match = re.search(pattern, test_text)
    if match:
        print(f"✅ Match found: {match.group(1)}")
    else:
        print("❌ No match found")
        print()
        
        # Let's try a simpler pattern
        print("🔍 Trying simpler patterns...")
        
        # Pattern 1: Just match the month and day
        pattern1 = r'apply\s+by\s+(\w+\s+\d+)'
        match1 = re.search(pattern1, test_text)
        if match1:
            print(f"✅ Pattern 1 match: {match1.group(1)}")
        else:
            print("❌ Pattern 1 no match")
        
        # Pattern 2: Match any text after "apply by"
        pattern2 = r'apply\s+by\s+([^,\s]+(?:\s+[^,\s]+)*)'
        match2 = re.search(pattern2, test_text)
        if match2:
            print(f"✅ Pattern 2 match: {match2.group(1)}")
        else:
            print("❌ Pattern 2 no match")

if __name__ == "__main__":
    test_deadline_patterns()
