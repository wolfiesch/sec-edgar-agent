# Review of Tier 0 Demo API Implementation Plan

**Review Date:** 12/11/2025
**Plan Reviewed:** `Plans/Tier_0_Demo_API_Implementation_2025-12-11.md`

## Summary

The plan is excellent. It is focused, aggressive but realistic (2-3 days), and clearly targets the specific differentiators (Table Parsing, Citations, SDK) needed for user validation. The "Day-by-Day" breakdown is logical.

## High-Value Improvements

### 1. Robust Configuration Management

**Current:** Mentions `.env` file additions but relies on manual loading or implicit behavior.
**Suggestion:** Explicitly use `pydantic-settings` to define a `Settings` class. This provides type safety for your config and automatic loading from `.env`.

**Action:**

- Add `src/api/config.py`:

  ```python
  from pydantic_settings import BaseSettings

  class Settings(BaseSettings):
      API_V1_STR: str = "/api/v1"
      PROJECT_NAME: str = "SEC API for LLMs"
      CORS_ORIGINS: list[str] = ["*"]

      class Config:
          env_file = ".env"

  settings = Settings()
  ```

- Use `settings.CORS_ORIGINS` in `main.py` instead of hardcoding `["*"]`.

### 2. Centralized Exception Handling

**Current:** Route handlers use generic `try/except` blocks raising HTTP 500.
**Suggestion:** detailed error messages are crucial for the "Developer Experience". Create custom exception classes and a central handler.

**Action:**

- Add `src/api/exceptions.py` to define specific errors (e.g., `TableNotFound`, `FilingUnavailable`).
- Add an exception handler in `main.py` to convert these to appropriate 404/400/422 responses with helpful error messages.

### 3. Dependency Management Alignment

**Current:** Suggests adding `fastapi` etc. to `pyproject.toml`.
**Observation:** Your `pyproject.toml` already has an `[project.optional-dependencies] -> api` group.
**Suggestion:** Decide if the API is now _core_ (move to main dependencies) or remains optional. For this "Pivot/Startup" phase, moving `fastapi`, `uvicorn`, `pydantic-settings` to the main `dependencies` list is recommended to simplify the "pip install" experience for deployment.

### 4. SDK "Monorepo" Handling

**Current:** The plan creates `sdk/` inside the main repo.
**Suggestion:** Ensure `sdk/pyproject.toml` doesn't conflict with the root one if you try to install both.

- **Tip:** For the demo, you might want to install the SDK in "editable" mode in your scripts: `pip install -e sdk/`. The plan mentions this, which is good. Just ensure your `requirements.txt` or start script handles this path correctly.

### 5. Table Parser State & Concurrency

**Current:** `parser = TableParser()` is instantiated as a global singleton in `tables.py`.
**Suggestion:** If `TableParser` (from the POC) maintains any per-request state (like `self.current_filing`), this will break with concurrent requests.

- **Fix:** Ensure `TableParser` is stateless (methods take all necessary context) OR instantiate it per-dependency/request.

## Minor Tweaks

- **Rate Limiting:** The "Potential Challenges" section correctly identifies SEC rate limits. For the demo, explicitly adding the `edgartools` generic identity/User-Agent configuration to the environment setup instructions is critical to avoid immediate blocking.
- **Testing:** Add `pytest` explicitly to the dev dependencies check (it's already in your `pyproject.toml`, just verify your environment has it).

## Verdict

**Status:** ✅ **APPROVED WITH MINOR REFINEMENTS**
Proceed with execution. The plan is solid.
