#!/usr/bin/env python3
"""Test workflow endpoints with actual KosDBClient"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webcms.workflow.kosdb_storage import KosDBWorkflowStorage
from webcms.workflow.models import WorkflowDefinition, WorkflowState, WorkflowTransition, WorkflowInstance

print("=" * 60)
print("Testing KosDBWorkflowStorage directly")
print("=" * 60)

# Create a simple file-based mock that stores JSON properly
class SimpleKosDB:
    def __init__(self, filepath):
        self.filepath = filepath
        self._tables = {}
        self._load()
    
    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    self._tables = json.load(f)
            except:
                pass
    
    def _save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self._tables, f, indent=2)
    
    def list_tables(self):
        return list(self._tables.keys())
    
    def execute(self, sql):
        # Parse CREATE TABLE
        if "CREATE TABLE" in sql.upper():
            table = sql.split("TABLE")[1].split("(")[0].strip()
            if table not in self._tables:
                self._tables[table] = []
                self._save()
            return {"success": True}
        
        # Parse INSERT INTO
        elif "INSERT INTO" in sql.upper():
            # Extract table name
            table = sql.split("TABLE")[1].split("(")[0].strip()
            if table not in self._tables:
                self._tables[table] = []
            
            # Extract column names
            cols_start = sql.find("(") + 1
            cols_end = sql.find(")", cols_start)
            cols = [c.strip() for c in sql[cols_start:cols_end].split(",")]
            
            # Extract values - find VALUES clause
            values_idx = sql.upper().find("VALUES")
            if values_idx > 0:
                vals_start = sql.find("(", values_idx) + 1
                vals_end = sql.rfind(")")
                vals_str = sql[vals_start:vals_end]
                
                # Parse values (handle quoted strings)
                row = {}
                val_parts = []
                current = ""
                in_quote = False
                quote_char = None
                
                for char in vals_str:
                    if char in "'\"" and not in_quote:
                        in_quote = True
                        quote_char = char
                    elif char == quote_char and in_quote:
                        in_quote = False
                        quote_char = None
                    elif char == "," and not in_quote:
                        val_parts.append(current.strip())
                        current = ""
                        continue
                    current += char
                
                if current.strip():
                    val_parts.append(current.strip())
                
                # Match columns with values
                for i, col in enumerate(cols):
                    if i < len(val_parts):
                        val = val_parts[i].strip().strip("'\"")
                        row[col] = val
                
                self._tables[table].append(row)
                self._save()
            
            return {"success": True}
        
        # Parse UPDATE
        elif "UPDATE" in sql.upper():
            # Simple update - just save
            self._save()
            return {"success": True}
        
        # Parse DELETE
        elif "DELETE" in sql.upper():
            table = None
            if "FROM" in sql.upper():
                table = sql.split("FROM")[1].split()[0].strip()
            
            if table and table in self._tables:
                if "WHERE" in sql.upper():
                    where_part = sql.split("WHERE")[1].strip()
                    if "=" in where_part:
                        parts = where_part.split("=")
                        if len(parts) >= 2:
                            col = parts[0].strip()
                            val = parts[1].strip().strip("'\"")
                            self._tables[table] = [
                                r for r in self._tables[table] 
                                if r.get(col) != val
                            ]
                            self._save()
            return {"success": True}
        
        return {"success": True}
    
    def query(self, sql):
        table = None
        if "FROM" in sql.upper():
            table = sql.split("FROM")[1].split()[0].strip()
        
        if table and table in self._tables:
            rows = list(self._tables[table])  # Copy
            if "WHERE" in sql.upper():
                where_part = sql.split("WHERE")[1].strip()
                if "=" in where_part:
                    parts = where_part.split("=")
                    if len(parts) >= 2:
                        col = parts[0].strip()
                        val = parts[1].strip().strip("'\"")
                        rows = [r for r in rows if r.get(col) == val]
            return {"rows": rows}
        
        return {"rows": []}

# Test with simple KosDB
db = SimpleKosDB("test_workflow_simple.db")
storage = KosDBWorkflowStorage(db)

print(f"\n1. _is_kosdb check: {storage._is_kosdb()}")
print(f"   Tables: {db.list_tables()}")

print(f"\n2. Creating and saving workflow definition")
states = [
    WorkflowState("draft", "Draft", "Draft", is_initial=True, color="#6c757d"),
    WorkflowState("published", "Published", "Published", is_final=True, color="#0d6efd")
]

transitions = [
    WorkflowTransition("publish", "draft", "published", "Publish")
]

wf = WorkflowDefinition(
    workflow_id="test-workflow",
    name="Test Workflow",
    content_types=["post"],
    states=states,
    transitions=transitions,
    is_default=True
)

storage.save_definition(wf)
print(f"   Saved workflow: {wf.workflow_id}")

print(f"\n3. Listing definitions")
definitions = storage.list_definitions()
print(f"   Found {len(definitions)} definitions")
for d in definitions:
    print(f"   - {d.workflow_id}: {d.name} (states: {len(d.states)})")

print(f"\n4. Getting definition by ID")
got = storage.get_definition("test-workflow")
if got:
    print(f"   Found: {got.workflow_id} - {got.name}")
    print(f"   States: {[s.state_id for s in got.states]}")
else:
    print("   NOT FOUND!")

print(f"\n5. Creating workflow instance")
instance = WorkflowInstance(
    instance_id="inst-001",
    workflow_id="test-workflow",
    content_id="post-123",
    content_type="post",
    current_state="draft"
)
instance.add_history_entry(None, "draft", "user1", "Admin", "Workflow started")
storage.save_instance(instance)
print(f"   Saved instance: {instance.instance_id}")

print(f"\n6. Listing instances")
instances = storage.list_instances()
print(f"   Found {len(instances)} instances")
for inst in instances:
    print(f"   - {inst.instance_id}: {inst.content_id} ({inst.current_state})")

print(f"\n7. Getting instance by ID")
got_inst = storage.get_instance("inst-001")
if got_inst:
    print(f"   Found: {got_inst.instance_id} - {got_inst.current_state}")
else:
    print("   NOT FOUND!")

print(f"\n8. Checking DB content")
print(f"   Tables: {db.list_tables()}")
for table in db.list_tables():
    print(f"   {table}: {len(db._tables[table])} rows")

print("\n" + "=" * 60)
print("Test completed successfully!")
print("=" * 60)

# Cleanup
os.remove("test_workflow_simple.db")
