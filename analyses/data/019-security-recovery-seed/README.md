# T37 security-recovery seed

A minimal-but-realistic FastAPI auth service used as the *starting
codebase* for the T37 security-recovery showcase. The team responds
to a synthesized credential-stuffing incident; their job is to extend
this code, not to invent it from nothing.

## What's here

```
src/
  auth/
    __init__.py      package surface — AuthService, User, Session, FailedAttempt
    models.py        SQLAlchemy models (User, Session, FailedAttempt)
    passwords.py     bcrypt wrappers (hash + verify, work_factor=12)
    service.py       AuthService — login(), logout(), get_session()
    middleware.py    FastAPI session dependency (Bearer token auth)
    endpoints.py     /auth/login, /auth/logout, /auth/me
  main.py            FastAPI app wiring + sqlite engine
tests/
  test_auth.py       baseline coverage — login success/failure, session, logout
pyproject.toml       project metadata + deps
```

~600 lines total. Real working code style — type hints, docstrings,
realistic error handling. Imports `fastapi`, `sqlalchemy`, `bcrypt`,
`pydantic` (none of which Wonderland actually installs at runtime —
the seed is only ever read via `read_file`, never executed by the
runtime).

## What's intentionally missing

The incident response should add these:

- **Rate limiting on /login** — none. A caller can hit POST /login
  arbitrarily quickly. References `#ENG-471` in code comments as the
  open thread, deferred-but-known. This is the load-bearing gap the
  credential-stuffing attack exploits.
- **Account lockout policy** — `FailedAttempt` rows are written but
  never read. No policy fires from the failure log.
- **Audit log for successful logins** — `Session` rows have timestamps
  but nothing produces a structured audit event for a security review.
- **Unlock primitive** — once accounts get locked out, there's no
  self-service recovery path. (T37 v2 surfaced this as the second-wave
  problem; pre-seeding makes it concrete.)

The team's expected behavior:
1. Tweedles `read_file` `auth/service.py`, `auth/endpoints.py`, etc.
2. Write a new `auth/rate_limit.py` (or extend middleware.py)
3. Add lockout state — extend `FailedAttempt` queries or add new
   `LockoutState` model
4. Wire the new primitives into the existing endpoint
5. Caterpillar reviews via `git_diff` against this baseline
6. Hatter writes new test_scenarios; possibly extends `tests/test_auth.py`

## How the showcase script seeds it

`scripts/security_recovery_showcase.py` (or its `/tmp/` equivalent
during development) does:

```python
SEED_DIR = Path("analyses/data/019-security-recovery-seed/")
shutil.copytree(SEED_DIR, project_root, dirs_exist_ok=True)
# … then Runner.make_full_cast initializes git + .gitignore + initial commit
```

The initial git commit captures the seed as the baseline. Every
write_file the Tweedles do shows up in `git_diff HEAD`, which is
exactly what Caterpillar reads.

## Why pre-seed at all

T37 v1 ran without a seed and the team had to imagine the auth surface
*and* respond to the incident in the same thread — three jobs in one.
Cost overran $3 by $0.0093 because the deliberation kept finding open
ends in the imagined system. Pre-seeding constrains the response to
the actual surface and makes the test about what the framework
*meant* to test: incident response on a real codebase.
