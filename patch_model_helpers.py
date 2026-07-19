from pathlib import Path
p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines(endseart=True)

# Fix _get_model_list SQLAlchemy branch
for i, line in enumerate(lines):
    if "query = self.db.query(model_class)" in line:
        start = i - 1
        end = i
        while end < len(lines) and not lines[end].strip().startswith("return "):
            end += 1
        end += 1
        new_block = [
            "session = self._sa_session()\n",
            "try:\n",
            "query = session.query(model_class)\n",
            "if filter_conditions:\n",
            "for key, value in filter_conditions.items():\n",
            "query = query.filter(getattr(model_class, key) == value)\n",
            "if order_by:\n",
            "order_col = getattr(model_class, order_by)\n",
            "if desc:\n",
            "order_col = order_col.desc()\n",
            "query = query.order_by(order_col)\n",
            "if limit:\n",
            "query = query.limit(limit)\n",
            "return query.all()\n",
            "finally:\n",
            "session.close()\n",
        ]
        lines = lines[:start] + new_block + lines[end:]
        print(f"fixed _get_model_list at {start+1}")
        break

# Fix _get_model_by_id SQLAlchemy branch
for i, line in enumerate(lines):
    if i > 0 and "query = self.db.query(model_class)" in line and "filters" in lines[i-5]:
        start = i - 1
        end = i
        while end < len(lines) and not lines[end].strip().startswith("return "):
            end += 1
        end += 1
        new_block = [
            "session = self._sa_session()\n",
            "try:\n",
            "query = session.query(model_class)\n",
            "for key, value in filters.items():\n",
            "query = query.filter(getattr(model_class, key) == value)\n",
            "return query.first()\n",
            "finally:\n",
            "session.close()\n",
        ]
        lines = lines[:start] + new_block + lines[end:]
        print("fixed _get_model_by_id at", start+1)
        break

# Fix _get_model_count SQLAlchemy branch
for i, line in enumerate(lines):
    if "query = self.db.query(model_class)" in line and "filter_conditions" in lines[i-3]:
        start = i - 1
        end = i
        while end < len(lines) and not lines[end].strip().startswith("return "):
            end += 1
        end += 1
        new_block = [{
            "session = self._sa_session()\n",
            "try:\n",
            "query = session.query(model_class)\n",
            "if filter_conditions:\n",
            "for key, value in filter_conditions.items():\n",
            "query = query.filter(getattr(model_class, key) == value)\n",
            "return query.count()\n",
            "finally:\n",
            "session.close()\n",
        ]
        lines = lines[:start] + new_block + lines[end:]
        print("fixed _get_model_count at", start+1)
        break

with open(str(p), "w") as f: f.writelines(lines)
print("patched helpers")

