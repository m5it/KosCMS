import urllib.request, urllib.error, json, os; base=os.environ.get("WEBCMS_BASE","http://127.0.0.1:43805")
def call(m,p,b=None):
    url=base+p; d=json.dumps(b).encode() if b is not None else None; r=urllib.request.Request(url,data=d,method=m); r.add_header("Content-Type","application/json")
    try:
        with urllib.request.urlopen(r,timeout=5) as resp: return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body=e.read().decode()
        try: return e.code, json.loads(body)
        except Exception: return e.code, body
    except Exception as e: return None, str(e)
for label, args in [
    ("GET /api/v1/admin/settings", ("GET","/api/v1/admin/settings")),
    ("PUT settings", ("PUT","/api/v1/admin/settings",{"site_name":"Test Site Alpha"})),
    ("GET settings verify", ("GET","/api/v1/admin/settings")),
    ("GET pages", ("GET","/api/v1/admin/pages")),
    ("POST page", ("POST","/api/v1/admin/pages",{"title":"Hello Page","slug":"hello-page-1","content":"Initial content"})),
    ("PUT page", ("PUT","/api/v1/admin/pages/hello-page-1",{"title":"Hello Page Updated","content":"Updated content"})),
    ("GET plugins", ("GET","/api/v1/admin/plugins")),
    ("POST activate", ("POST","/api/v1/admin/plugins/contact_form/activate")),
    ("POST deactivate", ("POST","/api/v1/admin/plugins/contact_form/deactivate")),
    ("GET templates", ("GET","/api/v1/admin/templates")),
    ("POST template", ("POST","/api/v1/admin/templates",{"name":"test-template","content":"<html><body>{{content}}</body></html>"})),
    ("PUT template", ("PUT","/api/v1/admin/templates/test-template",{"name":"test-template","content":"<html><body><h1>{{title}}</h1>{{content}}</body></html>"})),
]: print(label, "->", call(*args))