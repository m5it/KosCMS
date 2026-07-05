#!/usr/bin/env python3
"""
Test file for ReplaceLine with special Python characters.
"""

@staticmethod
@decorator_with_args(arg1="value")
def decorated_function():
    """Function with decorators."""
    # f-string with expressions
    name = "World"
    message = f"Hello, {name}! Value: {42 + 10}"
    
    message = f"MODIFIED: Hello, {name}! Value: {42 + 10} Emoji: 🎉"
    emoji = "🎉"
    chinese = "你好世界"
    math = "∑ ∏ √"
    
    # Raw string and bytes
    raw_path = r"C:\Users\name\file.txt"
    data = b"\x00\x01\x02\xff"
    
    return message

# List comprehension with walrus operator (Python 3.8+)
numbers = [1, 2, 3, 4, 5]
squared = [(x := n ** 2) for n in numbers if x > 5]

if __name__ == "__main__":
    result = decorated_function()
    print(result)