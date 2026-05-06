## Ruling 005: Passwords must not be stored in plaintext; use bcrypt or equivalent, with salt rounds >= 12

**Severity:** critical
**Domain:** secret-handling
**Source:** User model in architectural proposal; OWASP A02:2021 (Cryptographic Failures)

**Citation:**

OWASP A02:2021 (Cryptographic Failures); CWE-256 (Unencrypted Storage of Password); OWASP Password Storage Cheat Sheet (bcrypt recommendation)

**Finding:**

The Cat's User model includes 'password_hash,' which is correct. However, the proposal does not specify the hashing algorithm or parameters. If the Tweedles implement this without explicit guidance, they may use weak algorithms (MD5, SHA-1) or insufficient salt rounds. Plaintext or weakly hashed passwords are critical vulnerabilities; if the user table is breached, attackers can crack weak hashes offline at scale.

**Required Remediation:**

Use bcrypt with salt rounds >= 12 for all password hashing. Do not accept MD5, SHA-1, or SHA-256 without salt. Do not implement custom hashing. When a user registers or changes password, hash the new password with bcrypt(password, rounds=12) and store only the hash in password_hash column. Password is never stored in plaintext, logs, error messages, or cache. FastAPI integration: use a library like `passlib` with bcrypt backend (e.g., `CryptContext(schemes=['bcrypt'], deprecated='auto')`).

**Acceptance Criteria:**
- User.password_hash is populated using bcrypt with rounds >= 12
- Password is never logged, cached, or returned in API responses
- Login endpoint compares submitted password against stored hash using bcrypt.verify()
- All password change operations re-hash with bcrypt(rounds=12)
- Caterpillar review confirms no plaintext passwords in code or logs

**Residual Risk:**

If a user's password is compromised (phishing, keylogger), the attacker can access their account. This is unavoidable; mitigate with account-lockout policies and breach notification (see GDPR Art. 33-34 logging ruling).

**Compliance Implications:**

GDPR Art. 32(1)(a) (integrity and confidentiality of personal data); implicit in 'security of processing.'

**Audit Reference:**

Threat Garden entry: 'password hashing standard'; code-review checklist entry: 'password hashing verification.'
