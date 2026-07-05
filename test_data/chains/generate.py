#!/usr/bin/env python3
# Script to generate output and create a file

content = """Original Line 1
Original Line 2
Original Line 3"""

with open("test_data/chains/generated.txt", "w") as f:
    f.write(content)

print("File created successfully")