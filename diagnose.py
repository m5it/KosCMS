#!/usr/bin/env python3
"""Diagnose admin panel loading issue"""

import urllib.request
import urllib.error

BASE_URL = "http://192.168.0.68:8000"

urls_to_test = [
    "/",
    "/admin",
    "/admin/posts",
    "/admin/pages", 
    "/admin/settings",
]

print("Testing URLs...")
print("=" * 50)

for url in urls_to_test:
    full_url = BASE_URL + url
    print(f"\nTesting: {full_url}")
    try:
        req = urllib.request.Request(full_url, method='GET')
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        response = urllib.request.urlopen(req, timeout=5)
        
        print(f"  Status: {response.status}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"  Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        
        # Read first 500 bytes
        data = response.read(500)
        print(f"  Preview: {data[:200]}...")
        print("  ✓ SUCCESS")
        
    except urllib.error.HTTPError as e:
        print(f"  ✗ HTTP Error: {e.code} {e.reason}")
    except urllib.error.URLError as e:
        print(f"  ✗ Connection Error: {e.reason}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\n" + "=" * 50)
print("If all show SUCCESS but browser still hangs,")
print("check browser DevTools (F12) → Console for errors")
