import sys
sys.path.insert(0, '.')

from webcms.admin.admin_api import AdminAPI

class MockKosDB:
    def __init__(self):
        self.tables = {}
        self.queries = []
        self.executes = []
    def list_tables(self):
        return list(self.tables.keys())
    def query(self, sql):
        self.queries.append(sql)
        if 'CREATE TABLE' in sql or 'INSERT INTO' in sql or 'UPDATE' in sql or 'DELETE FROM' in sql:
            return {'rows': []}
        if 'SELECT id FROM templates' in sql:
            return {'rows': []}
        if 'SELECT id, name, path, content, updated_at FROM templates' in sql:
            return {'rows': [
                {'id': 'db_only', 'name': 'db_only.html', 'path': 'db_only.html', 'content': '<h1>DB</h1>', 'updated_at': '2024-01-01T00:00:00'}
            ]}
        return {'rows': []}
    def execute(self, sql):
        self.executes.append(sql)
        if 'CREATE TABLE' in sql:
            self.tables['templates'] = True

class MockRequest:
    def __init__(self, json_data=None):
        self.json = json_data

api = AdminAPI(db=MockKosDB())

def body_str(res):
    return res.body.decode() if isinstance(res.body, bytes) else res.body

# Test list_templates returns DB-only templates
req = MockRequest()
res = api.list_templates(req)
body = body_str(res)
assert 'db_only' in body, body

# Test create_template returns full record with content
req = MockRequest({'id': 'new_tpl', 'name': 'new.html', 'content': '<p>hi</p>'})
res = api.create_template(req)
body = body_str(res)
assert res.status == 201, body
assert '<p>hi</p>' in body, body
assert 'new_tpl' in body, body

# Test update_template returns full record
req = MockRequest({'content': '<p>updated</p>', 'name': 'updated.html'})
res = api.update_template(req, 'new_tpl')
body = body_str(res)
assert res.status == 200, body
assert '<p>updated</p>' in body, body

print("Admin API template tests passed")
