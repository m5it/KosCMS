from pathlib import Path
p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines(keepends=True)

# 1. Clean _sa_session
start = None
for i, line in enumerate(lines):
    if "def _sa_session(self):" in line and start is None:
        start = i
        break
if start is None: raise SystemExit("no _sa_session")
end = start + 1
while end < len(lines) and not lines[end].strip().startswith("def "):
    end += 1
new_sa = [
    "    def _sa_session(self):\n",
    '        """Return a SQLAlchemy session from the database manager."""\n',
    "        if self.db is None:\n",
    "            return None\n",
    "        if hasattr(self.db, 'get_session') and callable(self.db.get_session):\n",
    "            return self.db.get_session()\n",
    "        return self.db\n",
    "\n",
]
lines = lines[:start] + new_sa + lines[end:]

# 2. Fix update_settings SQLAlchemy block
for i, line in enumerate(lines):
    if 'print("[DEBUG] Using SQLAlchemy path")' in line:
        sa_start = i - 1
        break
else: raise SystemExit("no SQLAlchemy path")
for j in range(sa_start, len(lines)):
    if 'print("[DEBUG] Settings updated successfully")' in lines[j]:
        sa_end = j
        break
else: raise SystemExit("no end of sqlalchemy block")

new_update_sa = [
    "            else:\n",
    '                print("[DEBUG] Using SQLAlchemy path")\n',
    "                # Use the ORM Setting model for SQLAlchemy path\n",
    "                from webcms.models.system import Setting\n",
    "                session = self._sa_session()\n",
    "                try:\n",
    "                    for key, value in normalized.items():\n",
    "                        type_ = self._guess_type(value)\n",
    "                        existing = session.query(Setting).filter_by(key=key).first()\n",
    "                        if existing:\n",
    "                            existing.value = str(value)\n",
    "                            existing.type = type_\n",
    "                            existing.updated_at = datetime.utcnow()\n",
    "                        else:\n",
    "                            setting = Setting(\n",
    "                                key=key,\n",
    "                                value=str(value),\n",
    "                                type=type_,\n",
    "                                created_at=datetime.utcnow(),\n",
    "                                updated_at=datetime.utcnow()\n",
    "                            )\n",
    "                            session.add(setting)\n",
    "                    session.commit()\n",
    "                except Exception:\n",
    "                    session.rollback()\n",
    "                    raise\n",
    "                finally:\n",
    "                    session.close()\n",
    "\n",
]
lines = lines[:sa_start] + new_update_sa + lines[sa_end:]

with open(p, "w") as f:
n    f.writelines(lines)\nprint("patched admin_api")