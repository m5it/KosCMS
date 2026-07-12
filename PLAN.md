# Plan: Fix KosCMS Admin API Errors
## ID: 1783893354.576747
## Created: 2026-07-12 21:55:54
## Status: in_progress

### Goal:
Fix two critical errors in the KosCMS admin API: (1) ImportError for NotificationQueue class, and (2) AttributeError where dict object has no 'filter' attribute due to KosDB/SQLAlchemy interface mismatch.

### Tasks (7):
1. [pending] Create NotificationQueue class in queue.py
   ID: 1783893357.6022527

2. [pending] Add KosDB detection helper to admin_api.py
   ID: 1783893366.2778819

3. [pending] Fix dashboard() method for KosDB compatibility
   ID: 1783893366.2780678

4. [pending] Fix content list methods for KosDB
   ID: 1783893366.2793355

5. [pending] Fix user CRUD methods for KosDB
   ID: 1783893366.2795057

6. [pending] Fix media and roles methods for KosDB
   ID: 1783893366.2796092

7. [pending] Fix settings methods for KosDB
   ID: 1783893366.2797115

---

