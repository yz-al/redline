from typing import List, Dict, Any
import re

class TextReplacer:
    """Safely replaces substrings by text + occurrence, range, or other criteria"""
    
    def apply_changes(self, text: str, changes: List[Dict[str, Any]]) -> str:
        """
        Apply multiple changes to text
        
        Args:
            text: Original text
            changes: List of change operations
            
        Returns:
            Updated text with all changes applied
        """
        # Sort changes by position to apply them in order
        # This prevents overlapping changes from interfering with each other
        sorted_changes = self._sort_changes_by_position(text, changes)
        
        # Apply changes in reverse order to maintain correct positions
        result = text
        for change in reversed(sorted_changes):
            result = self._apply_single_change(result, change)
        
        return result
    
    def _sort_changes_by_position(self, text: str, changes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort changes by their position in the text"""
        changes_with_positions = []
        
        for change in changes:
            if change['operation'] == 'replace':
                if 'target' in change:
                    # Target-based replacement
                    position = self._find_target_position(text, change['target'])
                    changes_with_positions.append((position, change))
                elif 'range' in change:
                    # Range-based replacement
                    position = change['range']['start']
                    changes_with_positions.append((position, change))
        
        # Sort by position (ascending)
        changes_with_positions.sort(key=lambda x: x[0])
        return [change for _, change in changes_with_positions]
    
    def _find_target_position(self, text: str, target: Dict[str, Any]) -> int:
        """Find the position of a target text with specified occurrence"""
        target_text = target['text']
        occurrence = target.get('occurrence', 1)
        
        if occurrence < 1:
            raise ValueError(f"Invalid occurrence: {occurrence}")
        
        start = 0
        for i in range(occurrence):
            pos = text.find(target_text, start)
            if pos == -1:
                raise ValueError(f"Target text '{target_text}' not found at occurrence {occurrence}")
            start = pos + 1
        
        return pos
    
    def _apply_single_change(self, text: str, change: Dict[str, Any]) -> str:
        """Apply a single change operation"""
        if change['operation'] == 'replace':
            if 'target' in change:
                return self._replace_by_target(text, change)
            elif 'range' in change:
                return self._replace_by_range(text, change)
            else:
                raise ValueError("Invalid replace operation: missing target or range")
        else:
            raise ValueError(f"Unsupported operation: {change['operation']}")
    
    def _replace_by_target(self, text: str, change: Dict[str, Any]) -> str:
        """Replace text by target specification"""
        target = change['target']
        replacement = change.get('replacement', change.get('text', ''))
        
        target_text = target['text']
        occurrence = target.get('occurrence', 1)
        
        if occurrence < 1:
            raise ValueError(f"Invalid occurrence: {occurrence}")
        
        # Find the target position
        start = 0
        for i in range(occurrence):
            pos = text.find(target_text, start)
            if pos == -1:
                raise ValueError(f"Target text '{target_text}' not found at occurrence {occurrence}")
            start = pos + 1
        
        # Perform the replacement
        return text[:pos] + replacement + text[pos + len(target_text):]
    
    def _replace_by_range(self, text: str, change: Dict[str, Any]) -> str:
        """Replace text by range specification"""
        range_spec = change['range']
        replacement = change.get('text', '')
        
        start = range_spec['start']
        end = range_spec['end']
        
        if start < 0 or end > len(text) or start > end:
            raise ValueError(f"Invalid range: start={start}, end={end}, text_length={len(text)}")
        
        return text[:start] + replacement + text[end:] 