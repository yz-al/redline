import unittest
from core.text_replace import TextReplacer

class TestTextReplacer(unittest.TestCase):
    def setUp(self):
        self.replacer = TextReplacer()
        self.sample_text = "This is a test document with test content for testing purposes."

    def test_replace_by_range(self):
        """Test range-based text replacement"""
        changes = [{
            'operation': 'replace',
            'range': {'start': 10, 'end': 14},
            'text': 'was'
        }]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This is was test document with test content for testing purposes."
        self.assertEqual(result, expected)

    def test_replace_by_target_first_occurrence(self):
        """Test target-based replacement of first occurrence"""
        changes = [{
            'operation': 'replace',
            'target': {'text': 'test', 'occurrence': 1},
            'replacement': 'sample'
        }]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This is a sample document with test content for testing purposes."
        self.assertEqual(result, expected)

    def test_replace_by_target_second_occurrence(self):
        """Test target-based replacement of second occurrence"""
        changes = [{
            'operation': 'replace',
            'target': {'text': 'test', 'occurrence': 2},
            'replacement': 'sample'
        }]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This is a test document with sample content for testing purposes."
        self.assertEqual(result, expected)

    def test_replace_by_target_third_occurrence(self):
        """Test target-based replacement of third occurrence"""
        changes = [{
            'operation': 'replace',
            'target': {'text': 'test', 'occurrence': 3},
            'replacement': 'sample'
        }]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This is a test document with test content for sampleing purposes."
        self.assertEqual(result, expected)

    def test_multiple_changes(self):
        """Test applying multiple changes in sequence"""
        changes = [
            {
                'operation': 'replace',
                'range': {'start': 0, 'end': 4},
                'text': 'That'
            },
            {
                'operation': 'replace',
                'target': {'text': 'test', 'occurrence': 1},
                'replacement': 'sample'
            }
        ]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "That is a sample document with test content for testing purposes."
        self.assertEqual(result, expected)

    def test_empty_replacement(self):
        """Test replacing text with empty string (deletion)"""
        changes = [{
            'operation': 'replace',
            'range': {'start': 10, 'end': 15},
            'text': ''
        }]
        
        result = self.replacer.apply_changes(self.sample_text, changes)
        expected = "This is a  document with test content for testing purposes."
        self.assertEqual(result, expected)

    def test_large_text_performance(self):
        """Test performance with large text"""
        large_text = "test " * 10000  # 50,000 characters
        changes = [{
            'operation': 'replace',
            'target': {'text': 'test', 'occurrence': 5000},
            'replacement': 'sample'
        }]
        
        import time
        start_time = time.time()
        result = self.replacer.apply_changes(large_text, changes)
        end_time = time.time()
        
        # Should complete within 1 second
        self.assertLess(end_time - start_time, 1.0)
        
        # Verify the change was applied correctly
        occurrences = result.count('sample')
        self.assertEqual(occurrences, 1)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test replacement at very beginning
        changes = [{
            'operation': 'replace',
            'range': {'start': 0, 'end': 4},
            'text': 'That'
        }]
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertTrue(result.startswith('That'))

        # Test replacement at very end
        changes = [{
            'operation': 'replace',
            'range': {'start': len(self.sample_text) - 9, 'end': len(self.sample_text)},
            'text': 'purposes!'
        }]
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertTrue(result.endswith('purposes!'))

    def test_invalid_range(self):
        """Test handling of invalid range values"""
        changes = [{
            'operation': 'replace',
            'range': {'start': 100, 'end': 200},  # Out of bounds
            'text': 'test'
        }]
        
        # Should handle gracefully without crashing
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertEqual(result, self.sample_text)

    def test_target_not_found(self):
        """Test handling when target text is not found"""
        changes = [{
            'operation': 'replace',
            'target': {'text': 'nonexistent', 'occurrence': 1},
            'replacement': 'test'
        }]
        
        # Should return original text unchanged
        result = self.replacer.apply_changes(self.sample_text, changes)
        self.assertEqual(result, self.sample_text)

    def test_complex_scenario(self):
        """Test a complex scenario with multiple overlapping changes"""
        text = "The quick brown fox jumps over the lazy dog. The quick brown fox is fast."
        changes = [
            {
                'operation': 'replace',
                'range': {'start': 0, 'end': 3},
                'text': 'A'
            },
            {
                'operation': 'replace',
                'target': {'text': 'quick', 'occurrence': 1},
                'replacement': 'swift'
            },
            {
                'operation': 'replace',
                'target': {'text': 'fox', 'occurrence': 2},
                'replacement': 'cat'
            }
        ]
        
        result = self.replacer.apply_changes(text, changes)
        expected = "A swift brown fox jumps over the lazy dog. The quick brown cat is fast."
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main() 