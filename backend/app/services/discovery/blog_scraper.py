"""
Nigerian Blog/News Scraper

Scrapes popular Nigerian entertainment blogs to discover
trending celebrities and their latest news.

Sources:
- Linda Ikeji Blog
- Bella Naija
- Pulse Nigeria
- The Net NG
- SDK News
"""

import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Known celebrity name patterns for extraction
CELEBRITY_PATTERNS = [
    # Musicians
    r'\b(Davido|David Adeleke)\b',
    r'\b(Wizkid|Ayodeji Balogun)\b',
    r'\b(Burna Boy|Damini Ogulu)\b',
    r'\b(Tiwa Savage)\b',
    r'\b(Rema|Divine Ikubor)\b',
    r'\b(Asake|Ahmed Ololade)\b',
    r'\b(Tems|Temilade Openiyi)\b',
    r'\b(Don Jazzy|Michael Collins)\b',
    r'\b(Olamide|Olamide Baddo)\b',
    r'\b(Fireboy|Fireboy DML)\b',
    r'\b(Ayra Starr)\b',
    r'\b(CKay)\b',
    r'\b(Omah Lay)\b',
    r'\b(Kizz Daniel)\b',
    r'\b(Patoranking)\b',

    # Actors
    r'\b(Funke Akindele|Jenifa)\b',
    r'\b(Toyin Abraham)\b',
    r'\b(Mercy Johnson)\b',
    r'\b(Genevieve Nnaji)\b',
    r'\b(Omotola Jalade)\b',
    r'\b(Odunlade Adekola)\b',
    r'\b(Iyabo Ojo)\b',
    r'\b(Jim Iyke)\b',

    # Comedians
    r'\b(Basketmouth)\b',
    r'\b(Mr Macaroni)\b',
    r'\b(Broda Shaggi)\b',
    r'\b(Sabinus|Mr Funny)\b',
    r'\b(Taaooma)\b',
    r'\b(Lasisi Elenu)\b',

    # Influencers/Reality TV
    r'\b(Tacha|Natacha Akide)\b',
    r'\b(Mercy Eke)\b',
    r'\b(Laycon)\b',
    r'\b(Erica Nlewedim)\b',
    r'\b(Nengi)\b',
    r'\b(DJ Cuppy|Florence Otedola)\b',
    r'\b(Toke Makinwa)\b',
]


class BlogScraper:
    """
    Scrapes Nigerian entertainment blogs for celebrity news.
    """

    SOURCES = [
        {
            "name": "Linda Ikeji",
            "url": "https://www.lindaikejisblog.com/",
            "category_urls": [
                "https://www.lindaikejisblog.com/category/entertainment",
                "https://www.lindaikejisblog.com/category/gist",
            ],
            "selectors": {
                "articles": ".post, .blog-post, article",
                "title": "h2 a, h3 a, .post-title a",
                "link": "h2 a, h3 a, .post-title a",
                "snippet": ".post-content, .entry-content, p",
            }
        },
        {
            "name": "Bella Naija",
            "url": "https://www.bellanaija.com/",
            "category_urls": [
                "https://www.bellanaija.com/category/entertainment/",
                "https://www.bellanaija.com/category/bn-music/",
            ],
            "selectors": {
                "articles": "article, .post-item",
                "title": "h2 a, h3 a, .entry-title a",
                "link": "h2 a, h3 a, .entry-title a",
                "snippet": ".entry-summary, .excerpt, p",
            }
        },
        {
            "name": "Pulse Nigeria",
            "url": "https://www.pulse.ng/",
            "category_urls": [
                "https://www.pulse.ng/entertainment/",
                "https://www.pulse.ng/entertainment/celebrities/",
            ],
            "selectors": {
                "articles": "article, .article-card",
                "title": "h2 a, h3 a, .title a",
                "link": "h2 a, h3 a, .title a, a.article-link",
                "snippet": ".summary, .excerpt, p",
            }
        },
        {
            "name": "The Net NG",
            "url": "https://thenet.ng/",
            "category_urls": [
                "https://thenet.ng/category/entertainment/",
                "https://thenet.ng/category/music/",
            ],
            "selectors": {
                "articles": "article, .post",
                "title": "h2 a, h3 a",
                "link": "h2 a, h3 a",
                "snippet": ".entry-content p, .excerpt",
            }
        },
    ]

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.discovered_celebrities: Dict[str, Dict] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def scrape_source(self, source: Dict) -> List[Dict[str, Any]]:
        """Scrape articles from a single blog source."""
        articles = []
        session = await self._get_session()

        for url in source.get("category_urls", [source["url"]]):
            try:
                async with session.get(url, timeout=15) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to fetch {url}: {response.status}")
                        continue

                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')

                    # Find articles
                    selectors = source.get("selectors", {})
                    article_elements = soup.select(selectors.get("articles", "article"))

                    for article in article_elements[:20]:  # Limit per page
                        try:
                            # Get title
                            title_el = article.select_one(selectors.get("title", "h2 a"))
                            title = title_el.get_text(strip=True) if title_el else ""

                            # Get link
                            link_el = article.select_one(selectors.get("link", "a"))
                            link = link_el.get("href", "") if link_el else ""
                            if link and not link.startswith("http"):
                                link = urljoin(source["url"], link)

                            # Get snippet
                            snippet_el = article.select_one(selectors.get("snippet", "p"))
                            snippet = snippet_el.get_text(strip=True)[:300] if snippet_el else ""

                            if title:
                                articles.append({
                                    "title": title,
                                    "link": link,
                                    "snippet": snippet,
                                    "source": source["name"],
                                    "scraped_at": datetime.utcnow().isoformat()
                                })
                        except Exception as e:
                            logger.debug(f"Error parsing article: {e}")
                            continue

            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching {url}")
            except Exception as e:
                logger.warning(f"Error scraping {url}: {e}")

        return articles

    def extract_celebrities_from_articles(
        self,
        articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract celebrity mentions from article titles and snippets."""
        celebrity_mentions = {}

        for article in articles:
            text = f"{article.get('title', '')} {article.get('snippet', '')}"

            for pattern in CELEBRITY_PATTERNS:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Normalize name
                    name = match.strip().title()

                    if name not in celebrity_mentions:
                        celebrity_mentions[name] = {
                            "name": name,
                            "mention_count": 0,
                            "articles": [],
                            "sources": set(),
                            "first_seen": datetime.utcnow().isoformat()
                        }

                    celebrity_mentions[name]["mention_count"] += 1
                    celebrity_mentions[name]["sources"].add(article.get("source", "unknown"))

                    # Keep top 3 articles per celebrity
                    if len(celebrity_mentions[name]["articles"]) < 3:
                        celebrity_mentions[name]["articles"].append({
                            "title": article.get("title", ""),
                            "link": article.get("link", ""),
                            "source": article.get("source", "")
                        })

        # Convert to list and sort by mention count
        result = []
        for name, data in celebrity_mentions.items():
            data["sources"] = list(data["sources"])
            data["confidence"] = min(0.5 + (data["mention_count"] * 0.1), 1.0)
            result.append(data)

        result.sort(key=lambda x: x["mention_count"], reverse=True)
        return result

    async def discover_from_blogs(self) -> List[Dict[str, Any]]:
        """
        Scrape all blog sources and extract trending celebrities.
        """
        logger.info("Starting blog scraper discovery...")

        all_articles = []

        # Scrape all sources in parallel
        tasks = [self.scrape_source(source) for source in self.SOURCES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Blog source failed: {result}")

        logger.info(f"Scraped {len(all_articles)} articles from {len(self.SOURCES)} sources")

        # Extract celebrity mentions
        celebrities = self.extract_celebrities_from_articles(all_articles)

        logger.info(f"Extracted {len(celebrities)} celebrities from articles")

        return celebrities

    async def get_celebrity_news(self, celebrity_name: str) -> List[Dict[str, Any]]:
        """
        Get recent news articles about a specific celebrity.
        """
        all_articles = []

        for source in self.SOURCES:
            articles = await self.scrape_source(source)
            all_articles.extend(articles)

        # Filter articles mentioning this celebrity
        name_lower = celebrity_name.lower()
        relevant = []

        for article in all_articles:
            text = f"{article.get('title', '')} {article.get('snippet', '')}".lower()
            if name_lower in text:
                relevant.append(article)

        return relevant[:10]  # Top 10 articles


async def run_blog_discovery():
    """
    Run blog scraping discovery job.
    """
    scraper = BlogScraper()

    try:
        celebrities = await scraper.discover_from_blogs()

        # Get top trending
        top_trending = celebrities[:20]

        return {
            "total_discovered": len(celebrities),
            "top_trending": top_trending,
            "sources_scraped": len(BlogScraper.SOURCES)
        }

    finally:
        await scraper.close()


if __name__ == "__main__":
    async def test():
        result = await run_blog_discovery()
        print(f"Blog discovery result:")
        print(f"Total: {result['total_discovered']}")
        print(f"\nTop trending:")
        for celeb in result['top_trending'][:10]:
            print(f"  - {celeb['name']}: {celeb['mention_count']} mentions")

    asyncio.run(test())
