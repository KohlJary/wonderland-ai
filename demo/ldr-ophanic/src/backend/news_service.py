"""
RSS feed polling service for Austrian news.

Fetches headlines from Der Standard and ORF RSS feeds, extracts top 3 from each,
and returns structured headline objects.

**Contract:**
- Fetch from Der Standard and ORF RSS feeds (daily polling)
- Extract top 3 headlines per feed (title, URL, source)
- Handle encoding issues (UTF-8, ISO-8859-1)
- Graceful degradation: if one feed fails, return results from the other
- If both feeds fail, raise NewsServiceException

**Invariants enforced:**
- Each headline has non-empty title, url, source
- Headlines are deduplicated by URL (same article shouldn't appear twice)
- Source is either "Der Standard" or "ORF"
- URLs are preserved exactly as provided by feeds
"""
import logging
from typing import List, Optional
import feedparser

logger = logging.getLogger(__name__)


class NewsServiceException(Exception):
    """Raised when news fetching fails."""
    pass


class Headline:
    """Single news headline from RSS feed."""
    
    def __init__(self, title: str, url: str, source: str):
        self.title = title
        self.url = url
        self.source = source
    
    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
        }


async def fetch_austrian_news() -> List[Headline]:
    """
    Fetch top Austrian news headlines from Der Standard and ORF RSS feeds.
    
    **Flow:**
    1. Fetch Der Standard RSS feed
    2. Fetch ORF RSS feed
    3. Extract top 3 headlines from each (6 total)
    4. Deduplicate by URL
    5. Return combined list
    
    **Failure modes:**
    - Feed timeout: log error, continue with other feed
    - Feed unreachable (404, 503): log error, continue with other feed
    - Both feeds fail: raise NewsServiceException
    - Feed parse error: log error, continue with next feed
    - Empty feed: return empty list for that feed
    
    **Args:**
    None
    
    **Returns:**
    List of Headline objects (up to 6 if both feeds succeed, fewer if one fails)
    
    **Raises:**
    NewsServiceException: if both feeds fail to fetch/parse
    """
    
    # Feed URLs
    feeds = {
        "Der Standard": "https://www.derstandard.at/rss",
        "ORF": "https://rss.orf.at/news.xml",
    }
    
    all_headlines = []
    failed_feeds = []
    
    for source, feed_url in feeds.items():
        try:
            logger.debug(f"Fetching {source} RSS feed from {feed_url}")
            
            # feedparser handles encoding detection automatically
            feed = feedparser.parse(feed_url)
            
            # Check for parse errors
            if feed.bozo and feed.bozo_exception:
                logger.warning(
                    f"Feed parse warning for {source}: {feed.bozo_exception}. "
                    f"Continuing with partial data."
                )
            
            # Extract headlines
            if not feed.entries:
                logger.warning(f"{source} feed returned no entries")
                failed_feeds.append(source)
                continue
            
            # Take top 3 headlines from this feed
            headlines = _extract_headlines(feed.entries[:3], source)
            logger.info(f"Extracted {len(headlines)} headlines from {source}")
            all_headlines.extend(headlines)
            
        except Exception as e:
            logger.error(
                f"Failed to fetch {source} feed: {type(e).__name__}: {str(e)}"
            )
            failed_feeds.append(source)
    
    # If both feeds failed, raise exception
    if len(failed_feeds) == len(feeds):
        raise NewsServiceException(
            f"Failed to fetch headlines from all feeds: {', '.join(failed_feeds)}"
        )
    
    # Deduplicate by URL
    seen_urls = set()
    deduplicated = []
    for headline in all_headlines:
        if headline.url not in seen_urls:
            seen_urls.add(headline.url)
            deduplicated.append(headline)
    
    logger.info(
        f"Fetched {len(deduplicated)} headlines total "
        f"({len(all_headlines)} before dedup, {len(failed_feeds)} feeds failed)"
    )
    
    return deduplicated


def _extract_headlines(entries: list, source: str) -> List[Headline]:
    """
    Extract headline objects from RSS feed entries.
    
    **Args:**
    entries: list of feedparser entry objects
    source: source name (e.g., "Der Standard")
    
    **Returns:**
    List of Headline objects with title, url, source
    """
    headlines = []
    
    for entry in entries:
        try:
            title = entry.get("title", "").strip()
            # Prefer 'link' field; fallback to 'id' if present
            url = entry.get("link") or entry.get("id", "")
            
            if not title or not url:
                logger.debug(
                    f"Skipping entry from {source}: missing title or url. "
                    f"Title='{title}', URL='{url}'"
                )
                continue
            
            headlines.append(Headline(title=title, url=url, source=source))
        except Exception as e:
            logger.warning(
                f"Failed to parse entry from {source}: {type(e).__name__}: {str(e)}"
            )
            continue
    
    return headlines
