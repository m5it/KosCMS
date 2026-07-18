#!/usr/bin/env python3
"""Test templates and themes endpoints."""

import sys
sys.path.insert(0, '/home/t3ch/adata2/OurAI/playground/KosCMS')

from webcms.core.request import Request
from webcms.admin.admin_api import AdminAPI

print("=" * 60)
print("Testing Templates and Themes Endpoints")
print("=" * 60)

# Create admin API instance with no db
api = AdminAPI(db=None, auth=None)

# Test list_templates
print("\n1. Testing list_templates (no db)...")
request = Request({})
response = api.list_templates(request)
print(f"Response: {response}")
import json
try:
    data = json.loads(response.body)
    templates = data.get('templates', [])
    print(f"Found {len(templates)} templates")
    for t in templates[:5]:
        print(f"  - {t.get('name')} (id: {t.get('id')})")
except Exception as e:
    print(f"Error: {e}")

# Test list_themes
print("\n2. Testing list_themes (no db)...")
response = api.list_themes(request)
print(f"Response: {response}")
try:
    data = json.loads(response.body)
    themes = data.get('themes', [])
    print(f"Found {len(themes)} themes")
    for t in themes:
        print(f"  - {t.get('name')} v{t.get('version')} (active: {t.get('active')})")
        print(f"    Description: {t.get('description')}")
        print(f"    Author: {t.get('author')}")
except Exception as e:
    print(f"Error: {e}")

# Test theme activation if themes exist
if themes:
    theme_id = themes[0].get('id')
    print(f"\n3. Testing activate_theme for '{theme_id}'...")
    response = api.activate_theme(request, theme_id)
    print(f"Response: {response}")
    try:
        data = json.loads(response.body)
        print(f"Parsed: success={data.get('success')}, active={data.get('active')}")
    except Exception as e:
        print(f"Error: {e}")

    print(f"\n4. Testing deactivate_theme for '{theme_id}'...")
    response = api.deactivate_theme(request, theme_id)
    print(f"Response: {response}")
    try:
        data = json.loads(response.body)
        print(f"Parsed: success={data.get('success')}, active={data.get('active')}")
    except Exception as e:
        print(f"Error: {e}")

# Test with KosDB
print("\n5. Testing with KosDB...")
try:
    from kosdb import KosDB
    db = KosDB()
    
    api_with_db = AdminAPI(db=db, auth=None)
    
    print("\n   Testing list_templates with KosDB...")
    response = api_with_db.list_templates(request)
    try:
        data = json.loads(response.body)
        print(f"   Found {len(data.get('templates', []))} templates")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n   Testing list_themes with KosDB...")
    response = api_with_db.list_themes(request)
    try:
        data = json.loads(response.body)
        themes = data.get('themes', [])
        print(f"   Found {len(themes)} themes")
        for t in themes:
            print(f"     - {t.get('name')} (active: {t.get('active')})")
    except Exception as e:
        print(f"   Error: {e}")
    
    if themes:
        theme_id = themes[0].get('id')
        print(f"\n   Testing activate_theme with KosDB for '{theme_id}'...")
        response = api_with_db.activate_theme(request, theme_id)
        try:
            data = json.loads(response.body)
            print(f"   Result: success={data.get('success')}, active={data.get('active')}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Verify persistence
        print("\n   Verifying theme activation persisted...")
        response = api_with_db.list_themes(request)
        try:
            data = json.loads(response.body)
            for t in data.get('themes', []):
                if t.get('id') == theme_id:
                    print(f"   Theme '{theme_id}' active status: {t.get('active')}")
        except Exception as e:
            print(f"   Error: {e}")
    
except ImportError:
    print("   KosDB not available, skipping DB tests")
except Exception as e:
    print(f"   Error with KosDB: {e}")

print("\n" + "=" * 60)
print("All tests complete!")
print("=" * 60)
