"""Browser-based Instagram scraper using Playwright for comments."""
import asyncio
import json
import re
import logging
import aiohttp
from pathlib import Path
from typing import List, Dict, Any, Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from app.config import settings

logger = logging.getLogger(__name__)

# Instagram GraphQL endpoint for comments
GRAPHQL_URL = "https://www.instagram.com/graphql/query/"
COMMENTS_QUERY_HASH = "bc3296d1ce80a24b1b6e40b1e72903f5"  # May need updating


class BrowserScraper:
    """
    Browser-based scraper for Instagram comments.
    Uses Playwright to render pages and extract comments that require login.
    """

    def __init__(self, cookies_path: Optional[Path] = None):
        self.cookies_path = cookies_path or Path(settings.sessions_dir) / "instagram_cookies.json"
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize browser with saved cookies."""
        if self._initialized:
            return True

        if not self.cookies_path.exists():
            logger.warning(f"Cookies file not found: {self.cookies_path}")
            logger.info("Run browser_login.py to create a session first")
            return False

        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._context = await self._browser.new_context()

            # Load cookies
            with open(self.cookies_path, "r") as f:
                cookies = json.load(f)

            await self._context.add_cookies(cookies)
            self._initialized = True
            logger.info("Browser scraper initialized with saved session")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize browser scraper: {e}")
            return False

    async def close(self):
        """Close browser."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._playwright = None
        self._initialized = False

    async def get_post_comments(
        self,
        shortcode: str,
        max_comments: int = 5000,
        max_scroll_time: int = 300,
        progress_callback=None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch ALL comments from a post using browser rendering.

        Args:
            shortcode: Instagram post shortcode
            max_comments: Maximum comments to extract (default 5000)
            max_scroll_time: Maximum seconds to spend scrolling (default 5 minutes)
            progress_callback: Optional callback(count) to report progress

        Returns:
            List of comment dicts with username, text, etc.
        """
        if not self._initialized:
            if not await self.initialize():
                return []

        page = await self._context.new_page()

        try:
            url = f"https://www.instagram.com/p/{shortcode}/"
            logger.info(f"Fetching ALL comments from {url}")

            await page.goto(url)
            await page.wait_for_timeout(4000)

            # Click "View all X comments" to load the comments modal
            try:
                view_all_btn = await page.query_selector('span:has-text("View all")')
                if view_all_btn:
                    await view_all_btn.click()
                    logger.info("Clicked 'View all comments'")
                    await page.wait_for_timeout(3000)
            except Exception as e:
                logger.debug(f"No 'View all comments' button: {e}")

            # Continuously scroll until no more comments load
            import time
            start_time = time.time()
            last_count = 0
            no_change_count = 0
            scroll_iteration = 0
            collected_comments = []

            # Set up request interception to capture Instagram's API responses
            api_comments = []

            async def handle_response(response):
                if 'graphql' in response.url or 'api/v1' in response.url:
                    try:
                        if response.status == 200:
                            data = await response.json()
                            # Extract comments from API response
                            self._extract_api_comments(data, api_comments)
                    except:
                        pass

            page.on('response', handle_response)

            while True:
                scroll_iteration += 1
                elapsed = time.time() - start_time

                # Check time limit
                if elapsed > max_scroll_time:
                    logger.info(f"Reached time limit ({max_scroll_time}s)")
                    break

                # Scroll using multiple strategies
                current_count = await page.evaluate('''
                    () => {
                        const main = document.querySelector('main');
                        if (!main) return 0;

                        // Strategy 1: Find the specific comments scrollable area
                        // Instagram uses a div with specific classes for the comment section
                        let scrolled = false;

                        // Look for scrollable divs
                        const allDivs = Array.from(main.querySelectorAll('div'));
                        // Sort by scroll height to find the main comments container
                        const scrollables = allDivs.filter(div => {
                            const style = window.getComputedStyle(div);
                            return (style.overflowY === 'scroll' || style.overflowY === 'auto') &&
                                   div.scrollHeight > div.clientHeight + 50;
                        }).sort((a, b) => b.scrollHeight - a.scrollHeight);

                        if (scrollables.length > 0) {
                            // Scroll the largest scrollable container
                            const container = scrollables[0];
                            container.scrollTop = container.scrollHeight;
                            scrolled = true;
                        }

                        if (!scrolled) {
                            window.scrollTo(0, document.body.scrollHeight);
                        }

                        // Count username links
                        const links = main.querySelectorAll('a[href^="/"]');
                        let count = 0;
                        const seen = new Set();
                        links.forEach(link => {
                            const href = link.getAttribute('href');
                            if (href && href.match(/^\\/[a-zA-Z0-9._]+\\/$/) &&
                                !['home', 'explore', 'reels', 'direct', 'p', 'accounts'].includes(href.slice(1, -1))) {
                                if (!seen.has(href)) {
                                    seen.add(href);
                                    count++;
                                }
                            }
                        });
                        return count;
                    }
                ''')

                # Report progress
                total_found = max(current_count, len(api_comments))
                if progress_callback:
                    progress_callback(total_found)

                if scroll_iteration % 10 == 0:
                    logger.info(f"Scroll {scroll_iteration}: ~{current_count} DOM / {len(api_comments)} API ({elapsed:.0f}s)")

                # Check if we've stopped getting new comments
                if current_count == last_count:
                    no_change_count += 1
                    if no_change_count >= 8:  # Increased threshold
                        logger.info(f"No new comments after {no_change_count} scrolls")
                        break
                else:
                    no_change_count = 0

                last_count = current_count

                # Check max comments limit
                if total_found >= max_comments:
                    logger.info(f"Reached max comments limit ({max_comments})")
                    break

                # Wait for content to load
                await page.wait_for_timeout(800)

                # Periodically click "Load more" and "View replies" buttons
                if scroll_iteration % 3 == 0:
                    await page.evaluate('''
                        () => {
                            document.querySelectorAll('span, button, div[role="button"]').forEach(el => {
                                const text = el.innerText?.toLowerCase() || '';
                                if ((text.includes('view') || text.includes('load')) &&
                                    (text.includes('replies') || text.includes('more') || text.includes('comment'))) {
                                    try { el.click(); } catch(e) {}
                                }
                            });
                        }
                    ''')
                    await page.wait_for_timeout(300)

            page.remove_listener('response', handle_response)
            logger.info(f"Finished: {scroll_iteration} scrolls, {time.time() - start_time:.0f}s, API captured: {len(api_comments)}")

            # Extract comments using JavaScript that targets the comment section
            comments = await page.evaluate('''
                () => {
                    const results = [];
                    const seenComments = new Set();
                    const processedUsers = new Set();

                    // Instagram uses main/section instead of article
                    const container = document.querySelector('main') || document.querySelector('article') || document.body;

                    // Strategy: Find all username links and get text from their parent containers
                    container.querySelectorAll('a[href^="/"]').forEach(link => {
                        const href = link.getAttribute('href');
                        const match = href?.match(/^\\/([a-zA-Z0-9._]+)\\/$/);
                        if (!match) return;

                        const username = match[1];

                        // Skip known non-usernames and post author
                        const skipList = ['home', 'reels', 'messages', 'search', 'explore',
                                         'notifications', 'create', 'profile', 'more', 'direct',
                                         'p', 'accounts', 'about', 'blog', 'jobs', 'help',
                                         'api', 'privacy', 'terms', 'locations', 'hashtag'];
                        if (skipList.includes(username.toLowerCase())) return;

                        // Skip if we already processed this user (avoid dupes from multiple links)
                        const userKey = username;
                        if (processedUsers.has(userKey)) return;
                        processedUsers.add(userKey);

                        // Walk up to find the comment container
                        let el = link.parentElement;
                        let bestText = '';

                        for (let depth = 0; depth < 10 && el; depth++) {
                            const fullText = el.innerText || '';

                            // Split by newlines and filter out empty/whitespace-only lines
                            const lines = fullText.split('\\n')
                                .map(l => l.trim())
                                .filter(l => l && l !== '\\u00a0' && l !== ' ');

                            // Pattern: username, time (8h), comment text, likes, Reply
                            // Find lines AFTER username and time but BEFORE likes/Reply
                            let foundTime = false;
                            for (let i = 0; i < lines.length; i++) {
                                const line = lines[i];

                                // Skip username
                                if (line === username) continue;

                                // Skip time indicators
                                if (/^\\d+[hdwms]$/.test(line)) {
                                    foundTime = true;
                                    continue;
                                }

                                // Stop at likes/Reply
                                if (/^\\d+[,\\d]* likes?$/i.test(line)) break;
                                if (line === 'Reply') break;
                                if (/^View all/i.test(line)) break;

                                // After time, the next valid line is the comment
                                if (foundTime && line.length >= 1 && line.length <= 500) {
                                    bestText = line;
                                    break;
                                }
                            }

                            if (bestText) break;
                            el = el.parentElement;
                        }

                        if (bestText) {
                            const key = username + ':' + bestText.substring(0, 50);
                            if (!seenComments.has(key)) {
                                seenComments.add(key);
                                results.push({
                                    username: username,
                                    text: bestText.substring(0, 300)
                                });
                            }
                        }
                    });

                    return results;
                }
            ''')

            # Get post author to exclude from comments
            post_author = await page.evaluate('''
                () => {
                    // The first username link in the post header is the author
                    const main = document.querySelector('main');
                    if (!main) return null;
                    const firstLink = main.querySelector('a[href^="/"][href$="/"]');
                    if (firstLink) {
                        const href = firstLink.getAttribute('href');
                        const match = href?.match(/^\\/([a-zA-Z0-9._]+)\\/$/);
                        return match ? match[1].toLowerCase() : null;
                    }
                    return null;
                }
            ''')
            logger.debug(f"Detected post author: {post_author}")

            # Filter and deduplicate
            final_comments = []
            seen = set()

            for c in comments:
                username = c.get('username', '')
                text = c.get('text', '')

                # Skip post author caption, UI elements
                skip_users = ['instagram']
                if post_author:
                    skip_users.append(post_author)
                if username.lower() in skip_users:
                    continue

                # Skip short or duplicate
                if len(text) < 3:
                    continue

                key = f"{username}:{text[:30]}"
                if key in seen:
                    continue
                seen.add(key)

                final_comments.append({
                    'username': username,
                    'username_anonymized': self._anonymize(username),
                    'text': text[:300],
                    'like_count': 0,
                    'commented_at': None,
                    'is_reply': False,
                })

            logger.info(f"Extracted {len(final_comments)} comments from {shortcode}")
            return final_comments[:max_comments]

        except Exception as e:
            logger.error(f"Error fetching comments for {shortcode}: {e}")
            return []

        finally:
            await page.close()

    def _anonymize(self, username: str) -> str:
        """Anonymize username."""
        if not username:
            return "***"
        if len(username) <= 4:
            return username[0] + "***"
        visible = len(username) // 3
        return username[:visible] + "*" * (len(username) - 2 * visible) + username[-visible:]

    async def get_all_comments_via_api(
        self,
        shortcode: str,
        max_comments: int = 10000,
        progress_callback=None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch ALL comments using Instagram's GraphQL API directly.
        Much faster than browser scrolling for large comment counts.

        Args:
            shortcode: Instagram post shortcode
            max_comments: Maximum comments to fetch
            progress_callback: Optional callback(count) for progress

        Returns:
            List of comment dicts
        """
        if not self._initialized:
            if not await self.initialize():
                return []

        page = await self._context.new_page()
        all_comments = []

        try:
            # First, load the post page to get necessary tokens and media_id
            url = f"https://www.instagram.com/p/{shortcode}/"
            logger.info(f"Loading post to get media ID: {url}")

            await page.goto(url)
            await page.wait_for_timeout(3000)

            # Extract media_id from page source
            media_id = await page.evaluate('''
                () => {
                    // Try to find media_id in page scripts
                    const scripts = document.querySelectorAll('script');
                    for (const script of scripts) {
                        const text = script.textContent || '';
                        // Look for media_id pattern
                        const match = text.match(/"media_id":"(\\d+)"/);
                        if (match) return match[1];
                        // Alternative pattern
                        const match2 = text.match(/"pk":"(\\d+)"/);
                        if (match2) return match2[1];
                    }
                    return null;
                }
            ''')

            if not media_id:
                logger.warning("Could not find media_id, falling back to DOM scraping")
                await page.close()
                return await self.get_post_comments(shortcode, max_comments)

            logger.info(f"Found media_id: {media_id}")

            # Get cookies for API requests
            cookies = await self._context.cookies()
            cookie_header = "; ".join([f"{c['name']}={c['value']}" for c in cookies])

            # Get CSRF token
            csrf_token = next((c['value'] for c in cookies if c['name'] == 'csrftoken'), '')

            # Close browser page, we'll use direct HTTP requests now
            await page.close()

            # Fetch comments via API
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

            end_cursor = None
            has_next = True
            batch_count = 0

            async with aiohttp.ClientSession() as session:
                while has_next and len(all_comments) < max_comments:
                    batch_count += 1

                    # Build GraphQL variables
                    variables = {
                        "shortcode": shortcode,
                        "first": 50,  # Comments per request
                    }
                    if end_cursor:
                        variables["after"] = end_cursor

                    params = {
                        "query_hash": COMMENTS_QUERY_HASH,
                        "variables": json.dumps(variables)
                    }

                    try:
                        async with session.get(GRAPHQL_URL, params=params, headers=headers) as resp:
                            if resp.status == 429:  # Rate limited
                                logger.warning("Rate limited, waiting 30 seconds...")
                                await asyncio.sleep(30)
                                continue
                            elif resp.status != 200:
                                logger.warning(f"API returned {resp.status}")
                                # Try waiting and retrying once
                                await asyncio.sleep(5)
                                async with session.get(GRAPHQL_URL, params=params, headers=headers) as retry_resp:
                                    if retry_resp.status != 200:
                                        logger.warning(f"Retry also failed with {retry_resp.status}")
                                        break
                                    data = await retry_resp.json()
                            else:
                                data = await resp.json()

                            # Extract comments from response
                            shortcode_media = data.get('data', {}).get('shortcode_media', {})
                            comments_data = shortcode_media.get('edge_media_to_parent_comment', {})

                            edges = comments_data.get('edges', [])
                            for edge in edges:
                                node = edge.get('node', {})
                                owner = node.get('owner', {})

                                comment = {
                                    'username': owner.get('username', ''),
                                    'text': node.get('text', ''),
                                    'like_count': node.get('edge_liked_by', {}).get('count', 0),
                                    'created_at': node.get('created_at'),
                                }

                                if comment['username'] and comment['text']:
                                    all_comments.append(comment)

                                # Also get replies if available
                                replies = node.get('edge_threaded_comments', {}).get('edges', [])
                                for reply_edge in replies:
                                    reply_node = reply_edge.get('node', {})
                                    reply_owner = reply_node.get('owner', {})
                                    reply = {
                                        'username': reply_owner.get('username', ''),
                                        'text': reply_node.get('text', ''),
                                        'like_count': reply_node.get('edge_liked_by', {}).get('count', 0),
                                        'is_reply': True,
                                    }
                                    if reply['username'] and reply['text']:
                                        all_comments.append(reply)

                            # Check for next page
                            page_info = comments_data.get('page_info', {})
                            has_next = page_info.get('has_next_page', False)
                            end_cursor = page_info.get('end_cursor')

                            if progress_callback:
                                progress_callback(len(all_comments))

                            if batch_count % 5 == 0:
                                logger.info(f"Fetched {len(all_comments)} comments (batch {batch_count})")

                            # Rate limiting - be gentle to avoid blocks
                            delay = 1.0 if batch_count < 20 else 2.0 if batch_count < 50 else 3.0
                            await asyncio.sleep(delay)

                    except Exception as e:
                        logger.error(f"Error fetching comments batch: {e}")
                        break

            logger.info(f"Total comments fetched via API: {len(all_comments)}")

            # Format comments with anonymization
            formatted_comments = []
            seen = set()
            for c in all_comments:
                key = f"{c['username']}:{c['text'][:50]}"
                if key in seen:
                    continue
                seen.add(key)

                formatted_comments.append({
                    'username': c['username'],
                    'username_anonymized': self._anonymize(c['username']),
                    'text': c['text'][:300],
                    'like_count': c.get('like_count', 0),
                    'commented_at': c.get('created_at'),
                    'is_reply': c.get('is_reply', False),
                })

            return formatted_comments[:max_comments]

        except Exception as e:
            logger.error(f"Error in API comment fetch: {e}")
            return []

    def _extract_api_comments(self, data: dict, comments_list: list) -> None:
        """Recursively extract comments from Instagram API response."""
        if isinstance(data, dict):
            # Check for comment-like structures
            if 'text' in data and 'user' in data:
                user = data.get('user', {})
                username = user.get('username', '')
                text = data.get('text', '')
                if username and text:
                    comments_list.append({
                        'username': username,
                        'text': text,
                        'pk': data.get('pk', ''),
                    })

            # Check for edges (GraphQL format)
            if 'edges' in data:
                for edge in data['edges']:
                    node = edge.get('node', {})
                    if 'text' in node:
                        owner = node.get('owner', {})
                        username = owner.get('username', '')
                        text = node.get('text', '')
                        if username and text:
                            comments_list.append({
                                'username': username,
                                'text': text,
                                'pk': node.get('id', ''),
                            })

            # Recurse into nested structures
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._extract_api_comments(value, comments_list)

        elif isinstance(data, list):
            for item in data:
                self._extract_api_comments(item, comments_list)


async def test_browser_scraper():
    """Test the browser scraper."""
    scraper = BrowserScraper()

    try:
        if await scraper.initialize():
            # Progress callback
            def progress(count):
                print(f"\rLoading comments: {count}...", end="", flush=True)

            print("Trying API method (can fetch thousands of comments)...")

            # Try API method - fetch up to 10000 comments
            comments = await scraper.get_all_comments_via_api(
                "DULsWrPjwef",
                max_comments=10000,
                progress_callback=progress
            )

            # Fall back to DOM scraping if API fails
            if len(comments) < 50:
                print("\nAPI method returned few comments, trying DOM scraping...")
                comments = await scraper.get_post_comments(
                    "DULsWrPjwef",
                    max_comments=2000,
                    max_scroll_time=120,
                    progress_callback=progress
                )

            print()  # New line after progress

            print(f"\nFound {len(comments)} comments:\n")
            for i, c in enumerate(comments[:15]):
                text = c['text'][:60].encode('ascii', 'ignore').decode()
                print(f"{i+1}. @{c['username']}: {text}")

            # Save for verification
            with open("sessions/browser_comments.json", "w", encoding="utf-8") as f:
                json.dump(comments, f, indent=2, ensure_ascii=False)
            print(f"\nSaved to sessions/browser_comments.json")
        else:
            print("Failed to initialize - run browser_login.py first")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(test_browser_scraper())
