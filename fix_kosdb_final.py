from pathlib import Path

p = Path("webcms/database/kosdb_client.py")
content = p.read_text()

# Find the first transaction method's finally block
first_transaction_end = content.find("logger.debug(\"Transaction complete, connection released to pool\")")
if first_transaction_end == -1:
    print("First transaction not found")
    exit(1)

# Find where the second transaction starts (look for @contextmanager after first one)
second_cm_pos = content.find("@contextmanager", first_transaction_end + 50)
if second_cm_pos == -1:
    print("No duplicate found")
    exit(0)

# Find where the class ends (the last methods after second transaction)
# We need to find what comes after the duplicate

# The structure should be:
# - first transaction ends around line 565
# - duplicate starts at line 568 with @contextmanager
# - duplicate ends before other methods like close(), __enter__, __exit__

# Let's find what methods exist after the duplicate
# Look for "def close(self):" after second_cm_pos
close_pos = content.find("    def close(self):", second_cm_pos)
if close_pos == -1:
    print("Could not find closing methods")
    exit(1)

# Now extract: first part + closing methods
first_part = content[:second_cm_pos].rstrip() + "\n\n\n"

# Extract closing methods (from close_pos to end)
closing_methods = content[close_pos:]

# Combine
new_content = first_part + closing_methods

p.write_text(new_content)
print("Fixed - removed duplicate transaction method")
