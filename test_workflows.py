#!/usr/bin/env python3
"""Test workflow endpoints with KosDB"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webcms.database.kosdb_client import KosDBClient, KosDBConfig
from webcms.workflow.manager import WorkflowManager

print("=" * 60)
print("Testing WorkflowManager with KosDB")
print("=" * 60)

# Create KosDB instance (use file-based fallback since server may not be running)
class MockKosDB:
    """Mock KosDB for testing without server"""
    def __init__(self, db_path):
        self.db_path = db_path
        self._data = {}
        self._tables = set()
        self._load()
    
    def _load(self):
        import json
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    self._data = json.load(f)
                self._tables = set(self._data.keys())
            except:
                pass
    
    def _save(self):
        import json
        with open(self.db_path, 'w') as f:
            json.dump(self._data, f, indent=2)
    
    def list_tables(self):
        return list(self._tables)
    
    def execute(self, sql):
        # Simple CREATE TABLE handling
        if "CREATE TABLE" in sql:
            table_name = sql.split("CREATE TABLE")[1].split("(")[0].strip()
            if table_name not in self._data:
                self._data[table_name] = []
                self._tables.add(table_name)
                self._save()
            return {"success": True}
        elif "INSERT INTO" in sql:
            # Parse simple INSERT
            table = sql.split("INSERT INTO")[1].split("(")[0].strip()
            values_part = sql.split("VALUES")[1].strip().strip("()")
            # Create row from values
            row = {}
            if table not in self._data:
                self._data[table] = []
                self._tables.add(table)
            
            # Simple value parsing
            values = [v.strip().strip("'\"") for v in values_part.split(",")]
            cols_part = sql.split("(")[1].split(")")[0]
            columns = [c.strip() for c in cols_part.split(",")]
            
            for i, col in enumerate(columns):
                if i < len(values):
                    row[col] = values[i]
            
            self._data[table].append(row)
            self._save()
            return {"success": True, "inserted": 1}
        elif "UPDATE" in sql:
            table = sql.split("UPDATE")[1].split("SET")[0].strip()
            # Simple update - not fully implemented
            self._save()
            return {"success": True, "updated": 1}
        elif "DELETE" in sql:
            table = sql.split("FROM")[1].split("WHERE")[0].strip() if "FROM" in sql else sql.split("DELETE")[1].split("WHERE")[0].strip()
            if table in self._data:
                where = sql.split("WHERE")[1].strip() if "WHERE" in sql else ""
                if "=" in where:
                    col, val = where.split("=")
                    col = col.strip()
                    val = val.strip().strip("'\"")
                    self._data[table] = [r for r in self._data[table] if r.get(col) != val]
                self._save()
            return {"success": True, "deleted": 1}
        return {"success": True}
    
    def query(self, sql):
        table = None
        if "FROM" in sql:
            parts = sql.split("FROM")
            if len(parts) > 1:
                table = parts[1].split()[0].strip()
        
        if table and table in self._data:
            rows = self._data[table]
            # Simple WHERE filtering
            if "WHERE" in sql:
                where_part = sql.split("WHERE")[1].strip()
                if "=" in where_part:
                    col, val = where_part.split("=")
                    col = col.strip()
                    val = val.strip().strip("'\"")
                    rows = [r for r in rows if r.get(col) == val]
            return {"rows": rows}
        return {"rows": []}

# Use mock for testing
db = MockKosDB("test_workflow.db")

# Create workflow manager with KosDB
wm = WorkflowManager(db=db)

print("\n1. Testing list_definitions()")
print("-" * 40)
definitions = wm.list_definitions()
print(f"Found {len(definitions)} workflow definitions")
for d in definitions:
    print(f"  - {d['id']}: {d['name']}")
    print(f"    States: {len(d['states'])}")
    print(f"    Transitions: {len(d['transitions'])}")

print("\n2. Testing create_instance()")
print("-" * 40)
try:
    instance = wm.create_instance(
        content_id="test-post-123",
        content_type="post",
        workflow_id="default-editorial"
    )
    print(f"Created instance: {instance['id']}")
    print(f"  State: {instance['state']}")
    print(f"  Content: {instance['content_id']}")
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()

print("\n3. Testing list_instances()")
print("-" * 40)
instances = wm.list_instances()
print(f"Found {len(instances)} workflow instances")
for inst in instances:
    print(f"  - {inst['id']}: {inst['content_title']} ({inst['state']})")
    print(f"    Available actions: {[a['action'] for a in inst['available_actions']]}")

if instances:
    inst_id = instances[0]['id']
    
    print(f"\n4. Testing transition() for {inst_id}")
    print("-" * 40)
    try:
        result = wm.transition(
            instance_id=inst_id,
            action="review",
            user_id="test-user",
            comment="Submitting for review"
        )
        print(f"Transition successful:")
        print(f"  From: {result['from_state']}")
        print(f"  To: {result['to_state']}")
        print(f"  Message: {result['message']}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
    
    print(f"\n5. Testing assign() for {inst_id}")
    print("-" * 40)
    try:
        result = wm.assign(
            instance_id=inst_id,
            reviewer_id="reviewer-456"
        )
        print(f"Assignment successful:")
        print(f"  ID: {result['id']}")
        print(f"  Assigned: {result['assigned']}")
        print(f"  Reviewer: {result['reviewer_id']}")
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
    
    print(f"\n6. Verifying instance after operations")
    print("-" * 40)
    instances = wm.list_instances()
    for inst in instances:
        if inst['id'] == inst_id:
            print(f"Current state: {inst['state']}")
            print(f"Reviewers: {inst['assigned_reviewers']}")
            print(f"Available actions: {[a['action'] for a in inst['available_actions']]}")

print("\n7. Checking KosDB tables")
print("-" * 40)
try:
    tables = db.list_tables()
    print(f"Tables: {tables}")
    
    if 'workflow_definitions' in tables:
        result = db.query("SELECT * FROM workflow_definitions")
        print(f"\nWorkflow definitions in DB: {len(result.get('rows', []))}")
        for row in result.get('rows', []):
            print(f"  - {row.get('workflow_id')}: {row.get('name')}")
    
    if 'workflow_instances' in tables:
        result = db.query("SELECT * FROM workflow_instances")
        print(f"\nWorkflow instances in DB: {len(result.get('rows', []))}")
        for row in result.get('rows', []):
            print(f"  - {row.get('instance_id')}: {row.get('content_title')} ({row.get('current_state')})")
except Exception as e:
    import traceback
    print(f"Error checking tables: {e}")
    traceback.print_exc()

print("\n" + "=" * 60)
print("WorkflowManager with KosDB test completed")
print("=" * 60)

# Cleanup
if os.path.exists("test_workflow.db"):
    os.remove("test_workflow.db")
