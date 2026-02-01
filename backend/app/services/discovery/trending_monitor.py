"""
Trending Hashtag Monitor

Monitors Twitter/X and other platforms for trending Nigerian topics
to automatically discover celebrities worth tracking.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import aiohttp

logger = logging.getLogger(__name__)


# Known Nigerian celebrities for matching
KNOWN_CELEBRITIES = {
    # Musicians
    "davido", "wizkid", "burna boy", "burnaboy", "tiwa savage", "rema",
    "asake", "ckay", "fireboy", "joeboy", "omah lay", "tems", "ayra starr",
    "don jazzy", "olamide", "phyno", "flavour", "tekno", "kizz daniel",
    "patoranking", "yemi alade", "simi", "adekunle gold", "wande coal",
    "banky w", "2baba", "psquare", "ruger", "bnxn", "seyi vibez",

    # Actors/Nollywood
    "funke akindele", "toyin abraham", "mercy johnson", "omotola jalade",
    "genevieve nnaji", "ramsey nouah", "richard mofe damijo", "rmd",
    "iyabo ojo", "odunlade adekola", "femi adebayo", "kunle afolayan",
    "jim iyke", "nkem owoh", "patience ozokwor", "chiwetalu agu",
    "pete edochie", "olu jacobs", "joke silva", "sola sobowale",

    # Comedians
    "basketmouth", "ay comedian", "bovi", "i go dye", "gordons",
    "mc shakara", "mr macaroni", "lasisi elenu", "broda shaggi",
    "mark angel", "emmanuella", "sabinus", "josh2funny", "taaooma",

    # Influencers/Media
    "toke makinwa", "toolz", "ebuka", "daddy freeze", "linda ikeji",
    "laura ikeji", "temi otedola", "dj cuppy", "alex unusual",
    "tacha", "mercy eke", "laycon", "nengi", "erica nlewedim",
    "pere", "whitemoney", "liquorose", "cross", "angel smith",

    # Sports
    "victor osimhen", "osimhen", "sadiq umar", "wilfred ndidi",
    "kelechi iheanacho", "alex iwobi", "victor moses", "odion ighalo",
    "asisat oshoala", "rasheedat ajibade",

    # Politicians/Public figures (for news tracking)
    "peter obi", "tinubu", "atiku", "osinbajo",
}

# Nigerian slang/context that indicates celebrity discussion
CELEBRITY_INDICATORS = [
    r'\b(goat|legend|king|queen|icon)\b',
    r'\b(singer|artist|actor|actress|comedian|influencer)\b',
    r'\b(nollywood|afrobeats|naija)\b',
    r'@\w+',  # Instagram/Twitter handles
    r'#\w+',  # Hashtags
]


class TrendingMonitor:
    """
    Monitors trending topics to discover celebrities.

    Sources:
    - Twitter/X trending topics for Nigeria
    - Google Trends Nigeria
    - Instagram trending hashtags
    """

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.discovered_celebrities: Set[str] = set()

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def get_twitter_trends_nigeria(self) -> List[Dict[str, Any]]:
        """
        Get trending topics from Twitter/X for Nigeria.

        Note: Twitter API requires authentication. This uses alternative methods.
        """
        trends = []

        try:
            # Method 1: Use unofficial trends endpoint
            session = await self._get_session()

            # Nigeria WOEID is 23424908
            # We'll scrape from trend aggregator sites instead of direct API
            aggregator_urls = [
                "https://getdaytrends.com/nigeria/",
                "https://trends24.in/nigeria/",
            ]

            for url in aggregator_urls:
                try:
                    async with session.get(url, timeout=10) as response:
                        if response.status == 200:
                            html = await response.text()
                            # Extract trends from HTML
                            extracted = self._extract_trends_from_html(html)
                            trends.extend(extracted)
                            if trends:
                                break
                except Exception as e:
                    logger.warning(f"Failed to fetch from {url}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Twitter trends fetch failed: {e}")

        return trends[:50]  # Top 50 trends

    def _extract_trends_from_html(self, html: str) -> List[Dict[str, Any]]:
        """Extract trending topics from HTML."""
        trends = []

        # Pattern to match hashtags and trending topics
        hashtag_pattern = r'#([A-Za-z0-9_]+)'
        topic_pattern = r'<a[^>]*class="[^"]*trend[^"]*"[^>]*>([^<]+)</a>'

        # Extract hashtags
        hashtags = re.findall(hashtag_pattern, html)
        for tag in hashtags[:30]:
            if len(tag) > 2:  # Skip very short tags
                trends.append({
                    "name": f"#{tag}",
                    "type": "hashtag",
                    "source": "twitter"
                })

        # Extract topic names
        topics = re.findall(topic_pattern, html, re.IGNORECASE)
        for topic in topics[:20]:
            topic = topic.strip()
            if len(topic) > 2:
                trends.append({
                    "name": topic,
                    "type": "topic",
                    "source": "twitter"
                })

        return trends

    async def get_google_trends_nigeria(self) -> List[Dict[str, Any]]:
        """
        Get trending searches from Google Trends Nigeria.
        """
        trends = []

        try:
            session = await self._get_session()

            # Google Trends RSS feed for Nigeria
            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=NG"

            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    xml = await response.text()
                    # Extract titles from RSS
                    title_pattern = r'<title>([^<]+)</title>'
                    titles = re.findall(title_pattern, xml)

                    for title in titles[1:]:  # Skip the feed title
                        if title and len(title) > 2:
                            trends.append({
                                "name": title,
                                "type": "search",
                                "source": "google"
                            })

        except Exception as e:
            logger.warning(f"Google trends fetch failed: {e}")

        return trends[:30]

    def extract_celebrity_mentions(self, trends: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract celebrity names from trending topics.
        """
        discovered = []

        for trend in trends:
            name = trend.get("name", "").lower()

            # Check against known celebrities
            for celeb in KNOWN_CELEBRITIES:
                if celeb in name or name in celeb:
                    # Found a match
                    discovered.append({
                        "name": celeb.title(),
                        "trend": trend["name"],
                        "source": trend.get("source", "unknown"),
                        "confidence": 0.9 if celeb == name else 0.7,
                        "discovered_at": datetime.utcnow().isoformat()
                    })
                    break

            # Check for celebrity indicators
            for pattern in CELEBRITY_INDICATORS:
                if re.search(pattern, name, re.IGNORECASE):
                    # Might be a celebrity discussion
                    discovered.append({
                        "name": trend["name"],
                        "trend": trend["name"],
                        "source": trend.get("source", "unknown"),
                        "confidence": 0.5,  # Lower confidence, needs verification
                        "discovered_at": datetime.utcnow().isoformat(),
                        "needs_verification": True
                    })
                    break

        return discovered

    async def discover_trending_celebrities(self) -> List[Dict[str, Any]]:
        """
        Main method to discover trending celebrities.

        Returns list of discovered celebrities with confidence scores.
        """
        logger.info("Starting trending celebrity discovery...")

        all_trends = []

        # Gather trends from multiple sources in parallel
        twitter_task = self.get_twitter_trends_nigeria()
        google_task = self.get_google_trends_nigeria()

        results = await asyncio.gather(
            twitter_task,
            google_task,
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, list):
                all_trends.extend(result)
            elif isinstance(result, Exception):
                logger.warning(f"Trend source failed: {result}")

        logger.info(f"Collected {len(all_trends)} trending topics")

        # Extract celebrity mentions
        celebrities = self.extract_celebrity_mentions(all_trends)

        # Deduplicate by name
        seen = set()
        unique_celebrities = []
        for celeb in celebrities:
            name = celeb["name"].lower()
            if name not in seen:
                seen.add(name)
                unique_celebrities.append(celeb)

        # Sort by confidence
        unique_celebrities.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        logger.info(f"Discovered {len(unique_celebrities)} potential celebrities")

        return unique_celebrities

    async def get_instagram_username(self, celebrity_name: str) -> Optional[str]:
        """
        Try to find Instagram username for a celebrity.

        Uses search and known mappings.
        """
        # Known mappings
        username_map = {
            "davido": "davido",
            "wizkid": "wizkidayo",
            "burna boy": "burabornaboy",
            "tiwa savage": "taboriajayi",
            "don jazzy": "don_jazzy",
            "funke akindele": "funaborkeakindele",
            "rema": "heisrema",
            "asake": "asaborakemusik",
            "tems": "temsbaby",
            "ayra starr": "ayrastarr",
            "fireboy": "firaboreboyfordml",
            # Add more mappings as needed
        }

        name_lower = celebrity_name.lower()

        if name_lower in username_map:
            return username_map[name_lower]

        # Try simple username guess
        simple_username = name_lower.replace(" ", "").replace("-", "")
        return simple_username


async def run_discovery_job():
    """
    Scheduled job to run celebrity discovery.

    Should be run every few hours via Celery beat.
    """
    monitor = TrendingMonitor()

    try:
        celebrities = await monitor.discover_trending_celebrities()

        # Filter high-confidence discoveries
        high_confidence = [c for c in celebrities if c.get("confidence", 0) >= 0.7]

        logger.info(f"High-confidence discoveries: {len(high_confidence)}")

        # TODO: Save to database as pending celebrities
        # TODO: Trigger notification to admin for approval

        return {
            "total_discovered": len(celebrities),
            "high_confidence": len(high_confidence),
            "celebrities": high_confidence[:10]  # Top 10
        }

    finally:
        await monitor.close()


if __name__ == "__main__":
    # Test the monitor
    async def test():
        result = await run_discovery_job()
        print(f"Discovery result: {result}")

    asyncio.run(test())
