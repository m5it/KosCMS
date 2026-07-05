#!/usr/bin/env python3
"""
Test file for ReplaceLine in middle with indentation.
"""

def outer_function():
    """Outer function with nested blocks."""
    x = 10
    
    def inner_function():
        """Inner nested function."""
        y = 25  # MODIFIED: Changed from 20
        return x + y
    
    result = inner_function()
    return result

class MyClass:
    """A sample class."""
    
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        """Return the value."""
        return self.value

if __name__ == "__main__":
    obj = MyClass()
    print(obj.get_value())