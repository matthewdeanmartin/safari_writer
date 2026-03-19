---
name: session-sql-todos
description: Use for session SQL todo tracking or when 0 rows look wrong.
---

# Session SQL TODOs

```sql
todos(id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT, status TEXT DEFAULT 'pending' CHECK(status IN ('pending','in_progress','done','blocked')), created_at TEXT, updated_at TEXT)
todo_deps(todo_id TEXT, depends_on TEXT, PRIMARY KEY(todo_id, depends_on))
```

- Empty by default. `0 rows` usually means empty.
- Start `INSERT ... 'in_progress'`
- Update `UPDATE todos SET status='...' WHERE id='...'`
- Finish `UPDATE ... 'done'` then `DELETE` if transient
- `todo_deps` = blockers `(todo_id depends_on)`
- Split debug queries. Mixed `INSERT; SELECT; DELETE` output can mislead.

```sql
SELECT t.* FROM todos t
WHERE t.status='pending'
AND NOT EXISTS (
  SELECT 1 FROM todo_deps d
  JOIN todos dep ON dep.id=d.depends_on
  WHERE d.todo_id=t.id AND dep.status!='done'
);
```
