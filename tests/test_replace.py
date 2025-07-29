import unittest
from core.text_replace import TextReplacer

class TestTextReplacer(unittest.TestCase):
    
    def setUp(self):
        self.replacer = TextReplacer()
        self.sample_text = "This Agreement is made between Employee and Company. Employee agrees to work for Company."
    
    def test_replace_by_target_first_occurrence(self):
        """Test replacing first occurrence of target text"""
        changes = [{
            "operation": "replace",
            "target": {
                "text": "Employee",
                "occurrence": 1
            },
            "replacement": "Contractor"
        }]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This Agreement is made between Contractor and Company. Employee agrees to work for Company."
        self.assertEqual(result, expected)
    
    def test_replace_by_target_second_occurrence(self):
        """Test replacing second occurrence of target text"""
        changes = [{
            "operation": "replace",
            "target": {
                "text": "Employee",
                "occurrence": 2
            },
            "replacement": "Contractor"
        }]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This Agreement is made between Employee and Company. Contractor agrees to work for Company."
        self.assertEqual(result, expected)
    
    def test_replace_by_range(self):
        """Test replacing text by range"""
        changes = [{
            "operation": "replace",
            "range": {
                "start": 31,
                "end": 39
            },
            "replacement": "Contractor"
        }]
    
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This Agreement is made between Contractor and Company. Employee agrees to work for Company."
        self.assertEqual(result, expected)
    
    def test_multiple_changes(self):
        """Test applying multiple changes"""
        changes = [
            {
                "operation": "replace",
                "target": {
                    "text": "Employee",
                    "occurrence": 1
                },
                "replacement": "Contractor"
            },
            {
                "operation": "replace",
                "target": {
                    "text": "Employee",
                    "occurrence": 1  # This will now be the first occurrence in the modified text
                },
                "replacement": "Worker"
            }
        ]
    
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This Agreement is made between Worker and Company. Contractor agrees to work for Company."
        self.assertEqual(result, expected)
    
    def test_overlapping_changes(self):
        """Test that overlapping changes are handled correctly"""
        changes = [
            {
                "operation": "replace",
                "range": {
                    "start": 20,
                    "end": 40
                },
                "replacement": "New Text"
            },
            {
                "operation": "replace",
                "range": {
                    "start": 25,
                    "end": 35
                },
                "replacement": "Overlapping"
            }
        ]
        
        # Should handle overlapping changes gracefully
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertIsInstance(result, str)
    
    def test_target_not_found(self):
        """Test error handling when target text is not found"""
        changes = [{
            "operation": "replace",
            "target": {
                "text": "Nonexistent",
                "occurrence": 1
            },
            "replacement": "Something"
        }]
        
        # Should return original text unchanged when target is not found
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertEqual(result, self.sample_text)
    
    def test_invalid_occurrence(self):
        """Test error handling for invalid occurrence number"""
        changes = [{
            "operation": "replace",
            "target": {
                "text": "Employee",
                "occurrence": 0
            },
            "replacement": "Contractor"
        }]
        
        # Should return original text unchanged when occurrence is invalid
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertEqual(result, self.sample_text)
    
    def test_invalid_range(self):
        """Test error handling for invalid range"""
        changes = [{
            "operation": "replace",
            "range": {
                "start": 100,
                "end": 200
            },
            "replacement": "Something"
        }]
        
        # Should return original text unchanged when range is invalid
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertEqual(result, self.sample_text)
    
    def test_empty_changes(self):
        """Test handling of empty changes list"""
        result = self.replacer.apply_changes(self.sample_text, [])
        self.assertEqual(result, self.sample_text)
    
    def test_large_document(self):
        """Test with a large document"""
        large_text = "Lorem ipsum " * 1000
        changes = [{
            "operation": "replace",
            "target": {
                "text": "ipsum",
                "occurrence": 500
            },
            "replacement": "REPLACED"
        }]
        
        result = self.replacer.apply_changes(large_text, changes)
        self.assertIn("REPLACED", result)
        
        # Count occurrences before the replacement
        replaced_index = result.find("REPLACED")
        text_before = result[:replaced_index]
        ipsum_count_before = text_before.count("ipsum")
        
        # Should have exactly 499 "ipsum" occurrences before the replacement
        self.assertEqual(ipsum_count_before, 499)
        
        # Should have exactly 999 "ipsum" occurrences after the replacement (1000 total - 1 replaced)
        ipsum_count_after = result.count("ipsum")
        self.assertEqual(ipsum_count_after, 999)

if __name__ == '__main__':
    unittest.main() 