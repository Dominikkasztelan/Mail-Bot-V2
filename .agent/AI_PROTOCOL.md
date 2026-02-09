# AI Development Protocol: Production & UV Standards

## 1. Environment Management (UV ONLY)
- This project uses `uv` for package management. 
- NEVER suggest `pip`. Use `uv add <package>` for dependencies.
- Use `uv run <script>` for execution to ensure virtual environment isolation.
- Always maintain a consistent `uv.lock` file.
- Python version is pinned via `uv python pin`.

## 2. Code Quality & Production Readiness
- **Strong Typing:** Use Python Type Hints everywhere. Ensure `typing` imports are correct.
- **Config Management:** No hardcoded secrets or URLs. Use environment variables or `pydantic-settings`.
- **Error Handling:** No silent failures. Every `try-except` must handle specific exceptions and log them properly.
- **Async:** Prefer asynchronous patterns for I/O bound tasks where applicable.
- **SOLID/KISS:** Keep code modular but avoid unnecessary abstractions.

## 3. Mandatory "Devil's Advocate" Analysis
Before providing any code, perform a mental "What could go wrong?" check:
- Analyze edge cases (None, Empty, 0, Network Timeout).
- Check for race conditions in concurrent access.
- Ensure input sanitization to prevent security gaps.
- Evaluate performance under 100x load.

## 4. Response Structure Protocol
Every solution must follow this structure:
1. **The Solution:** Clean, documented, typed code with robust error handling.
2. **Potential Pitfalls (Safety Check):** A bulleted list of what might fail in the provided code (e.g., "This function blocks the main thread").
3. **Production Improvements (Hardening):** Specific, actionable steps (e.g., "Add Redis for caching", "Implement Rate Limiting").

## 5. Tooling
- **Formatter/Linter:** Use `Ruff`.
- **Testing:** Use `pytest`.
- **Docs:** Use Google-style docstrings. 
