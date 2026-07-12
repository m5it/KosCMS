# Plan: Fix Admin Panel CSP & Asset Routing
## ID: 1783840287.8256898
## Created: 2026-07-12 07:11:27
## Status: in_progress

### Goal:
The admin panel is blank because inline scripts are blocked by CSP nonce policy, and nested static assets under /admin/assets/ fail to route. Fix by moving admin UI JavaScript to an external file, supporting multi-segment path parameters in the router, and verifying /admin renders menus and controls.

### Tasks (4):
1. [pending] Move admin JS to external file
   ID: 1783840289.9386477

2. [pending] Support multi-segment path routes in router
   ID: 1783840291.8749337

3. [pending] Update admin route to use path parameter
   ID: 1783840294.0633264

4. [pending] Verify admin panel renders
   ID: 1783840296.10318

---

