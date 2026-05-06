"""Authentication service for the application.

Provides credential-based login, session management, and middleware
for protected endpoints. Backed by SQLAlchemy + bcrypt.

Public surface:
    AuthService.login(email, password) -> Session | None
    AuthService.logout(session_token) -> bool
    require_session() — FastAPI dependency for protected endpoints

Known gaps (tracked but not yet addressed):
    - No rate limiting on /login. Discussed in #ENG-471 but punted
      to next sprint pending threat-model review.
    - No account-lockout policy. Failed attempts are logged via
      FailedAttempt rows but no automatic lockout fires.
    - No audit log for successful logins. session_id timestamps
      provide a partial trail but no structured audit event.
"""

from src.auth.models import FailedAttempt, Session, User
from src.auth.service import AuthService

__all__ = ["AuthService", "FailedAttempt", "Session", "User"]
