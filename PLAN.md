# Plan: Settings Save Performance Optimization
## ID: 1784451884.852964
## Created: 2026-07-19 09:04:44
## Status: in_progress

### Goal:
Optimize the CMS settings save path to reduce database round-trips and connection overhead, targeting the 10-30 second save time on /admin/settings. Focus on changes within this repository: the CMS admin API and the KosDB client adapter. Document KosDB-server-side limitations that require changes in the external test.KosDB project.

### Tasks (6):
1. [pending] Fix N+1 SELECT in update_settings
   ID: 1784451891.5425017

2. [pending] Add connection reuse for KosDB multi-query operations
   ID: 1784451891.5427217

3. [pending] Use KosDB transaction in update_settings
   ID: 1784451891.5436406

4. [pending] Reduce ping overhead in KosDB pool
   ID: 1784451891.5437474

5. [pending] Add benchmark test for settings save
   ID: 1784451891.5438564

6. [pending] Document KosDB server-side limitations
   ID: 1784451891.5439565

---

