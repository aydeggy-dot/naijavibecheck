"""Test fetching comments using browser session - targeted extraction."""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def fetch_comments():
    print("Loading saved cookies and fetching comments...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()

        with open("sessions/instagram_cookies.json", "r") as f:
            cookies = json.load(f)

        await context.add_cookies(cookies)
        page = await context.new_page()

        print("\nFetching post...")
        await page.goto("https://www.instagram.com/p/DULsWrPjwef/")
        await page.wait_for_timeout(6000)

        # Take screenshot
        await page.screenshot(path="sessions/final_screenshot.png", full_page=True)

        # Debug: Check what's on the page
        page_info = await page.evaluate('''
            () => {
                return {
                    url: window.location.href,
                    title: document.title,
                    hasArticle: !!document.querySelector('article'),
                    mainTags: Array.from(document.querySelectorAll('main, article, section, div[role="main"]')).map(el => el.tagName),
                    bodyClasses: document.body.className,
                    firstDivs: Array.from(document.querySelectorAll('div')).slice(0, 5).map(d => d.className?.substring(0, 50))
                };
            }
        ''')
        print(f"Page info: {page_info}")

        # Get comments using specific selectors
        print("\nExtracting comments via DOM...")

        # First, let's debug what's on the page
        debug_info = await page.evaluate('''
            () => {
                const container = document.querySelector('main') || document.body;

                // Find the first comment username (not davido)
                let targetLink = null;
                container.querySelectorAll('a[href^="/"]').forEach(link => {
                    if (targetLink) return;
                    const href = link.getAttribute('href');
                    if (href === '/bredhkn/' && link.innerText?.trim() === 'bredhkn') {
                        targetLink = link;
                    }
                });

                if (!targetLink) {
                    return { error: 'Could not find bredhkn link' };
                }

                // Walk up parents and capture their text
                const parentInfo = [];
                let el = targetLink;
                for (let i = 0; i < 10 && el; i++) {
                    parentInfo.push({
                        depth: i,
                        tag: el.tagName,
                        className: el.className?.substring(0, 50),
                        text: el.innerText?.substring(0, 200)
                    });
                    el = el.parentElement;
                }

                return { parentInfo };
            }
        ''')
        debug_str = json.dumps(debug_info, indent=2, ensure_ascii=True)
        print(f"Debug: {debug_str}")

        comments = await page.evaluate('''
            () => {
                const results = [];
                const seenComments = new Set();
                const processedUsers = new Set();

                const container = document.querySelector('main') || document.body;

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
                                     'api', 'privacy', 'terms', 'locations', 'hashtag', 'davido'];
                    if (skipList.includes(username.toLowerCase())) return;

                    // Skip if we already processed this user (avoid dupes from multiple links)
                    const userKey = username;
                    if (processedUsers.has(userKey)) return;
                    processedUsers.add(userKey);

                    // Walk up to find the comment container (depth 6-8 based on debug)
                    let el = link.parentElement;
                    let bestText = '';

                    for (let depth = 0; depth < 10 && el; depth++) {
                        const fullText = el.innerText || '';

                        // Split by newlines and filter out empty/whitespace-only lines
                        const lines = fullText.split('\\n')
                            .map(l => l.trim())
                            .filter(l => l && l !== '\\u00a0' && l !== ' ');

                        // Pattern: username, (optional verified badge), time (8h), comment text, likes, Reply
                        // We need to find lines AFTER username and time but BEFORE likes/Reply

                        let foundTime = false;
                        for (let i = 0; i < lines.length; i++) {
                            const line = lines[i];

                            // Skip username
                            if (line === username) continue;

                            // Skip time indicators (marks when comment section starts)
                            if (/^\\d+[hdwms]$/.test(line)) {
                                foundTime = true;
                                continue;
                            }

                            // Stop at likes/Reply
                            if (/^\\d+[,\\d]* likes?$/i.test(line)) break;
                            if (line === 'Reply') break;
                            if (/^View all/i.test(line)) break;

                            // After we've seen the time, the next valid line is the comment
                            if (foundTime && line.length >= 2 && line.length <= 500) {
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

        # Filter and clean
        final = []
        seen_texts = set()

        for c in comments:
            # Skip post author and UI elements
            if c['username'].lower() in ['davido', 'home', 'reels', 'explore']:
                continue

            # Skip duplicates
            if c['text'] in seen_texts:
                continue
            seen_texts.add(c['text'])

            final.append({
                'username': c['username'],
                'text': c['text']
            })

        print(f"\n Found {len(final)} comments:\n")
        for i, c in enumerate(final[:20]):
            text = c['text'][:70].encode('ascii', 'ignore').decode()
            print(f"{i+1}. @{c['username']}: {text}")

        # Save
        with open('sessions/sample_comments.json', 'w', encoding='utf-8') as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"\n Saved {len(final)} comments to sessions/sample_comments.json")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_comments())
