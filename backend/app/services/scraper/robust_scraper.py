"""
Robust Instagram Comment Scraper - Production Ready

Designed to:
- Handle millions of comments patiently
- Work overnight with intelligent rate limiting
- Protect account from bans with conservative delays
- Resume from interruptions
- Save progress checkpoints
"""

import asyncio
import json
import logging
import random
import time
import aiohttp
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.config import settings

logger = logging.getLogger(__name__)


class RobustInstagramScraper:
    """
    Production-ready Instagram scraper with:
    - Exponential backoff for rate limits
    - Progress checkpoints for resume capability
    - Account protection mechanisms
    - Support for millions of comments
    """

    # Conservative rate limiting settings
    DEFAULT_CONFIG = {
        # Delays (in seconds)
        'min_delay_between_requests': 2.0,
        'max_delay_between_requests': 5.0,
        'delay_after_rate_limit': 60,  # 1 minute
        'max_delay_after_rate_limit': 900,  # 15 minutes max backoff

        # Backoff settings
        'backoff_multiplier': 2.0,
        'max_retries': 10,

        # Batch settings
        'comments_per_api_request': 50,
        'checkpoint_interval': 500,  # Save every 500 comments

        # Session protection
        'requests_before_long_pause': 100,  # Pause every 100 requests
        'long_pause_duration': 30,  # 30 second pause
        'max_requests_per_hour': 200,

        # Time limits (0 = unlimited)
        'max_scrape_time_hours': 0,  # Can run indefinitely
    }

    def __init__(
        self,
        cookies_path: Optional[Path] = None,
        checkpoint_dir: Optional[Path] = None,
        config: Optional[Dict] = None,
    ):
        self.cookies_path = cookies_path or Path(settings.sessions_dir) / "instagram_cookies.json"
        self.checkpoint_dir = checkpoint_dir or Path(settings.sessions_dir) / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._initialized = False

        # Rate limiting state
        self._request_count = 0
        self._hour_request_count = 0
        self._hour_start = time.time()
        self._current_backoff = self.config['delay_after_rate_limit']
        self._consecutive_errors = 0

    async def initialize(self) -> bool:
        """Initialize browser with saved cookies."""
        if self._initialized:
            return True

        if not self.cookies_path.exists():
            logger.error(f"Cookies file not found: {self.cookies_path}")
            logger.info("Run browser_login.py to create a session first")
            return False

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._context = await self._browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            with open(self.cookies_path, "r") as f:
                cookies = json.load(f)

            await self._context.add_cookies(cookies)
            self._initialized = True
            logger.info("Robust scraper initialized with saved session")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}")
            return False

    async def close(self):
        """Clean up resources."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._initialized = False

    async def _smart_delay(self, context: str = "request"):
        """Apply intelligent delay with jitter to appear human-like."""
        base_delay = random.uniform(
            self.config['min_delay_between_requests'],
            self.config['max_delay_between_requests']
        )

        # Add extra delay every N requests to protect account
        if self._request_count > 0 and self._request_count % self.config['requests_before_long_pause'] == 0:
            logger.info(f"Taking a longer pause after {self._request_count} requests...")
            await asyncio.sleep(self.config['long_pause_duration'])

        # Check hourly rate limit
        elapsed_hour = time.time() - self._hour_start
        if elapsed_hour >= 3600:
            self._hour_request_count = 0
            self._hour_start = time.time()
        elif self._hour_request_count >= self.config['max_requests_per_hour']:
            wait_time = 3600 - elapsed_hour + random.uniform(60, 120)
            logger.warning(f"Hourly limit reached. Waiting {wait_time/60:.1f} minutes...")
            await asyncio.sleep(wait_time)
            self._hour_request_count = 0
            self._hour_start = time.time()

        await asyncio.sleep(base_delay)
        self._request_count += 1
        self._hour_request_count += 1

    async def _handle_rate_limit(self, error_type: str = "rate_limit"):
        """Handle rate limit with exponential backoff."""
        self._consecutive_errors += 1

        # Calculate backoff with jitter
        backoff = min(
            self._current_backoff * (self.config['backoff_multiplier'] ** (self._consecutive_errors - 1)),
            self.config['max_delay_after_rate_limit']
        )
        jitter = random.uniform(0, backoff * 0.2)
        total_wait = backoff + jitter

        logger.warning(
            f"Rate limit hit ({error_type}). "
            f"Backing off for {total_wait/60:.1f} minutes "
            f"(attempt {self._consecutive_errors}/{self.config['max_retries']})"
        )

        await asyncio.sleep(total_wait)

        if self._consecutive_errors >= self.config['max_retries']:
            logger.error("Max retries exceeded. Stopping to protect account.")
            return False
        return True

    def _reset_backoff(self):
        """Reset backoff after successful request."""
        self._consecutive_errors = 0
        self._current_backoff = self.config['delay_after_rate_limit']

    def _get_checkpoint_path(self, shortcode: str) -> Path:
        """Get checkpoint file path for a post."""
        return self.checkpoint_dir / f"comments_{shortcode}.json"

    def _save_checkpoint(
        self,
        shortcode: str,
        comments: List[Dict],
        end_cursor: Optional[str],
        metadata: Dict
    ):
        """Save progress checkpoint for resume capability."""
        checkpoint = {
            'shortcode': shortcode,
            'timestamp': datetime.now().isoformat(),
            'comments_count': len(comments),
            'end_cursor': end_cursor,
            'metadata': metadata,
            'comments': comments
        }

        checkpoint_path = self._get_checkpoint_path(shortcode)
        with open(checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2, default=str)

        logger.info(f"Checkpoint saved: {len(comments)} comments")

    def _load_checkpoint(self, shortcode: str) -> Optional[Dict]:
        """Load checkpoint if exists."""
        checkpoint_path = self._get_checkpoint_path(shortcode)
        if checkpoint_path.exists():
            try:
                with open(checkpoint_path, 'r', encoding='utf-8') as f:
                    checkpoint = json.load(f)
                logger.info(f"Resuming from checkpoint: {checkpoint['comments_count']} comments")
                return checkpoint
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        return None

    async def scrape_all_comments(
        self,
        shortcode: str,
        max_comments: int = 0,  # 0 = unlimited
        resume: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Scrape ALL comments from a post with full robustness.

        Args:
            shortcode: Instagram post shortcode
            max_comments: Maximum comments (0 = unlimited, get all)
            resume: Whether to resume from checkpoint
            progress_callback: Callback(current_count, estimated_total)

        Returns:
            Dict with comments and metadata
        """
        if not self._initialized:
            if not await self.initialize():
                return {'error': 'Failed to initialize', 'comments': []}

        # Check for existing checkpoint
        all_comments = []
        end_cursor = None

        if resume:
            checkpoint = self._load_checkpoint(shortcode)
            if checkpoint:
                all_comments = checkpoint.get('comments', [])
                end_cursor = checkpoint.get('end_cursor')
                logger.info(f"Resuming with {len(all_comments)} comments")

        page = await self._context.new_page()
        start_time = time.time()

        try:
            # First, get post info and media_id
            url = f"https://www.instagram.com/p/{shortcode}/"
            logger.info(f"Fetching post: {url}")

            await page.goto(url)
            await self._smart_delay("page_load")
            await page.wait_for_timeout(3000)

            # Extract media_id and total comment count
            post_info = await page.evaluate('''
                () => {
                    const scripts = document.querySelectorAll('script');
                    let mediaId = null;
                    let commentCount = null;

                    for (const script of scripts) {
                        const text = script.textContent || '';

                        const idMatch = text.match(/"media_id":"(\\d+)"/);
                        if (idMatch) mediaId = idMatch[1];

                        const countMatch = text.match(/"comment_count":(\\d+)/);
                        if (countMatch) commentCount = parseInt(countMatch[1]);

                        if (mediaId && commentCount) break;
                    }

                    return { mediaId, commentCount };
                }
            ''')

            media_id = post_info.get('mediaId')
            total_comments = post_info.get('commentCount', 0)

            logger.info(f"Post has approximately {total_comments:,} comments")

            if not media_id:
                logger.warning("Could not find media_id, using DOM scraping fallback")
                # Fallback to DOM scraping would go here
                await page.close()
                return {'error': 'Could not get media_id', 'comments': all_comments}

            # Get cookies and tokens for API requests
            cookies = await self._context.cookies()
            cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            csrf_token = next((c['value'] for c in cookies if c['name'] == 'csrftoken'), '')

            await page.close()

            # Fetch comments via API with full robustness
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cookie': cookie_header,
                'X-CSRFToken': csrf_token,
                'X-IG-App-ID': '936619743392459',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://www.instagram.com/p/{shortcode}/',
            }

            graphql_url = "https://www.instagram.com/graphql/query/"
            query_hash = "bc3296d1ce80a24b1b6e40b1e72903f5"

            has_next = True
            batch_count = 0
            last_checkpoint_count = len(all_comments)

            async with aiohttp.ClientSession() as session:
                while has_next:
                    # Check max_comments limit
                    if max_comments > 0 and len(all_comments) >= max_comments:
                        logger.info(f"Reached max_comments limit: {max_comments}")
                        break

                    # Check time limit
                    if self.config['max_scrape_time_hours'] > 0:
                        elapsed_hours = (time.time() - start_time) / 3600
                        if elapsed_hours >= self.config['max_scrape_time_hours']:
                            logger.info(f"Reached time limit: {self.config['max_scrape_time_hours']} hours")
                            break

                    batch_count += 1

                    # Apply smart delay
                    await self._smart_delay("api_request")

                    variables = {
                        "shortcode": shortcode,
                        "first": self.config['comments_per_api_request'],
                    }
                    if end_cursor:
                        variables["after"] = end_cursor

                    params = {
                        "query_hash": query_hash,
                        "variables": json.dumps(variables)
                    }

                    try:
                        async with session.get(graphql_url, params=params, headers=headers, timeout=30) as resp:
                            if resp.status == 429:  # Rate limited
                                logger.warning("HTTP 429 - Rate limited")
                                should_continue = await self._handle_rate_limit("HTTP 429")
                                if not should_continue:
                                    break
                                continue

                            elif resp.status == 401:
                                logger.error("HTTP 401 - Session expired. Please re-login.")
                                break

                            elif resp.status != 200:
                                logger.warning(f"HTTP {resp.status}")
                                should_continue = await self._handle_rate_limit(f"HTTP {resp.status}")
                                if not should_continue:
                                    break
                                continue

                            data = await resp.json()

                            # Check for errors in response
                            if 'errors' in data:
                                logger.warning(f"API returned errors: {data['errors']}")
                                should_continue = await self._handle_rate_limit("API error")
                                if not should_continue:
                                    break
                                continue

                            # Reset backoff on success
                            self._reset_backoff()

                            # Extract comments
                            shortcode_media = data.get('data', {}).get('shortcode_media', {})
                            comments_data = shortcode_media.get('edge_media_to_parent_comment', {})

                            edges = comments_data.get('edges', [])

                            if not edges:
                                logger.info("No more comments in response")
                                has_next = False
                                break

                            for edge in edges:
                                node = edge.get('node', {})
                                owner = node.get('owner', {})

                                comment = {
                                    'id': node.get('id'),
                                    'username': owner.get('username', ''),
                                    'text': node.get('text', ''),
                                    'like_count': node.get('edge_liked_by', {}).get('count', 0),
                                    'created_at': node.get('created_at'),
                                    'is_reply': False,
                                }

                                if comment['username'] and comment['text']:
                                    all_comments.append(comment)

                                # Get replies
                                replies = node.get('edge_threaded_comments', {}).get('edges', [])
                                for reply_edge in replies:
                                    reply_node = reply_edge.get('node', {})
                                    reply_owner = reply_node.get('owner', {})
                                    reply = {
                                        'id': reply_node.get('id'),
                                        'username': reply_owner.get('username', ''),
                                        'text': reply_node.get('text', ''),
                                        'like_count': reply_node.get('edge_liked_by', {}).get('count', 0),
                                        'created_at': reply_node.get('created_at'),
                                        'is_reply': True,
                                        'parent_id': node.get('id'),
                                    }
                                    if reply['username'] and reply['text']:
                                        all_comments.append(reply)

                            # Update pagination
                            page_info = comments_data.get('page_info', {})
                            has_next = page_info.get('has_next_page', False)
                            end_cursor = page_info.get('end_cursor')

                            # Progress callback
                            if progress_callback:
                                progress_callback(len(all_comments), total_comments)

                            # Log progress
                            if batch_count % 10 == 0:
                                elapsed = time.time() - start_time
                                rate = len(all_comments) / (elapsed / 60) if elapsed > 0 else 0
                                eta = (total_comments - len(all_comments)) / rate if rate > 0 else 0
                                logger.info(
                                    f"Progress: {len(all_comments):,}/{total_comments:,} comments "
                                    f"({len(all_comments)/total_comments*100:.1f}%) "
                                    f"Rate: {rate:.0f}/min, ETA: {eta:.0f} min"
                                )

                            # Save checkpoint periodically
                            if len(all_comments) - last_checkpoint_count >= self.config['checkpoint_interval']:
                                self._save_checkpoint(
                                    shortcode, all_comments, end_cursor,
                                    {'total_expected': total_comments, 'batch_count': batch_count}
                                )
                                last_checkpoint_count = len(all_comments)

                    except asyncio.TimeoutError:
                        logger.warning("Request timeout")
                        should_continue = await self._handle_rate_limit("timeout")
                        if not should_continue:
                            break
                        continue

                    except aiohttp.ClientError as e:
                        logger.warning(f"Network error: {e}")
                        should_continue = await self._handle_rate_limit("network_error")
                        if not should_continue:
                            break
                        continue

            # Final checkpoint
            self._save_checkpoint(
                shortcode, all_comments, end_cursor,
                {'total_expected': total_comments, 'batch_count': batch_count, 'completed': not has_next}
            )

            elapsed = time.time() - start_time
            logger.info(
                f"Scraping complete: {len(all_comments):,} comments in {elapsed/60:.1f} minutes"
            )

            # Deduplicate and format
            seen_ids = set()
            unique_comments = []
            for c in all_comments:
                cid = c.get('id') or f"{c['username']}:{c['text'][:50]}"
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    unique_comments.append({
                        'username': c['username'],
                        'username_anonymized': self._anonymize(c['username']),
                        'text': c['text'][:500],
                        'like_count': c.get('like_count', 0),
                        'commented_at': c.get('created_at'),
                        'is_reply': c.get('is_reply', False),
                    })

            return {
                'shortcode': shortcode,
                'total_scraped': len(unique_comments),
                'total_expected': total_comments,
                'coverage_pct': (len(unique_comments) / total_comments * 100) if total_comments > 0 else 0,
                'scrape_time_minutes': elapsed / 60,
                'comments': unique_comments,
            }

        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            # Save checkpoint on error
            self._save_checkpoint(
                shortcode, all_comments, end_cursor,
                {'error': str(e), 'batch_count': batch_count}
            )
            return {
                'error': str(e),
                'comments': all_comments,
                'checkpoint_saved': True,
            }

    def _anonymize(self, username: str) -> str:
        """Anonymize username for privacy."""
        if not username:
            return "***"
        if len(username) <= 4:
            return username[0] + "***"
        visible = len(username) // 3
        return username[:visible] + "*" * (len(username) - 2 * visible) + username[-visible:]


async def test_robust_scraper():
    """Test the robust scraper."""
    scraper = RobustInstagramScraper()

    def progress(current, total):
        pct = (current / total * 100) if total > 0 else 0
        print(f"\rProgress: {current:,}/{total:,} ({pct:.1f}%)", end="", flush=True)

    try:
        result = await scraper.scrape_all_comments(
            "DULsWrPjwef",
            max_comments=1000,  # Limit for testing
            progress_callback=progress
        )

        print(f"\n\nResults:")
        print(f"  Total scraped: {result.get('total_scraped', 0):,}")
        print(f"  Expected: {result.get('total_expected', 0):,}")
        print(f"  Coverage: {result.get('coverage_pct', 0):.1f}%")
        print(f"  Time: {result.get('scrape_time_minutes', 0):.1f} minutes")

        # Save results
        with open('sessions/robust_scrape_results.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nResults saved to sessions/robust_scrape_results.json")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_robust_scraper())
