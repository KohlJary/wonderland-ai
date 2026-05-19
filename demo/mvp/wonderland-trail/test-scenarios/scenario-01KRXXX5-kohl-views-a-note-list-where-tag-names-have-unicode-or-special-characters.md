## Scenario 148: Kohl views a note list where tag names have unicode or special characters

**GUID:** 01KRXXX5EYSQXB8M7T8022QXTP
**Severity:** silent-wrongness

**Setup:**

Kohl has tagged notes with multilingual tags: 'rust-🦀', 'python-🐍', 'café', 'naïve-algo', '中文', '日本語'. The list view renders all notes.

**Trigger:**

Each tag displays in its badge.

**Expected:**

All unicode and special-character tags render correctly and legibly. No mojibake, no truncation, no rendering errors. Badges scale appropriately to their content (longer tag names get slightly wider badges, but remain aligned).

**Concern:**

If the frontend doesn't handle unicode properly (e.g., uses substring truncation that breaks multi-byte characters, or doesn't set UTF-8 charset), tags will display as garbled text. Kohl's international tags become unreadable.

**Property:**

Tag display must correctly handle unicode and special characters across all target platforms (web, mobile if applicable).

**Implies:**
- Tag text must be rendered as UTF-8 without encoding errors.
- Tag truncation (if any) must be character-aware, not byte-aware.
- Badge sizing must not assume fixed character width.
