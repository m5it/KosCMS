#!/usr/bin/env python3
"""
Test file for ReplaceLine at end.
"""

def calculate(x, y):
    """Calculate sum."""
    return x + y

def main():
    """Entry point."""
    result = calculate(10, 20)
    print(f"Result: {result}")
    return 0

if __name__ == "__main__":
    # MODIFIED: Added final message
    print("Goodbye!")
    sys.exit(main())