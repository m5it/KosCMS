#!/usr/bin/env python3
"""Debug workflow storage"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webcms.workflow.kosdb_storage import KosDBWorkflowStorage

# Create mock KosDB
class MockKosDB:
    def __init__(self):
        self._tables = set()
        self._data = {}
    
    def list_tables(self):
        return list(self._tables)
    
    def execute(self, sql):
        print(f"EXECUTE: {sql[:60]}...")
        if "CREATE TABLE" in sql:
            table = sql.split("CREATE TABLE")[1].split("(")[0].strip()
            self._tables.add(table)
            self._data[table] = []
        elif "INSERT INTO" in sql:
            table = sql.split("INSERT INTO")[1].split("(")[0].strip()
            if table not in self._data:
                self._data[table] = []
            # Parse values
            values_part = sql.split("VALUES")[1].strip().strip("()")
            values = [v.strip().strip("'\"") for v in values_part.split(",")]
            cols_part = sql.split("(")[1].split(")")[0]
            columns = [c.strip() for c in cols_part.split(",")]
            row = {}
            for i, col in enumerate(columns):
                if i < len(values):
                    row[col] = values[i]
            self._data[table].append(row)
            print(f"  Inserted into {table}: {row.get('workflow_id', row.get('instance_id', 'unknown'))}")
        return {"success": True}
    
    def query(self, sql):
        print(f"QUERY: {sql[:60]}...")
        table = None
        if "FROM" in sql:
            parts = sql.split("FROM")
            if len(parts) > 1:
                table = parts[1].split()[0].strip().strip("'")
        
        if table and table in self._data:
            rows = self._data[table]
            if "WHERE" in sql:
                where_part = sql.split("WHERE")[1].strip()
                if "=" in where_part:
                    parts = where_part.split("=")
                    if len(parts) >= 2:
                        col = parts[0].strip()
                        val = parts[1].strip().strip("'\"")
                        rows = [r for r in rows if r.get(col) == val]
            print(f"  Found {len(rows)} rows in {table}")
            return {"rows": rows}
        print(f"  No data for table {table}")
        return {"rows": []}

db = MockKosDB()
storage = KosDBWorkflowStorage(db)

print(f"\n_is_kosdb: {storage._is_kosdb()}")
print(f"Tables after init: {db.list_tables()}")

# Create a test definition
from webcms.workflow.models import WorkflowDefinition, WorkflowState, WorkflowTransition

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

print(f"\nSaving definition...")
storage.save_definition(wf)

print(f"\nData in DB:")
print(f"  Tables: {db.list_tables()}")
if 'workflow_definitions' in db._data:
    print(f"  Definitions: {len(db._data['workflow_definitions'])}")
    for row in db._data['workflow_definitions']:
        print(f"    - {row}")

print(f"\nListing definitions...")
definitions = storage.list_definitions()
print(f"Found {len(definitions)} definitions")
for d in definitions:
    print(f"  - {d.workflow_id}: {d.name}")

print(f"\nGetting definition by ID...")
got = storage.get_definition("test-workflow")
if got:
    print(f"Found: {got.workflow_id} - {got.name}")
    print(f"States: {len(got.states)}")
    print(f"Transitions: {len(got.transitions)}")
else:
    print("Not found!")
