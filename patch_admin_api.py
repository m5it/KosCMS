from pathlib import Path; p = Path("webcms/admin/admin_api.py"); txt = p.read_text()
start = txt.find("    def get_settings(self, request: Request) -> Response:")
end = txt.find("    def update_settings(self, request: Request) -> Response:")
if start == -1 or end == -1: print("markers not found"); raise SystemExit(1)
new = """    def _sa_session(self):
        \"\"\"Return a SQLAlchemy session from the database manager.\"\"\"
        if self.db is None:
            return None
        if hasattr(self.db, 'get_session') and callable(self.db.get_session):
            return self.db.get_session()
        return self.db

""" + txt[start:end]
txt = txt[:start] + new + txt[end:]
p.write_text(txt)
print("patched")