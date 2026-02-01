"""
Celebrity Discovery Services

Automatic discovery of trending Nigerian celebrities through:
1. Trending hashtag monitoring (Twitter/X)
2. Blog/news scraping (Linda Ikeji, Bella Naija)
3. User submissions with admin approval
"""

from app.services.discovery.trending_monitor import TrendingMonitor
from app.services.discovery.blog_scraper import BlogScraper
from app.services.discovery.celebrity_suggester import CelebritySuggester

__all__ = [
    "TrendingMonitor",
    "BlogScraper",
    "CelebritySuggester",
]
