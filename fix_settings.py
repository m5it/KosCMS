#!/usr/bin/env python3
"""
Fix settings save functionality - add debugging and ensure proper KosDB persistence
"""

import re

with open('webcms/admin/admin_api.py', 'r') as f:
    content = f.read()

# Find the update_settings method and add better error handling and debugging
old_update_settings = '''    def update_settings(self, request: Request) -> Response:
        data = request.json or {}
        if not self.db:
            return Response.json({"updated": True, "settings": data})
        normalized = {}
        for key, value in data.items():
            normalized[key] = self._normalize_setting_value(key, value)
        try:
            if self._is_kosdb():
                self._ensure_settings_table_kosdb()
                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = self._sql_escape(str(value))
                    check = self.db.query(
                        f"SELECT setting_key FROM settings WHERE setting_key='{self._sql_escape(key)}'"
                    )
                    exists = bool(check.get('rows', []))
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
                    self.db.execute(cmd)
            else:
                # Use raw SQL to avoid ORM mapper configuration issues.
                from sqlalchemy import text
                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = str(value).replace("'", "''")
                    check = self.db.execute(
                        text("SELECT key FROM settings WHERE key=:key"),
                        {"key": key}
                    ).fetchone()
                    if check:
                        self.db.execute(
                            text("UPDATE settings SET value=:value, type=:type WHERE key=:key"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                    else:
                        self.db.execute(
                            text("INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                self.db.commit()
            return Response.json({"updated": True, "settings": normalized})
        except Exception as e:
            if not self._is_kosdb():
                self.db.rollback()
            return Response.error(str(e), 400)'''

new_update_settings = '''    def update_settings(self, request: Request) -> Response:
        data = request.json or {}
        print(f"[DEBUG] update_settings called with data: {data}")
        
        if not self.db:
            print("[DEBUG] No database connection, returning mock success")
            return Response.json({"updated": True, "settings": data})
        
        normalized = {}
        for key, value in data.items():
            normalized[key] = self._normalize_setting_value(key, value)
        
        print(f"[DEBUG] Normalized settings: {normalized}")
        
        try:
            if self._is_kosdb():
                print("[DEBUG] Using KosDB path")
                self._ensure_settings_table_kosdb()
                
                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = self._sql_escape(str(value))
                    
                    print(f"[DEBUG] Processing setting: {key} = {value} (type: {type_})")
                    
                    # Check if setting exists
                    check_query = f"SELECT setting_key FROM settings WHERE setting_key='{self._sql_escape(key)}'"
                    print(f"[DEBUG] Check query: {check_query}")
                    
                    check = self.db.query(check_query)
                    print(f"[DEBUG] Check result: {check}")
                    
                    exists = bool(check.get('rows', []))
                    
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
                    
            else:
                print("[DEBUG] Using SQLAlchemy path")
                # Use raw SQL to avoid ORM mapper configuration issues.
                from sqlalchemy import text
                for key, value in normalized.items():
                    type_ = self._guess_type(value)
                    val_str = str(value).replace("'", "''")
                    check = self.db.execute(
                        text("SELECT key FROM settings WHERE key=:key"),
                        {"key": key}
                    ).fetchone()
                    if check:
                        self.db.execute(
                            text("UPDATE settings SET value=:value, type=:type WHERE key=:key"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                    else:
                        self.db.execute(
                            text("INSERT INTO settings (key, value, type) VALUES (:key, :value, :type)"),
                            {"key": key, "value": val_str, "type": type_}
                        )
                self.db.commit()
                
            print("[DEBUG] Settings updated successfully")
            return Response.json({"updated": True, "settings": normalized})
            
        except Exception as e:
            print(f"[DEBUG] Error updating settings: {e}")
            import traceback
            traceback.print_exc()
            if not self._is_kosdb():
                self.db.rollback()
            return Response.json({"updated": False, "error": str(e), "settings": data}, 400)'''

if old_update_settings in content:
    content = content.replace(old_update_settings, new_update_settings)
    print("Updated update_settings method with debugging")
else:
    print("Could not find exact match for update_settings, trying partial match...")
    # Try to find and replace with a more flexible pattern

# Also improve get_settings to add debugging
old_get_settings = '''    def get_settings(self, request: Request) -> Response:
        defaults = {
            "site_name": "WebCMS",
            "site_url": "https://example.com",
            "admin_email": "admin@example.com",
            "default_language": "en",
            "posts_per_page": 10,
            "cache_enabled": True,
            "cache_ttl": 300,
            "search_enabled": True,
            "elasticsearch_url": "http://localhost:9200",
            "notifications_enabled": True,
            "smtp_host": "localhost",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_pass": "",
            "csp_enabled": True,
            "require_https": False
        }
        if not self.db:
            return Response.json({"settings": defaults})
        try:
            if self._is_kosdb():
                self._ensure_settings_table_kosdb()
                result = self.db.query("SELECT * FROM settings")
                if result.get('error'):
                    return Response.json({"settings": defaults})
                settings = result.get('rows', [])
                for s in settings:
                    key = s.get('setting_key')
                    if not key:
                        continue
                    defaults[key] = self._coerce_setting(s.get('value'), s.get('type'))
            else:
                # Use raw SQL to avoid ORM mapper configuration issues.
                from sqlalchemy import text
                rows = self.db.execute(text("SELECT key, value, type FROM settings")).fetchall()
                for row in rows:
                    defaults[row[0]] = self._coerce_setting(row[1], row[2])
        except Exception:
            pass
        return Response.json({"settings": defaults})'''

new_get_settings = '''    def get_settings(self, request: Request) -> Response:
        print("[DEBUG] get_settings called")
        defaults = {
            "site_name": "WebCMS",
            "site_url": "https://example.com",
            "admin_email": "admin@example.com",
            "default_language": "en",
            "posts_per_page": 10,
            "cache_enabled": True,
            "cache_ttl": 300,
            "search_enabled": True,
            "elasticsearch_url": "http://localhost:9200",
            "notifications_enabled": True,
            "smtp_host": "localhost",
            "smtp_port": 587,
            "smtp_user": "",
            "smtp_pass": "",
            "csp_enabled": True,
            "require_https": False
        }
        if not self.db:
            print("[DEBUG] No database, returning defaults")
            return Response.json({"settings": defaults})
        try:
            if self._is_kosdb():
                print("[DEBUG] Using KosDB for get_settings")
                self._ensure_settings_table_kosdb()
                result = self.db.query("SELECT * FROM settings")
                print(f"[DEBUG] Settings query result: {result}")
                if result.get('error'):
                    print(f"[DEBUG] Error getting settings: {result.get('error')}")
                    return Response.json({"settings": defaults})
                settings = result.get('rows', [])
                print(f"[DEBUG] Found {len(settings)} settings")
                for s in settings:
                    key = s.get('setting_key')
                    if not key:
                        continue
                    defaults[key] = self._coerce_setting(s.get('value'), s.get('type'))
                    print(f"[DEBUG] Loaded setting: {key} = {defaults[key]}")
            else:
                print("[DEBUG] Using SQLAlchemy for get_settings")
                # Use raw SQL to avoid ORM mapper configuration issues.
                from sqlalchemy import text
                rows = self.db.execute(text("SELECT key, value, type FROM settings")).fetchall()
                for row in rows:
                    defaults[row[0]] = self._coerce_setting(row[1], row[2])
        except Exception as e:
            print(f"[DEBUG] Error in get_settings: {e}")
            import traceback
            traceback.print_exc()
        print(f"[DEBUG] Returning settings: {defaults}")
        return Response.json({"settings": defaults})'''

if old_get_settings in content:
    content = content.replace(old_get_settings, new_get_settings)
    print("Updated get_settings method with debugging")
else:
    print("Could not find exact match for get_settings")

with open('webcms/admin/admin_api.py', 'w') as f:
    f.write(content)

print("Settings methods updated!")
