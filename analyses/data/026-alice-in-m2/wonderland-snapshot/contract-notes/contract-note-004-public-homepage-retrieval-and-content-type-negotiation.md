## Contract Note 004: Public homepage retrieval and content-type negotiation

**State:** agreed
**Contract Version:** v1 (public-homepage-retrieval-accept-header-negotiation)

**Current Shape:**

Not yet specified

**Proposed Change:**

GET /homepage/:slug with Accept header controls response format. Accept: text/html returns full HTML page (backend renders markdown to HTML, includes layout). Accept: text/markdown or Accept: text/plain returns raw markdown. Accept: application/json returns {content_html: '...', markdown_content: '...', published_at, slug} JSON. If no Accept header or Accept: */* defaults to text/html. Also support ?format=html|markdown|json query param as shorthand. Cache-Control: public, max-age=3600. ETag: hash of content + published_at. 404 if slug does not exist or user has not published content. Soft-deleted content returns 404.

**Source:** ticket-005 (public view), ticket-006 (share link)

**Frontend Impact (Tweedledee):**

Frontend: (1) POST publish endpoint returns something that tells frontend the public URL works (either redirects to it, or frontend constructs URL as /homepage/:slug); (2) Share section displays full URL (hostname + /homepage/:slug), no API call needed (frontend knows the URL); (3) Clicking share URL goes to GET /homepage/:slug in browser, backend returns HTML page. Frontend does not need API call to verify publish; POST success is enough. Browser caching (Cache-Control, ETag) is transparent; browser handles conditional requests.

**Backend Impact (Tweedledum):**

Endpoint queries homepages (by slug) and content (by homepage_id) tables. Checks if content exists; if not, returns 404 {error: 'not_found', message: 'This page does not exist or has not been published yet'}. Parses Accept header; if text/html, renders HTML template (jinja2 or equivalent) with {rendered_html [from cache], slug, published_at, footer + inline CSS for minimal styling}. If text/markdown or ?format=markdown, returns raw markdown_content with Content-Type: text/plain. If application/json or ?format=json, returns {content_html, markdown_content, published_at, slug} with Content-Type: application/json (author_slug deferred to v2 to avoid exposing user identity on public pages). Cache headers: public, max-age=3600 (1 hour). ETag: hash of (rendered_html + published_at), computed once at content write time, served on every GET. If user updates content, ETag changes, browser re-fetches (cache invalidation is write-time, not TTL-based). No database writes on GET. Failure mode: content exists but is marked deleted (soft-delete) — return 404. Performance: GET /homepage/:slug is the most common endpoint; optimize for read (index on slug in homepages table, pre-rendered HTML in content table).

**Resolution:** agreed — seam composes. Accept header negotiation is clean; backend serves HTML by default, supports raw markdown and JSON on request. Frontend doesn't need to call the API; browser GET handles caching transparently.

**Resolution:**

Agreed. Accept header negotiation cleanly separates HTML (default), markdown (?format=markdown), and JSON (?format=json) responses. Frontend constructs share URL locally; no verification call needed. Browser handles caching via Cache-Control and ETag. Backend includes hostname in GET /auth/me response for frontend share-URL construction.
