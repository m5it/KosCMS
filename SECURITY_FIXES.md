# WebCMS Security Header Fixes

## Issue Summary
Admin panel navigation buttons (Posts, Pages, Media, etc.) were hanging/not loading due to overly restrictive security headers blocking navigation in the browser context.

## Root Cause
The `Cross-Origin-Embedder-Policy: require-corp` header combined with `X-Frame-Options: DENY` was preventing normal navigation between admin pages.

## Changes Made

### webcms/security/middleware.py

| Header | Before | After | Reason |
|--------|--------|-------|--------|
| `X-Frame-Options` | `DENY` | `SAMEORIGIN` | Allow framing from same origin |
| `frame_ancestors` CSP | `'none'` | `'self'` | Allow same-origin embedding |
| `Cross-Origin-Embedder-Policy` | `require-corp` | **REMOVED** | Was blocking navigation |
| `Cross-Origin-Opener-Policy` | `same-origin` | **REMOVED** | Was blocking navigation |

### webcms/app_factory.py

| Change | Description |
|--------|-------------|
| API registration | Now works with both 'db' (SQLAlchemy) AND 'kosdb' services |
| Response imports | Added proper `Response.html()` and `Response.json()` returns |
| All routes | Now return proper Response objects instead of strings/dicts |

## COEP/COOP Compatibility Note

**Cross-Origin-Embedder-Policy (COEP)** and **Cross-Origin-Opener-Policy (COOP)** are modern security headers designed to enable cross-origin isolation and protect against Spectre attacks. However:

- `COEP: require-corp` requires all subresources to have CORP headers
- `COOP: same-origin` prevents cross-origin window interactions

These headers can break:
- Navigation between pages in single-page applications
- Embedded content (iframes, frames)
- Cross-origin popups and window.open()

**Recommendation**: Only enable COEP/COOP if:
1. All subresources have proper CORP headers
2. You don't need cross-origin interactions
3. You're running in a high-security environment with full control over all resources

## Files Modified

1. `webcms/security/middleware.py` - Security headers configuration
2. `webcms/app_factory.py` - Response handling and API registration

## Verification

All admin routes tested and working:
- ✅ /admin (Dashboard)
- ✅ /admin/posts
- ✅ /admin/pages
- ✅ /admin/media
- ✅ /admin/users
- ✅ /admin/plugins
- ✅ /admin/themes
- ✅ /admin/settings

All API endpoints accessible:
- ✅ /api/v1/status (returns 200)
- ⚠️ /api/v1/dashboard (501 when using KosDB - expected)
- ⚠️ /api/v1/posts (501 when using KosDB - expected)

## Security Trade-offs

**Removed protection:**
- Cross-origin isolation (Spectre protection)
- Cross-origin window control

**Retained protection:**
- CSP (Content Security Policy)
- XSS Protection
- Content-Type sniffing prevention
- HTTPS redirect
- Frame options (sameorigin)

## Recommendation

For production deployments requiring high security:

1. Consider implementing a `security_strict` mode flag in config
2. Only enable COEP/COOP if all subresources support CORP
3. Use `report-only` mode for CSP to test before enforcing
4. Document any third-party resources that need CORP headers

## Syntax Verification

All modified files pass Python syntax validation:
- ✅ webcms/security/middleware.py
- ✅ webcms/app_factory.py
- ✅ webcms/admin/routes.py
