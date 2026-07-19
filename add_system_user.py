from pathlib import Path
p = Path("webcms/admin/admin_api.py")
lines = p.read_text().splitlines(keepends=True)

# Find _current_user_id method and insert _ensure_system_user before it
for i, line in enumerate(lines):
    if "def _current_user_id(self, request: Request) -> str:" in line:
        insert_at = i
        new_method = [
            "    def _ensure_system_user(self):\\n",
            "        \\\"\\\"\\\"Ensure a system user exists and return its id.\\\"\\\"\\\"\\n",
            "        from webcms.models.user import User\\n",
            "        session = self._sa_session()\\n",
            "        try:\\n",
            "            user = session.query(User).filter_by(username='system').first()\\n",
            "            if user:\\n",
            "                return user.id\\n",
            "            user = User(\\n",
            "                username='system',\\n",
            "                email='system@localhost',\\n",
            "                password_hash='system',\\n",
            "                is_active=True,\\n",
            "                is_superuser=True\\n",
            "            )\\n",
            "            session.add(user)\\n",
            "            session.commit()\\n",
            "            return user.id\\n",
            "        finally:\\n",
            "            session.close()\\n",
            "\\n",
        ]
        lines = lines[:insert_at] + new_method + lines[insert_at:]
        print(f"inserted system user helper at {insert_at+1}")
        break

# Fix create_page to use system user id
for i, line in enumerate(lines):
    if "payload.setdefault('author_id', self._current_user_id(request) or 'system')" in line:
        lines[i] = "            payload['author_id'] = self._ensure_system_user()\\n"
        print(f"fixed create_page author_id at {i+1}")
        break

# Fix update_page to use system user if needed
for i, line in enumerate(lines):
    if "page = manager.update_page(page_id, **data)" in line:
        # Insert author_id into data if missing
        lines[i] = "            data.setdefault('author_id', self._ensure_system_user())\\n            page = manager.update_page(page_id, **data)\\n"
        print(f"fixed update_page author_id at {i+1}")
        break

with open(str(p), "w") as f: f.writelines(lines)
print("patched system user")