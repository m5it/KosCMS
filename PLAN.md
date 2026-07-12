# Plan: Fix Admin Panel Not Loading
## ID: 1783844596.1984804
## Created: 2026-07-12 08:23:16
## Status: in_progress

### Goal:
The admin panel at /admin does not load in the browser. The browser console shows /admin/assets/admin.js and /favicon.ico timing out over HTTPS on port 8000, even though the server is running plain HTTP. Diagnose whether the issue is CSP upgrade-insecure-requests, HSTS browser caching, HTTPS redirect middleware, or the deployed files not matching the edited source. Fix the root cause and verify the admin panel renders with menus and controls.

### Tasks (4):
1. [pending] Verify deployed files match edited source
   ID: 1783844599.8584874

2. [pending] Check HTTPS/HSTS redirect behavior
   ID: 1783844602.5288258

3. [pending] Fix admin asset loading
   ID: 1783844605.2655919

4. [pending] Browser verify admin panel renders
   ID: 1783844610.3948958

---

