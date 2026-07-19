import urllib.request, urllib.error, json, os, sys, time
base = os.environ.get("WEBCMS_BASE", "http://127.0.0.1:43805")
unique_slug = f"hello-page-{int(time.time())}"
def call(m, p, b=None, expect_json=True):
    url = base + p
    data = json.dumps(b).encode() if b is not None else None
    req = urllib.request.Request(url, data=data, method=m)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode()
            if expect_json:
                return resp.status, json.loads(body)
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try: return e.code, json.loads(body)
        except Exception: return e.code, body
    except Exception as e: return None, str(e)

checks = [
    ("settings read", lambda s, b: s == 200 and b.get("settings", {}).get("site_name") == "Test Site Alpha", ("GET", "/api/v1/admin/settings", None, True)),
    ("settings update", lambda s, b: s == 200 and b.get("updated") is True, ("PUT", "/api/v1/admin/settings", {"site_name": "Test Site Alpha"}, True)),
    ("admin ui", lambda s, b: s == 200 and "WebCMS Admin" in b, ("GET", "/admin", None, False)),
    ("page create", lambda s, b: s == 201 and unique_slug in b.get("slug", ""), ("POST", "/api/v1/admin/pages", {"title": "Hello Page", "slug": unique_slug, "content": "Initial content"}, True)),
    ("page update", lambda s, b: s == 200 and b.get("title") == "Hello Page Updated", ("PUT", f"/api/v1/admin/pages/{unique_slug}", {"title": "Hello Page Updated", "content": "Updated content"}, True)),
    ("plugins list", lambda s, b: s == 200 and "plugins" in b, ("GET", "/api/v1/admin/plugins", None, True)),
    ("plugin activate", lambda s, b: s == 200 and b.get("active") is True, ("POST", "/api/v1/admin/plugins/contact_form/activate", None, True)),
    ("plugin deactivate", lambda s, b: s == 200 and b.get("active") is False, ("POST", "/api/v1/admin/plugins/contact_form/deactivate", None, True)),
    ("templates list", lambda s, b: s == 200 and "templates" in b, ("GET", "/api/v1/admin/templates", None, True)),
    ("template create", lambda s, b: s == 201 and b.get("id") == "test-template", ("POST", "/api/v1/admin/templates", {"name": "test-template", "content": "<html><body>{{content}}</body></html>"}, True)),
    ("template update", lambda s, b: s == 200 and b.get("updated") is True, ("PUT", "/api/v1/admin/templates/test-template", {"name": "test-template", "content": "<html><body><h1>{{title}}</h1>{{content}}</body></html>"}, True)),
]

failed = []
for name, check, args in checks:
    status, body = call(*args)
    ok = check(status, body)
    print(f"{'PASS' if ok else 'FAIL'}: {name} (HTTP {status})")
    if not ok:
        failed.append((name, status, body))

if failed:
    print(f"\n{len(failed)} check(s) failed:")
    for name, status, body in failed:
        print(f"  - {name}: {status} {body[:200] if isinstance(body, str) else body}")
    sys.exit(1)
print("\nAll checks passed.")
