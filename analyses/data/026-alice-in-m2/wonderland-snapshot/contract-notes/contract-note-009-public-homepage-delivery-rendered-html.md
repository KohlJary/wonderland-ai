## Contract Note 009: Public Homepage Delivery (Rendered HTML)

**State:** agreed
**Contract Version:** v1.0-public-page

**Finalized Shape:**

**GET /homepage/:slug** — unauthenticated, public page
- Response 200: Full HTML page (Content-Type: text/html)
- Response 404: Slug does not exist or content not published (returns HTML error page)
- Headers: Cache-Control: public, max-age=3600; ETag: hash of rendered_html + published_at
- Behavior: Queries homepages and content tables. If content exists and not soft-deleted, renders HTML page (jinja2 template) with user's rendered_html. If not found, returns 404 HTML error page. Page is self-contained (no JavaScript, no CSS framework, minimal inline CSS for readability).

**GET /homepage/:slug?raw=true** — unauthenticated, raw markdown
- Response 200: Raw markdown (Content-Type: text/plain)
- Response 404: Slug does not exist or content not published.
- Behavior: Returns stored markdown_content as plain text. No rendering.

**HTML Page Template (Minimal):**
```
<!DOCTYPE html>
<html>
  <head>
    <title>~{slug} — homepages</title>
    <meta charset="utf-8">
    <style>
      body { font-family: system-ui; max-width: 800px; margin: 2em auto; padding: 1em; }
      a { color: #0066cc; }
    </style>
  </head>
  <body>
    <article>
      {rendered_html}
    </article>
    <footer>
      <p><small>Made with <a href="/">homepages</a> — owned by <strong>~{slug}</strong></small></p>
      <p><small><a href="?raw=true">View raw markdown</a></small></p>
    </footer>
  </body>
</html>
```

**Frontend Behavior (Confirmed):**
- After successful POST /homepage/:slug/content, frontend constructs share URL as `{hostname}/homepage/{slug}`.
- Frontend does NOT make a GET request to verify the page is live; POST 200 is sufficient confirmation.
- User copies/shares the URL; browser navigates to GET /homepage/:slug, renders full HTML page.
- Frontend itself is a SPA (React/Vue); this endpoint returns static HTML (not an API endpoint frontend consumes as JSON).
- Frontend extracts hostname from one of: (1) backend config endpoint, (2) environment variable at build time, or (3) window.location.hostname.

**Hostname Provisioning (Resolved):**
- **Recommendation:** Backend includes `hostname` field in GET /auth/me response.
- **Example:** GET /auth/me returns {email, verified, slug, created_at, hostname: 'homepages.test'}
- **Rationale:** Frontend gets hostname from a single, trusted source (user's profile endpoint). Works across domains (dev, staging, prod). No build-time config required. No window.location assumption (resilient to reverse proxies).
- **Alternative (deferred):** A separate GET /config endpoint returning {hostname, features: {...}}, used at app init. More RESTful but adds a round-trip. v2 can add this if needed.

**Caching & Validation:**
- **Browser caching:** Cache-Control: public, max-age=3600 tells browser to cache for 1 hour.
- **Cache invalidation:** When content is updated (POST /homepage/:slug/content succeeds), ETag changes (hash of rendered_html + published_at). Browser detects stale cache and re-fetches.
- **Frontend does not interact with ETag:** Browser handles this automatically (conditional requests, 304 Not Modified).

**Soft Delete Handling:**
- If a homepage's content is marked deleted (soft-delete), GET /homepage/:slug returns 404 (treat as not-existing).
- Slug reservation is NOT deleted; user retains slug ownership, but page is not publicly visible.

**Failure Modes Handled:**
- Slug does not exist: return 404 HTML error page.
- Content not published yet (slug created but no content): return 404 HTML error page.
- Content deleted (soft-delete): return 404 HTML error page.
- Database query fails (rare): return 500 (Dormouse observes).
- Hostname missing in GET /auth/me: frontend falls back to window.location.hostname (not recommended, but safe).

**Known Limitations:**
- No authentication for private pages in v1; all pages are public once slug is claimed.
- No pagination or multi-page content in v1; one slug = one page.
- No custom CSS or styling in v1; template is minimal baseline.
- No JavaScript on public page in v1 (e.g., no comments, no analytics).

**Resolution:**
- ✅ GET /homepage/:slug returns full self-contained HTML page.
- ✅ GET /homepage/:slug?raw=true returns raw markdown.
- ✅ Frontend constructs share URL as {hostname}/homepage/{slug}.
- ✅ Hostname provisioned via GET /auth/me response (hostname field).
- ✅ Browser caching via Cache-Control + ETag.
- ✅ 404 for nonexistent/deleted pages.
- ✅ Frontend does NOT verify publish by calling GET /homepage/:slug.

**Agreed by:** Tweedledum (2025-01-XX), Tweedledee (responding)
