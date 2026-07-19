from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines(keepends=True)

# Find where transaction method ends (around line 565)
# and where the duplicate close/__enter__/__exit__ starts

# First, find the transaction method
trans_start = None
for i, line in enumerate(lines):
    if "def transaction(self):" in line:
        trans_start = i
        break

print(f"transaction starts at line {trans_start+1}")

# Find end of transaction (finally block)
trans_end = None
for i in range(trans_start, len(lines)):
    if i > trans_start + 50:  # Look for end after reasonable length
        # Check for class-level method definition (4 spaces indent)
        if lines[i].startswith("    def ") and not lines[i].startswith("        "):
            trans_end = i
            break
        # Or check for end of file markers
        if lines[i].strip() and not lines[i].startswith(" ") and not lines[i].startswith("\n"):
            trans_end = i
            break

print(f"transaction ends around line {trans_end+1}")

# Now find where KosDBClient class ends
# Look for the second set of close/__enter__/__exit__
# These should be right after transaction

# The file should end with __exit__, anything after is duplicate
# Find last __exit__
last_exit = None
for i in range(len(lines)-1, -1, -1):
    if "def __exit__(self, *args):" in lines[i]:
        last_exit = i
        break

print(f"Last __exit__ at line {last_exit+1}")

# Check if there's anything meaningful after last_exit
# If the file properly ends there, we should only have blank lines or nothing
if last_exit:
    remaining = lines[last_exit+1:]
    non_empty = [l for l in remaining if l.strip()]
    print(f"Non-empty lines after last __exit__: {len(non_empty)}")
    for i, line in enumerate(remaining):
        if line.strip():
            print(f"  Line {last_exit+2+i}: {line[:60]}")

# The fix: keep only up to and including the last __exit__ method
# But we need to find which __exit__ is the real one (part of KosDBClient)

# Actually, let's look at the structure - the first __exit__ is at line 482
# The second should be removed

first_exit = None
second_exit = None
for i, line in enumerate(lines):
    if "def __exit__(self, *args):" in line:
        if first_exit is None:
            first_exit = i
        else:
            second_exit = i
            break

print(f"First __exit__ at {first_exit+1}, second at {second_exit+1 if second_exit else 'None'}")

if second_exit:
    # Remove from second_exit back to the close before it
    # Find where the duplicate section starts
    dup_start = second_exit
    for i in range(second_exit, -1, -1):
        if lines[i].strip() == "" and i < second_exit - 5:
            # Look for close method before
            if "def close(self):" in lines[i+1]:
                dup_start = i + 1
                break
    
    print(f"Removing duplicate section from line {dup_start+1} to end")
    new_lines = lines[:dup_start]
    p.write_text("".join(new_lines))
    print("Done")
