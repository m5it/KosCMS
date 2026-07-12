# Plan: Fix AUTOVERSION single-source-of-truth sync
## ID: 1783890212.3923602
## Created: 2026-07-12 21:03:32
## Status: in_progress

### Goal:
Repair the corrupted imports in webcms/app_factory.py, replace all hardcoded version strings with imports from webcms.__version__ (which comes from AUTOVERSION.py), update the admin_api.py docstring version, and verify the result with a Python syntax/import check.

### Tasks (3):
1. [pending] Fix app_factory.py imports
   ID: 1783890215.0271313

2. [pending] Replace hardcoded versions in app_factory.py endpoints
   ID: 1783890219.4099796

3. [pending] Update admin_api.py docstring version
   ID: 1783890222.8838978

---

