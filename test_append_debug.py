#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.models import Document
from datetime import datetime, timezone

def test_append_debug():
    """Debug the append functionality to see exact behavior"""
    
    # Test case 1: Original text without trailing space
    print("=== Test Case 1: Original text without trailing space ===")
    doc1 = Document(
        id="test-1",
        title="Test Document 1",
        text="starter text",  # No trailing space
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    print(f"Original text: '{doc1.text}' (length: {len(doc1.text)})")
    print(f"Original text bytes: {doc1.text.encode('utf-8')}")
    
    # Append text without leading space
    text_to_append = "newer text"
    print(f"Text to append: '{text_to_append}' (length: {len(text_to_append)})")
    print(f"Text to append bytes: {text_to_append.encode('utf-8')}")
    
    # Simulate append
    doc1.text += text_to_append
    print(f"After append: '{doc1.text}' (length: {len(doc1.text)})")
    print(f"After append bytes: {doc1.text.encode('utf-8')}")
    print()
    
    # Test case 2: Original text with trailing space
    print("=== Test Case 2: Original text with trailing space ===")
    doc2 = Document(
        id="test-2",
        title="Test Document 2",
        text="starter text ",  # With trailing space
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    print(f"Original text: '{doc2.text}' (length: {len(doc2.text)})")
    print(f"Original text bytes: {doc2.text.encode('utf-8')}")
    
    # Append text without leading space
    text_to_append = "newer text"
    print(f"Text to append: '{text_to_append}' (length: {len(text_to_append)})")
    print(f"Text to append bytes: {text_to_append.encode('utf-8')}")
    
    # Simulate append
    doc2.text += text_to_append
    print(f"After append: '{doc2.text}' (length: {len(doc2.text)})")
    print(f"After append bytes: {doc2.text.encode('utf-8')}")
    print()
    
    # Test case 3: Original text with trailing space, append with leading space
    print("=== Test Case 3: Original text with trailing space, append with leading space ===")
    doc3 = Document(
        id="test-3",
        title="Test Document 3",
        text="starter text ",  # With trailing space
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    print(f"Original text: '{doc3.text}' (length: {len(doc3.text)})")
    print(f"Original text bytes: {doc3.text.encode('utf-8')}")
    
    # Append text with leading space
    text_to_append = " newer text"
    print(f"Text to append: '{text_to_append}' (length: {len(text_to_append)})")
    print(f"Text to append bytes: {text_to_append.encode('utf-8')}")
    
    # Simulate append
    doc3.text += text_to_append
    print(f"After append: '{doc3.text}' (length: {len(doc3.text)})")
    print(f"After append bytes: {doc3.text.encode('utf-8')}")
    print()
    
    # Test case 4: Check for any hidden characters
    print("=== Test Case 4: Check for hidden characters ===")
    test_text = "starter textender text"
    print(f"Test text: '{test_text}' (length: {len(test_text)})")
    print(f"Test text bytes: {test_text.encode('utf-8')}")
    print(f"Character by character:")
    for i, char in enumerate(test_text):
        print(f"  {i}: '{char}' (ord: {ord(char)})")

if __name__ == "__main__":
    test_append_debug() 