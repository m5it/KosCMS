from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
lines = p.read_text().splitlines(keepends=True)

# Find the duplicate transaction method (starts at line 568)
# and remove everything from there to the class end
# Keep lines 1-567 (first transaction ends at 565, plus blank line)
# and then keep the class methods after the duplicate

# Actually, let's be more careful - find where the second transaction starts
start_remove = None
for i, line in enumerate(lines):
    if i > 480 and "@contextmanager" in line:
        # Check if next line has def transaction
        if i+1 < len(lines) and "def transaction(self):" in lines[i+1]:
            start_remove = i
            break

if start_remove:
    print(f"Found duplicate at line {start_remove+1}")
    # Keep everything up to start_remove
    new_lines = lines[:start_remove]
    
    # But we need to keep the class closing - let's check what's after
    # The duplicate goes from ~568 to ~650, then we have other methods
    
    # Actually, let's look for what comes after the duplicate
    # Find where the transaction ends (finally block)
    end_remove = start_remove
    brace_count = 0
    in_transaction = False
    for i in range(start_remove, len(lines)):
        line = lines[i]
        if "def transaction(self):" in line:
            in_transaction = True
        if in_transaction:
            # Count indentation to find end
            if line.strip() and not line.startswith("    ") and not line.startswith("\t"):
                if not line.strip().startswith("@"):
                    end_remove = i
                    break
            # Or look for next method definition at class level
            if i > start_remove + 10 and line.startswith("    def ") and not line.startswith("        "):
                end_remove = i
                break
    
    print(f"Duplicate ends around line {end_remove+1}")
    
    # Keep lines before start_remove and from end_remove onwards
    # But we need to check what's at end_remove
    for i in range(end_remove-5, min(end_remove+10, len(lines))):
        print(f"{i+1}: {repr(lines[i][:80])}")
    
    # Actually, let's just keep 1-567 and see what's there
    new_content = "".join(lines[:568])
    p.write_text(new_content)
    print("Removed duplicate, kept first 568 lines")
else:
    print("No duplicate found")
