# Common “Gotchas” in Project Build

During development we encountered several recurring issues. Below is a summary of fixes and lessons learned:

---

### 1. **Database & Testing**

* **Issue**: Tests were running on the same database as development, causing data conflicts.
* **Fix**: In `database.py`, we detect `APP_ENV=test` or `PYTEST_CURRENT_TEST` and automatically append `_test` to the database name.
* **Tip**: Always isolate testing DB from dev/prod.

---

### 2. **Redis Caching**

* **Issue**: Corrupted or missing cache keys would raise unexpected exceptions.
* **Fix**:

  * Added `safe_set_hash`, `safe_del_key`, `safe_refresh_ttl` wrappers that swallow Redis errors instead of breaking requests.
  * Invalid/undecodable keys are auto-deleted and rebuilt on next request.
* **Tip**: Cache should **never** bring down the app. Treat it as optional performance layer.

---

### 3. **Repository Rollbacks**

* **Issue**: Some repository methods didn’t call `rollback()` after a failed transaction → sessions got stuck.
* **Fix**: All `create/update/delete` methods now explicitly `rollback()` on exceptions.
* **Tip**: Always rollback before raising exceptions when using SQLAlchemy.

---

### 4. **Cache Key Patterns**

* **Issue**: Passing wrong arguments to cache decorators caused `KeyError` in format strings.
* **Fix**: `_build_cache_key()` now falls back to safe string with args dump.
* **Tip**: Validate key patterns with your method signature.

---

### 5. **Note Filtering**

* **Issue**: SQLAlchemy’s filter with `tags` arrays initially raised `AttributeError`.
* **Fix**: Switched to Postgres operators:

  * `&&` for “any tag”
  * `@>` for “all tags”.
* **Tip**: Always use **Postgres array operators** when filtering `ARRAY` columns.

---

### 6. **Soft Deletes**

* **Issue**: Accidentally returning deleted notes in queries.
* **Fix**: Default `filter_notes()` sets `is_deleted=False` unless explicitly overridden.
* **Tip**: Default to *not showing deleted* unless user asks.

---

### 7. **Indexing & Performance**

* **Issue**: Queries on tags and notebooks became slow at scale.
* **Fix**: Added GIN indexes for tags and composite B-Tree indexes for notebook queries.
* **Tip**: Benchmark filters early and add indexes proactively.

---

### 8. **Value Object Validation**

* **Issue**: Invalid UUID strings would silently pass in entity constructors.
* **Fix**: `UserId`, `NoteId`, `NotebookId` now validate UUID format and raise `ValueError` if invalid.
* **Tip**: Defensive programming: always validate value objects.

---

### 9. **Pytest Failures with Redis**

* **Issue**: Tests failed when Redis was down.
* **Fix**: Safe wrappers (`safe_*`) ensure tests run even without Redis.
* **Tip**: For unit tests, mock or disable Redis entirely.

---

✅ With these fixes, the system is now stable and production-ready with **robust caching, transaction safety, and predictable query performance.**

---
