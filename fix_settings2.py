path = "webcms/admin/admin_api.py"
with open(path) as f:
    src = f.read()

marker = "[DEBUG] Using SQLAlchemy path"
idx = src.find(marker)
if idx == -1:
    print("marker not found")
else:
    start = src.rfind("            else:", 0, idx)
    end_marker = 'return Response.json({"updated": False, "error": str(e), "settings": data}, 400)'
    end = src.find(end_marker, idx)
    if end == -1:
        print("end marker not found")
    else:
        end += len(end_marker)
        replacement_lines = [
            "            else:",
            '                print("[DEBUG] Using SQLAlchemy path")',
            "                # Use a proper session from the DatabaseManager",
            "                from sqlalchemy import text",
            "                session = self.db.get_session()",
            "                try:",
            "                    for key, value in normalized.items():",
            "                        type_ = self._guess_type(value)",
            "                        val_str = str(value).replace(\"'\", \"''\")",
            '                        check = session.execute(',
            '                            text(\"SELECT key FROM settings WHERE key=:key\"),',
            '                            {\"key\": key}',
            "                        ).fetchone()",
            "                        if check:",
            "                            session.execute(",
            '                                text(\"UPDATE settings SET value=:value, type=:type WHERE key=:key\"),',
            '                                {\"key\": key, \"value\": val_str, \"type\": type_}',
            "                            )",
            "                        else:",
            "                            session.execute(",
            '                                text(\"INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)\"),',
            '                                {\"key\": key, \"value\": val_str, \"type\": type_}',
            "                            )",
            "                    session.commit()",
            "                except Exception:",
            "                    session.rollback()",
            "                    raise",
            "                finally:",
            "                    session.close()",
            "",
            '            print("[DEBUG] Settings updated successfully")',
            '            return Response.json({\"updated\": True, \"settings\": normalized})',
            "",
            "        except Exception as e:",
            '            print(f\"[DEBUG] Error updating settings: {e}\")',
            "            import traceback",
            "            traceback.print_exc()",
            '            return Response.json({\"updated\": False, \"error\": str(e), \"settings\": data}, 400)',
        ]
        new_block = "\n".join(replacement_lines)
        src = src[:start] + new_block + src[end:]
        with open(path, "w") as f:
n            f.write(src)\n        print(\"fixed\")\n