import sys
sys.path.insert(0, '.')

from webcms.templates.engine import TemplateEngine

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

# Test DB-only templates
db = MockKosDB()
engine = TemplateEngine(template_dirs=[], db=db)
templates = engine.list_templates()
assert any(t['id'] == 'db_only' for t in templates), f"DB-only template missing: {templates}"

# Test save with content return
result = engine.save_template('test_id', '<p>hello</p>', name='test.html')
assert result.get('id') == 'test_id', result
assert result.get('content') == '<p>hello</p>', result
assert result.get('path') == 'test.html', result

# Test SQL escaping
result = engine.save_template("it's", "content with ' quote", name="name'quote")
assert 'error' not in result, result

escaped_contents = []
for ex in db.executes:
    if 'content with' in ex:
        escaped_contents.append(ex)
assert escaped_contents, "No execute contained the test content"
for ex in escaped_contents:
    assert "content with '' quote" in ex, f"Content not escaped in: {ex}"

print("All tests passed")
