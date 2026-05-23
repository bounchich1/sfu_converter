# Task 02: Fix README Broken Document References

## Priority: Low
## Phase: Immediate cleanup
## Affected files: `README.md`

## Summary

The README references two documentation files that do not exist in the repository:

- Line 140: `docs/sfu-standard-audit.md` — file does not exist
- Line 141: `docs/superpowers/plans/2026-04-18-sfu-standard-compliance.md` — file and directory do not exist

## Fix

Replace lines 138-141 in `README.md` (the "Документация по стандарту и roadmap" section) to point to the actual documentation:

```markdown
## Документация по стандарту и roadmap

В репозиторий добавлены отдельные документы:

- `docs/formatting requirements/` — требования к оформлению по СТУ 7.5-07-2021, разбитые по типам документов.
- `docs/technical requirements/` — технические требования к переписке проекта, архитектуре, CLI, синтаксису и покрытию тестами.
- `docs/tasks/` — пошаговые задачи по реализации всех фич и рефакторингу.
```

## Verification

- All referenced paths in README must resolve to existing files or directories in the repo.
