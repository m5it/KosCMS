path = "webcms/admin/admin_api.py"
with open(path) as f:
    lines = f.readlines()

# Lines are 0-indexed internally; target 1319-1349 (1-indexed) -> indices 1318-1349
start = 1318
end = 1349

replacement = \"\"\"            else:
                print(\"[DEBUG] Using SQLAlchemy path\")
                # Use a proper session from the DatabaseManager
                from sqlalchemy import text
                session = self.db.get_session()
                try:
                    for key, value in normalized.items():
                        type_ = self._guess_type(value)
                        val_str = str(value).replace(\"'\", \"''\")
                        check = session.execute(
                            text(\"SELECT key FROM settings WHERE key=:key\"),
n                            {\"key\": key}\n                        ).fetchone()\n                        if check:\n                            session.execute(\n                                text(\"UPDATE settings SET value=:value, type=:type WHERE key=:key\"),\n                                {\"key\": key, \"value\": val_str, \"type\": type_}\n                            )\n                        else:\n                            session.execute(\n                                text(\"INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)\"),\n                                {\"key\": key, \"value\": val_str, \"type\": type_}\n                            )\n                    session.commit()\n                except Exception:\n                    session.rollback()\n                    raise\n                finally:\n                    session.close()\n\n            print(\"[DEBUG] Settings updated successfully\")\n            return Response.json({\"updated\": True, \"settings\": normalized})\n\n        except Exception as e:\n            print(f\"[DEBUG] Error updating settings: {e}\")\n            import traceback\n            traceback.print_exc()\n            return Response.json({\"updated\": False, \"error\": str(e), \"settings\": data}, 400)\n\"\"\"\n\nnew_lines = replacement.splitlines(keepends=True)\nlines = lines[:start] + new_lines + lines[end:]\n\nwith open(path, \"w\") as f:\n    f.writelines(lines)\nprint(\"fixed settings lines\")\n