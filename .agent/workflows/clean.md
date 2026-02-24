---
description: remove Python cache directories and pytest/mypy artifacts
---

// turbo
1. Run `for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"` to remove all `__pycache__` folders.
// turbo
2. Run `if exist .pytest_cache rd /s /q .pytest_cache` to remove pytest cache.
// turbo
3. Run `if exist .mypy_cache rd /s /q .mypy_cache` to remove mypy cache.
