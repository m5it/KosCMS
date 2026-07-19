from pathlib import Path

p = Path("webcms/admin/admin_api.py")
content = p.read_text()

# Find the KosDB block in update_settings and replace it
old_kosdb_block = '''            if self._is_kosdb():
                print("[DEBUG] Using KosDB path")
                self._ensure_settings_table_kosdb()

                errors = []

                # OPTIMIZATION: Load all existing keys in a single query instead
                # of issuing one SELECT per setting. This cuts the KosDB round-
                # trips from 2*N (check + write) to N+1 (one check + N writes).
                existing_keys_result = self.db.query("SELECT setting_key FROM settings")
                print(f"[DEBUG] Existing keys query result: {existing_keys_result}")
                if existing_keys_result.get('error'):
                    print(f"[DEBUG] Error loading existing keys: {existing_keys_result.get('error')}")
                    return Response.json({"updated": False, "error": existing_keys_result.get('error'), "settings": normalized}, 400)

                existing_keys = {
                    row.get('setting_key')
                    for row in existing_keys_result.get('rows', [])
                    if row.get('setting_key')
                }
                print(f"[DEBUG] Existing keys: {existing_keys}")

                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = self._sql_escape(str(value))

                    print(f"[DEBUG] Processing setting: {key} = {value} (type: {type_})")

                    exists = key in existing_keys

                    if exists:
                        cmd = (
                            f"UPDATE settings SET value='{val_str}', type='{type_}' "
                            f"WHERE setting_key='{self._sql_escape(key)}'"
                        )
                    else:
                        cmd = (
                            f"INSERT INTO settings (setting_key, value, type) VALUES "
                            f"('{self._sql_escape(key)}', '{val_str}', '{type_}')"
                        )

                    print(f"[DEBUG] Executing: {cmd}")
                    result = self.db.execute(cmd)
                    print(f"[DEBUG] Execute result: {result}")

                    if result and ("ERROR" in result or "No database" in result):
                        errors.append({"key": key, "error": result})

                if errors:
                    print(f"[DEBUG] Errors during update: {errors}")
                    return Response.json({"updated": False, "errors": errors, "settings": normalized}, 400)'''

new_kosdb_block = '''            if self._is_kosdb():
                print("[DEBUG] Using KosDB path")
                self._ensure_settings_table_kosdb()

                errors = []

                # Use transaction context manager for single connection across all operations.
                # This avoids repeated pool acquire/release and ping overhead.
                # Check if db has transaction() method (KosDBClient instance).
                if hasattr(self.db, 'transaction'):
                    # TRANSACTION PATH: Use single pooled connection for all operations
                    with self.db.transaction() as conn:
                        # OPTIMIZATION: All operations share one connection via transaction()
                        # This cuts pool overhead from N acquire/release cycles to 1.
                        existing_keys_result = conn.query("SELECT setting_key FROM settings")
                        print(f"[DEBUG] Existing keys query result: {existing_keys_result}")
                        if existing_keys_result.get('error'):
                            print(f"[DEBUG] Error loading existing keys: {existing_keys_result.get('error')}")
                            return Response.json({"updated": False, "error": existing_keys_result.get('error'), "settings": normalized}, 400)

                        existing_keys = {
                            row.get('setting_key')
                            for row in existing_keys_result.get('rows', [])
                            if row.get('setting_key')
                        }
                        print(f"[DEBUG] Existing keys: {existing_keys}")

                        for key, value in normalized.items():
                            type_ = self._guess_type(value)
                            val_str = self._sql_escape(str(value))

                            print(f"[DEBUG] Processing setting: {key} = {value} (type: {type_})")

                            exists = key in existing_keys

                            if exists:
                                cmd = (
                                    f"UPDATE settings SET value='{val_str}', type='{type_}' "
                                    f"WHERE setting_key='{self._sql_escape(key)}'"
                                )
                            else:
                                cmd = (
                                    f"INSERT INTO settings (setting_key, value, type) VALUES "
                                    f"('{self._sql_escape(key)}', '{val_str}', '{type_}')"
                                )

                            print(f"[DEBUG] Executing: {cmd}")
                            result = conn.execute(cmd)
                            print(f"[DEBUG] Execute result: {result}")

                            if result and ("ERROR" in result or "No database" in result):
                                errors.append({"key": key, "error": result})

                        if errors:
                            print(f"[DEBUG] Errors during update: {errors}")
                            return Response.json({"updated": False, "errors": errors, "settings": normalized}, 400)
                else:
                    # FALLBACK: Raw dict-style db without transaction() - use direct db methods
                    # OPTIMIZATION: Load all existing keys in a single query instead
                    # of issuing one SELECT per setting. This cuts the KosDB round-
                    # trips from 2*N (check + write) to N+1 (one check + N writes).
                    existing_keys_result = self.db.query("SELECT setting_key FROM settings")
                    print(f"[DEBUG] Existing keys query result: {existing_keys_result}")
                    if existing_keys_result.get('error'):
                        print(f"[DEBUG] Error loading existing keys: {existing_keys_result.get('error')}")
                        return Response.json({"updated": False, "error": existing_keys_result.get('error'), "settings": normalized}, 400)

                    existing_keys = {
                        row.get('setting_key')
                        for row in existing_keys_result.get('rows', [])
                        if row.get('setting_key')
                    }
                    print(f"[DEBUG] Existing keys: {existing_keys}")

                    for key, value in normalized.items():
                        type_ = self._guess_type(value)
                        val_str = self._sql_escape(str(value))

                        print(f"[DEBUG] Processing setting: {key} = {value} (type: {type_})")

                        exists = key in existing_keys

                        if exists:
                            cmd = (
                                f"UPDATE settings SET value='{val_str}', type='{type_}' "
                                f"WHERE setting_key='{self._sql_escape(key)}'"
                            )
                        else:
                            cmd = (
                                f"INSERT INTO settings (setting_key, value, type) VALUES "
                                f"('{self._sql_escape(key)}', '{val_str}', '{type_}')"
                            )

                        print(f"[DEBUG] Executing: {cmd}")
                        result = self.db.execute(cmd)
                        print(f"[DEBUG] Execute result: {result}")

                        if result and ("ERROR" in result or "No database" in result):
                            errors.append({"key": key, "error": result})

                    if errors:
                        print(f"[DEBUG] Errors during update: {errors}")
                        return Response.json({"updated": False, "errors": errors, "settings": normalized}, 400)'''

if old_kosdb_block in content:
    content = content.replace(old_kosdb_block, new_kosdb_block)
    p.write_text(content)
    print("Successfully updated update_settings() to use transaction() context manager")
else:
    print("Could not find the exact KosDB block to replace")
    # Try to find partial match
    if "existing_keys_result = self.db.query" in content:
        print("Found partial match - checking context")
    else:
        print("No match found")
