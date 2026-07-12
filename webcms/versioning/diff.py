"""
Diff viewer for comparing content versions.
"""

import difflib
from typing import Dict, Any, List


class DiffViewer:
    """Generate diffs between content versions."""
    
    @staticmethod
    def text_diff(old_text: str, new_text: str, context: int = 3) -> str:
        """Generate unified text diff."""
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        
        if old_lines and not old_lines[-1].endswith('\n'):
            old_lines[-1] += '\n'
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines[-1] += '\n'
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='previous',
            tofile='current',
            n=context
        )
        
        return ''.join(diff)
    
    @staticmethod
    def html_diff(old_text: str, new_text: str) -> str:
        """Generate HTML diff with insertions/deletions highlighted."""
        differ = difflib.HtmlDiff()
        return differ.make_table(
            old_text.splitlines(),
            new_text.splitlines(),
            fromdesc='Previous Version',
            todesc='Current Version'
        )
    
    @staticmethod
    def structured_diff(old_data: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two dictionaries field by field."""
        result = {
            "added": {},
            "removed": {},
            "modified": {},
            "unchanged": {}
        }
        
        all_keys = set(old_data.keys()) | set(new_data.keys())
        
        for key in all_keys:
            if key not in old_data:
                result["added"][key] = new_data[key]
            elif key not in new_data:
                result["removed"][key] = old_data[key]
            elif old_data[key] != new_data[key]:
                result["modified"][key] = {
                    "old": old_data[key],
                    "new": new_data[key]
                }
            else:
                result["unchanged"][key] = old_data[key]
        
        return result
    
    @staticmethod
    def word_diff(old_text: str, new_text: str) -> List[Dict[str, Any]]:
        """Generate word-level diff for rich text comparison."""
        old_words = old_text.split()
        new_words = new_text.split()
        
        sm = difflib.SequenceMatcher(None, old_words, new_words)
        result = []
        
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                result.append({
                    "type": "equal",
                    "text": ' '.join(old_words[i1:i2])
                })
            elif tag == 'delete':
                result.append({
                    "type": "delete",
                    "text": ' '.join(old_words[i1:i2])
                })
            elif tag == 'insert':
                result.append({
                    "type": "insert",
                    "text": ' '.join(new_words[j1:j2])
                })
            elif tag == 'replace':
                result.append({
                    "type": "delete",
                    "text": ' '.join(old_words[i1:i2])
                })
                result.append({
                    "type": "insert",
                    "text": ' '.join(new_words[j1:j2])
                })
        
        return result
