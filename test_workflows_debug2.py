#!/usr/bin/env python3
"""Debug SQL parsing"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test SQL parsing
sql = """INSERT INTO workflow_definitions 
                    (workflow_id, name, content_types, states, transitions, is_default, created_at)
                    VALUES (
                        'test-workflow',
                        'Test Workflow',
                        '[\"post\"]',
                        '[{\"state_id\": \"draft\", \"name\": \"Draft\", \"label\": \"Draft\", \"is_initial\": true, \"is_final\": false, \"requires_approval\": false, \"color\": \"#6c757d\"}, {\"state_id\": \"published\", \"name\": \"Published\", \"label\": \"Published\", \"is_initial\": false, \"is_final\": true, \"requires_approval\": false, \"color\": \"#0d6efd\"}]',
                        '[{\"transition_id\": \"publish\", \"from_state\": \"draft\", \"to_state\": \"published\", \"name\": \"Publish\", \"required_role\": null, \"requires_comment\": false}]',
                        '1',
                        '2025-01-22T10:00:00'
                    )"""

print("Original SQL:")
print(sql[:200])
print("...")

# Extract table name
table = sql.split("TABLE")[1].split("(")[0].strip()
print(f"\nTable: '{table}'")

# Extract columns
cols_start = sql.find("(") + 1
cols_end = sql.find(")", cols_start)
cols_str = sql[cols_start:cols_end]
cols = [c.strip() for c in cols_str.split(",")]
print(f"Columns ({len(cols)}): {cols}")

# Extract values
values_idx = sql.upper().find("VALUES")
print(f"\nVALUES index: {values_idx}")

vals_start = sql.find("(", values_idx) + 1
vals_end = sql.rfind(")")
vals_str = sql[vals_start:vals_end]
print(f"Values string length: {len(vals_str)}")
print(f"Values string (first 200 chars): {vals_str[:200]}")

# Parse values properly
val_parts = []
current = ""
in_quote = False
quote_char = None

for char in vals_str:
    if char in "'\"" and not in_quote:
        in_quote = True
        quote_char = char
        current += char
    elif char == quote_char and in_quote:
        in_quote = False
        quote_char = None
        current += char
    elif char == "," and not in_quote:
        val_parts.append(current.strip())
        current = ""
    else:
        current += char

if current.strip():
    val_parts.append(current.strip())

print(f"\nParsed values ({len(val_parts)}):")
for i, v in enumerate(val_parts):
    print(f"  {i}: {v[:50]}...")

print(f"\nMatching columns to values:")
row = {}
for i, col in enumerate(cols):
    if i < len(val_parts):
        val = val_parts[i].strip().strip("'\"")
        row[col] = val
        print(f"  {col} = {val[:50]}...")

print(f"\nFinal row keys: {list(row.keys())}")
