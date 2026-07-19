path = "webcms/admin/admin_api.py"
with open(path) as f:
    lines = f.readlines()

start = 1318  # 0-indexed for line 1319
end = 1349    # 0-indexed for line 1349

new_lines = [
    "            else:\n",
    '                print("[DEBUG] Using SQLAlchemy path")\n',
    "                # Use a proper session from the DatabaseManager\n",
    "                from sqlalchemy import text\n",
    "                session = self.db.get_session()\n",
    "                try:\n",
    "                    for key, value in normalized.items():\n",
    "                        type_ = self._guess_type(value)\n",
    "                        val_str = str(value).replace(\"'\", \"''\")\n",
    '                        check = session.execute(\n',
    '                            text(\"SELECT key FROM settings WHERE key=:key\"),\n',
    '                            {\"key\": key}\n',
    "                        ).fetchone()\n",
    "                        if check:\n",
    "                            session.execute(\n",
    '                                text(\"UPDATE settings SET value=:value, type=:type WHERE key=:key\"),\n',
    '                                {\"key\": key, \"value\": val_str, \"type\": type_}\n',
    "                            )\n",
    "                        else:\n",
    "                            session.execute(\n",
    '                                text(\"INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)\"),\n',
    '                                {\"key\": key, \"value\": val_str, \"type\": type_}\n',
    "                            )\n",
    "                    session.commit()\n",
    "                except Exception:\n",
    "                    session.rollback()\n",
    "                    raise\n",
    "                finally:\n",
    "                    session.close()\n",
    "\n",
    '            print("[DEBUG] Settings updated successfully")\n',
    '            return Response.json({\"updated\": True, \"settings\": normalized})\n',
    "\n",
    "        except Exception as e:\n",
    '            print(f\"[DEBUG] Error updating settings: {e}\")\n',
    "            import traceback\n",
    "            traceback.print_exc()\n",
    '            return Response.json({\"updated\": False, \"error\": str(e), \"settings\": data}, 400)\n',
]

lines = lines[:start] + new_lines + lines[end:]

with open(path, "w") as f:
    f.writelines(lines)
print("fixed settings lines")
