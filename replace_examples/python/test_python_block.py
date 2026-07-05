#!/usr/bin/env python3
"""
Test file for ReplaceLine multi-line block replacement.
"""

def old_function_to_replace():
    """
    This function will be replaced entirely.
    It has multiple lines.
    """
    x = 1
    y = 2
    z = 3
    return x + y + z

class OldClass:
    """
    This class will be replaced.
    Multiple lines here.
    """
    def __init__(self):
        self.name = "old"
    
    def greet(self):
        return f"Hello from {self.name}"

@decorator
def another_function():
    pass

if __name__ == "__main__":
    print("Before replacement")