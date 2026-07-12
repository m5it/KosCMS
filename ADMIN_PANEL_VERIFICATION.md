# Admin Panel Verification Steps

## 1. Restart the server

On your deployed VM:

```bash
cd ~/www/KosCMS
source .venv/bin/activate

# Stop any running instance
pkill -f "python3 run.py"

# Start fresh
python3 run.py
```

## 2. Open in a clean browser

Use an **incognito/private** window to avoid cached HSTS/CSP headers:

```
http://aiiaframework.com:8000/admin
```

## 3. Check DevTools Network tab

Open DevTools (F12) → Network tab, then reload the page.

Expected results:

| Request | Status | Content-Type | Notes |
|---------|--------|--------------|-------|
| `GET /admin` | 200 | `text/html` | Should contain sidebar HTML |
| `GET /admin/assets/admin.js` | 200 | `application/javascript` | Must NOT time out |
| `GET /favicon.ico` | 200 | `image/x-icon` | Should not time out |
| `GET /` (homepage) | 200 or 301 | — | Public pages may still redirect to HTTPS |

## 4. Check Response Headers

For `/admin` and `/admin/assets/admin.js`, verify:

- **NO** `Strict-Transport-Security` header
- **NO** `upgrade-insecure-requests` in `Content-Security-Policy`
- `Content-Security-Policy` contains `script-src 'self'`

## 5. Check Console

There should be **no** errors like:

- `net::ERR_TIMED_OUT`
- `Refused to load the script ... because it violates the following Content Security Policy`
- `Bad request version` in server logs

## 6. Verify UI renders

You should see:

- Left sidebar with groups: **Content**, **Design**, **Access**, **Operations**
- Menu items: Dashboard, Pages & Posts, Media, Templates, Themes, Plugins, Users, Roles, Settings, Cache, Backups, Workflows, Tenants, Search, Notifications
- Top bar with breadcrumb and "Admin User"

## 7. If it still fails

If the panel is still blank:

1. Hard-refresh: `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
2. Clear browser HSTS cache for `aiiaframework.com` in `chrome://net-internals/#hsts`
3. Check that the deployed files match this repo:
   ```bash
   grep -n "upgrade-insecure-requests" webcms/admin/routes.py webcms/security/middleware.py
   # Should return nothing
   ```

## curl verification

You can also test from the server itself:

```bash
curl -I http://localhost:8000/admin
curl -I http://localhost:8000/admin/assets/admin.js
curl -I http://localhost:8000/favicon.ico
```

Expected: all return `HTTP/1.1 200 OK` and no `Strict-Transport-Security` header.
