/**
 * Preview — renders markdown body as HTML.
 *
 * Contract: accepts markdown body (string) as prop; renders HTML.
 * Supports: headers (# through ######), code blocks (triple-backtick fenced),
 * unordered lists, ordered lists, links, images, blockquotes.
 *
 * Security: uses DOMPurify to sanitize HTML and prevent XSS.
 * No syntax highlighting for code blocks yet (deferred to M5).
 *
 * Invariants:
 * - all HTML is sanitized before rendering (no XSS)
 * - empty body renders as empty div (no error state)
 * - malformed markdown gracefully degrades (renders what it can parse)
 */

import { useMemo } from 'react';
import DOMPurify from 'dompurify';
import { marked } from 'marked';

interface PreviewProps {
  body: string;
}

export function Preview({ body }: PreviewProps) {
  // Parse markdown and sanitize HTML once per body change
  const htmlContent = useMemo(() => {
    if (!body || body.trim() === '') {
      return '';
    }
    try {
      const rawHtml = marked(body);
      const cleanHtml = DOMPurify.sanitize(rawHtml);
      return cleanHtml;
    } catch (err) {
      // Malformed markdown: show error inline, not as crash
      console.error('Markdown parse error:', err);
      return `<p style="color: #999; font-style: italic;">Error parsing markdown</p>`;
    }
  }, [body]);

  return (
    <div
      className="preview"
      dangerouslySetInnerHTML={{ __html: htmlContent }}
      style={{
        flex: 1,
        padding: '1rem',
        overflow: 'auto',
        borderLeft: '1px solid #ddd',
        lineHeight: 1.6,
        color: '#333',
      }}
    />
  );
}

export default Preview;
