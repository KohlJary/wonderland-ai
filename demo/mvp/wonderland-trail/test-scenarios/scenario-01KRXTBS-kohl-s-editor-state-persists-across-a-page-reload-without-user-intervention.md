## Scenario 051: Kohl's editor state persists across a page reload without user intervention

**GUID:** 01KRXTBSX1SQXPMXS4J54GRZBN
**Severity:** silent-wrongness

**Setup:**

Kohl has typed 'Rust async patterns' + 250 words into the editor. She has NOT clicked Save. The browser tab still shows the page. localStorage contains {title: 'Rust async patterns', body: '...250 words...', timestamp: ...}.

**Trigger:**

The browser refreshes (user presses F5, or the page auto-reloads for an app update). The editor component mounts from scratch.

**Expected:**

After the page finishes loading, the title field shows 'Rust async patterns' and the body field shows the full 250-word text. No Save button click required; the restore is automatic. Kohl can immediately continue editing from where she left off.

**Concern:**

If the editor does not restore from localStorage on mount, Kohl's work disappears. She sees blank fields and thinks her typing was lost. This is the core value of the keystroke buffer — protecting against browser restart. If restoration doesn't work, the feature is broken.

**Property:**

editor restores draft from localStorage on mount

**Implies:**
- user-reloads-the-page-editor-restores-the-draft-from-localstorage-and-populates-the-fields
