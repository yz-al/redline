#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.models import Document
from datetime import datetime, timezone

def test_append_functionality():
    """Test the append functionality to see what's happening"""
    
    # Create a test document
    doc = Document(
        id="test-123",
        title="Test Document",
        text="This is the original text.",
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    print("Original document:")
    print(f"Text: '{doc.text}'")
    print(f"Length: {len(doc.text)}")
    print()
    
    # Test append
    text_to_append = " This is appended text."
    print(f"Text to append: '{text_to_append}'")
    print()
    
    # Simulate the append operation
    doc.text += text_to_append
    doc.version += 1
    doc.updated_at = datetime.now(timezone.utc)
    
    print("After append:")
    print(f"Text: '{doc.text}'")
    print(f"Length: {len(doc.text)}")
    print()
    
    # Test serialization/deserialization
    doc_dict = doc.to_dict()
    doc_restored = Document.from_dict(doc_dict)
    
    print("After serialization/deserialization:")
    print(f"Text: '{doc_restored.text}'")
    print(f"Length: {len(doc_restored.text)}")
    print()
    
    # Test multiple appends
    print("Testing multiple appends:")
    original_text = "Original content."
    doc2 = Document(
        id="test-456",
        title="Test Document 2",
        text=original_text,
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    print(f"Initial: '{doc2.text}'")
    
    # First append
    doc2.text += " First append."
    print(f"After first append: '{doc2.text}'")
    
    # Second append
    doc2.text += " Second append."
    print(f"After second append: '{doc2.text}'")
    
    # Third append
    doc2.text += " Third append."
    print(f"After third append: '{doc2.text}'")

if __name__ == "__main__":
    test_append_functionality() 