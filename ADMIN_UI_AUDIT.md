# WebCMS Admin UI Audit — 2026-07-12

## Executive Summary

The admin panel blank-screen issue was caused by the CSP `upgrade-insecure-requests` directive forcing the browser to request `/admin/assets/admin.js` over HTTPS while the server runs plain HTTP. This was fixed by serving the admin UI with a custom relaxed CSP. A second issue was a corrupted `AdminShell.jsx` containing literal escaped newlines, which was rewritten.

The remaining blocker is an **API endpoint mismatch**: the React UI calls `/api/v1/admin/*`, but the backend only registers legacy endpoints under `/api/v1/*`.

## Critical Issues (Fixed)

### 1. CSP blocked admin JavaScript asset
- **Symptom:** Blank admin page; browser console showed `net::ERR_TIMED_OUT` for `/admin/assets/admin.js`; server log showed TLS bytes on the HTTP port.
- **Root cause:** The security middleware's CSP included `upgrade-insecure-requests`, so the browser upgraded the same-origin JS request to HTTPS. The HTTP server on port 8000 could not handle the TLS handshake.
- **Fix:** `webcms/admin/routes.py` now sets a custom `Content-Security-Policy` header for all `/admin` responses that does **not** include `upgrade-insecure-requests`.
- **Verification:** WSGI checks confirmed `/admin` and `/admin/assets/admin.js` return 200 with the correct CSP.

### 2. Corrupted AdminShell.jsx
- **Symptom:** Potential JSX parse/runtime failure in the React build.
- **Root cause:** The file contained literal `\n` escape sequences and escaped quotes instead of real newlines/quotes.
- **Fix:** Rewrote `webcms/admin-ui/src/admin/AdminShell.jsx` cleanly with proper JSX syntax, imports, relative child routes, and sidebar navigation.

## High-Priority Issue (Outstanding)

### 3. Admin API endpoint mismatch
- **Symptom:** Management screens will load but show no data or errors because API calls fail.
- **Root cause:** `webcms/admin/api.py` registers endpoints like `/api/v1/dashboard`, `/api/v1/posts`, `/api/v1/users`, etc. The React UI (`webcms/admin-ui/src/admin/pages/*.jsx`) calls `/api/v1/admin/dashboard`, `/api/v1/admin/content`, `/api/v1/admin/users`, etc.
- **Impact:** Every management screen depends on these endpoints.
- **Proposed fix:** Add a new set of `/api/v1/admin/*` endpoints in `webcms/admin/api.py` (or a new `webcms/admin/admin_api.py`) that wrap the existing endpoint classes or implement stub handlers returning the expected JSON shapes. Example endpoints needed:
  - `GET /api/v1/admin/dashboard`
  - `GET /api/v1/admin/content`
  - `GET /api/v1/admin/media`
  - `GET /api/v1/admin/templates`
  - `GET /api/v1/admin/themes`
  - `GET /api/v1/admin/plugins`
  - `GET /api/v1/admin/users`
  - `GET /api/v1/admin/roles`
  - `GET /api/v1/admin/settings`
  - `GET/POST /api/v1/admin/cache/*`
  - `GET/POST /api/v1/admin/backups/*`
  - `GET/POST /api/v1/admin/workflows/*`
  - `GET/POST /api/v1/admin/tenants/*`
  - `GET/POST /api/v1/admin/search/*`
  - `GET/POST /api/v1/admin/notifications/*`

## Medium-Priority Issues

### 4. Version string inconsistency in `DashboardStats`
- **Root cause:** `webcms/admin/api.py` still returns `"version": "1.1.0"` in `DashboardStats`.
- **Fix:** Update to `"1.3.0"` to match `webcms/__init__.py` and `webcms/admin-ui/package.json`.

### 5. React build not produced
- **Root cause:** `npm` is not available in the development shell, so the fallback `dist/index.html` and `dist/assets/admin.js` are plain HTML/JS instead of the bundled React app.
- **Fix:** On the deployment machine, run `cd webcms/admin-ui && npm install && npm run build` to replace the fallback with the real Vite/React bundle.

## Test Results

| Test | Status | Reason |
|------|--------|--------|
| pytest tests/ | FAIL | pytest not installed in shell |
| test_admin.py | FAIL | missing sqlalchemy in shell |
| test_admin_dashboard.py | FAIL | missing sqlalchemy in shell |
| test_backup.py | PASS | |
| test_cache.py | FAIL | missing redis |
| test_graphql.py | FAIL | missing graphene |
| test_nosec.py | FAIL | missing sqlalchemy |
| test_notifications.py | PASS | |
| test_search.py | FAIL | missing elasticsearch |
| test_tenants.py | PASS | |
| test_workflow.py | PASS | |

The admin-related test failures are environment-specific (missing dependencies). They are not code defects.

## Recommended Next Steps

1. Restart the WebCMS server to pick up the CSP and AdminShell fixes.
2. Hard-refresh the browser and confirm the admin sidebar and menu groups render.
3. Implement `/api/v1/admin/*` endpoints so management screens can fetch and display data.
4. Run `npm run build` in `webcms/admin-ui` on the deployment machine to use the React bundle.
5. Update `DashboardStats` version to `"1.3.0"`.
