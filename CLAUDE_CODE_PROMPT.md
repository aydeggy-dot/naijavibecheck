# 🚀 NaijaVibeCheck - Full Project Development Prompt for Claude Code

## Project Overview

Build a complete, production-ready social media analytics and content generation platform called **"NaijaVibeCheck"** (or user's chosen brand name). The platform monitors Nigerian celebrities' Instagram posts, analyzes comment sentiment, generates eye-catching content showcasing the analysis, and autonomously manages an Instagram page to grow followers.

---

## 🎯 Core Mission

Create an automated system that:
1. **Discovers** trending Nigerian celebrities and their viral posts
2. **Extracts** comments from viral posts
3. **Analyzes** sentiment (positive, negative, neutral) using AI
4. **Identifies** the top 3 most positive and top 3 most toxic comments
5. **Generates** visually stunning posts (images, carousels, reels) displaying these analytics
6. **Publishes** content to the NaijaVibeCheck Instagram page
7. **Learns** from engagement to optimize future content
8. **Provides** a dashboard for human oversight and control

---

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NAIJAVIBECHECK SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │   SCRAPER    │───▶│   ANALYZER   │───▶│  GENERATOR   │───▶│  PUBLISHER │ │
│  │   MODULE     │    │   MODULE     │    │   MODULE     │    │   MODULE   │ │
│  └──────────────┘    └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │                   │        │
│         ▼                   ▼                   ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         PostgreSQL DATABASE                              ││
│  │  • celebrities • posts • comments • analytics • generated_content       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│         │                   │                   │                   │        │
│         ▼                   ▼                   ▼                   ▼        │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      LEARNING ENGINE (ML/AI)                            ││
│  │  • Engagement prediction • Content optimization • Timing analysis       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                      DASHBOARD (React/Next.js)                          ││
│  │  • Monitoring • Controls • Analytics • Content approval • Settings      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Reason |
|-----------|------------|--------|
| **Backend API** | Python (FastAPI) | Fast, async, great for AI integration |
| **Scraping Engine** | Python (instaloader + instagrapi) | Robust Instagram access |
| **AI/ML** | Anthropic Claude API (claude-opus-4-5-20250514) | Sentiment analysis, content generation |
| **Image Generation** | Pillow + Cairo + MoviePy | Static images, carousels, video reels |
| **Database** | PostgreSQL | Reliable, scalable, good for analytics |
| **Cache/Queue** | Redis | Job queuing, rate limiting, caching |
| **Task Scheduler** | Celery | Background jobs, scheduled tasks |
| **Frontend Dashboard** | Next.js 14 + TypeScript + Tailwind CSS | Modern, fast, great DX |
| **Charts/Viz** | Recharts + D3.js | Dashboard analytics visualization |
| **Hosting** | DigitalOcean (Droplet + Managed DB) | Cost-effective, simple |
| **File Storage** | DigitalOcean Spaces (S3-compatible) | Generated media storage |

---

## 📁 Project Structure

```
naijavibecheck/
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
│
├── backend/                          # Python FastAPI Backend
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── alembic/                      # Database migrations
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── config.py                 # Settings & environment
│   │   ├── database.py               # DB connection
│   │   │
│   │   ├── api/                      # API Routes
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── celebrities.py
│   │   │   │   ├── posts.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── content.py
│   │   │   │   ├── settings.py
│   │   │   │   └── auth.py
│   │   │   └── deps.py               # Dependencies
│   │   │
│   │   ├── models/                   # SQLAlchemy Models
│   │   │   ├── __init__.py
│   │   │   ├── celebrity.py
│   │   │   ├── post.py
│   │   │   ├── comment.py
│   │   │   ├── analysis.py
│   │   │   ├── generated_content.py
│   │   │   ├── engagement.py
│   │   │   └── settings.py
│   │   │
│   │   ├── schemas/                  # Pydantic Schemas
│   │   │   ├── __init__.py
│   │   │   ├── celebrity.py
│   │   │   ├── post.py
│   │   │   ├── comment.py
│   │   │   ├── analysis.py
│   │   │   └── content.py
│   │   │
│   │   ├── services/                 # Business Logic
│   │   │   ├── __init__.py
│   │   │   ├── scraper/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── instagram_scraper.py
│   │   │   │   ├── account_manager.py    # Rotating throwaway accounts
│   │   │   │   ├── proxy_manager.py
│   │   │   │   └── rate_limiter.py
│   │   │   │
│   │   │   ├── analyzer/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sentiment_analyzer.py  # Claude AI integration
│   │   │   │   ├── toxicity_detector.py
│   │   │   │   ├── trending_detector.py
│   │   │   │   └── viral_scorer.py
│   │   │   │
│   │   │   ├── generator/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── content_generator.py   # AI content ideas
│   │   │   │   ├── image_generator.py     # Static posts
│   │   │   │   ├── carousel_generator.py  # Multi-slide posts
│   │   │   │   ├── reel_generator.py      # Video content
│   │   │   │   ├── caption_generator.py   # Post captions
│   │   │   │   └── templates/             # Design templates
│   │   │   │       ├── base_template.py
│   │   │   │       ├── stats_card.py
│   │   │   │       ├── comment_spotlight.py
│   │   │   │       └── vibe_meter.py
│   │   │   │
│   │   │   ├── publisher/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── instagram_publisher.py
│   │   │   │   ├── scheduler.py
│   │   │   │   └── optimal_time.py
│   │   │   │
│   │   │   └── learning/
│   │   │       ├── __init__.py
│   │   │       ├── engagement_tracker.py
│   │   │       ├── content_optimizer.py
│   │   │       ├── trend_predictor.py
│   │   │       └── recommendation_engine.py
│   │   │
│   │   ├── workers/                  # Celery Tasks
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── scraping_tasks.py
│   │   │   ├── analysis_tasks.py
│   │   │   ├── generation_tasks.py
│   │   │   ├── publishing_tasks.py
│   │   │   └── learning_tasks.py
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── text_processing.py
│   │       ├── image_utils.py
│   │       ├── username_anonymizer.py  # Partial asterisks
│   │       └── nigerian_context.py     # Nigerian slang/context
│   │
│   └── tests/
│       ├── __init__.py
│       ├── test_scraper.py
│       ├── test_analyzer.py
│       ├── test_generator.py
│       └── test_publisher.py
│
├── dashboard/                        # Next.js Frontend
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Dashboard home
│   │   │   ├── celebrities/
│   │   │   │   ├── page.tsx          # Celebrity management
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── posts/
│   │   │   │   ├── page.tsx          # Analyzed posts
│   │   │   │   └── [id]/page.tsx
│   │   │   ├── content/
│   │   │   │   ├── page.tsx          # Generated content queue
│   │   │   │   ├── pending/page.tsx  # Awaiting approval
│   │   │   │   ├── published/page.tsx
│   │   │   │   └── [id]/edit/page.tsx
│   │   │   ├── analytics/
│   │   │   │   ├── page.tsx          # Your page's performance
│   │   │   │   └── insights/page.tsx
│   │   │   ├── settings/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── accounts/page.tsx # Scraper accounts
│   │   │   │   ├── thresholds/page.tsx
│   │   │   │   ├── automation/page.tsx
│   │   │   │   └── branding/page.tsx
│   │   │   └── api/                  # API routes (if needed)
│   │   │
│   │   ├── components/
│   │   │   ├── ui/                   # Reusable UI components
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   ├── Modal.tsx
│   │   │   │   ├── Table.tsx
│   │   │   │   ├── Toggle.tsx
│   │   │   │   └── ...
│   │   │   ├── charts/
│   │   │   │   ├── SentimentPieChart.tsx
│   │   │   │   ├── EngagementLineChart.tsx
│   │   │   │   ├── TrendingBarChart.tsx
│   │   │   │   └── VibeMeter.tsx
│   │   │   ├── celebrities/
│   │   │   │   ├── CelebrityCard.tsx
│   │   │   │   ├── CelebrityList.tsx
│   │   │   │   └── AddCelebrityModal.tsx
│   │   │   ├── content/
│   │   │   │   ├── ContentPreview.tsx
│   │   │   │   ├── ContentEditor.tsx
│   │   │   │   ├── ApprovalQueue.tsx
│   │   │   │   └── PublishButton.tsx
│   │   │   └── layout/
│   │   │       ├── Sidebar.tsx
│   │   │       ├── Header.tsx
│   │   │       └── Footer.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useCelebrities.ts
│   │   │   ├── usePosts.ts
│   │   │   ├── useContent.ts
│   │   │   ├── useAnalytics.ts
│   │   │   └── useSettings.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                # API client
│   │   │   ├── utils.ts
│   │   │   └── constants.ts
│   │   │
│   │   └── types/
│   │       └── index.ts
│   │
│   └── public/
│       ├── logo.svg
│       └── assets/
│
├── templates/                        # Visual templates for content
│   ├── fonts/
│   │   └── (Nigerian-friendly fonts)
│   ├── backgrounds/
│   ├── overlays/
│   └── elements/
│
└── scripts/
    ├── setup.sh
    ├── seed_celebrities.py
    └── backup_db.sh
```

---

## 📊 Database Schema

### Core Tables

```sql
-- Celebrities being tracked
CREATE TABLE celebrities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instagram_username VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    category VARCHAR(50), -- 'musician', 'actor', 'influencer', 'athlete'
    follower_count INTEGER,
    is_active BOOLEAN DEFAULT true,
    discovered_at TIMESTAMP DEFAULT NOW(),
    last_scraped_at TIMESTAMP,
    scrape_priority INTEGER DEFAULT 5, -- 1-10, higher = more frequent
    metadata JSONB DEFAULT '{}'
);

-- Viral posts detected
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    celebrity_id UUID REFERENCES celebrities(id),
    instagram_post_id VARCHAR(255) UNIQUE NOT NULL,
    shortcode VARCHAR(50) NOT NULL,
    post_url VARCHAR(500),
    caption TEXT,
    like_count INTEGER,
    comment_count INTEGER,
    posted_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_viral BOOLEAN DEFAULT false,
    viral_score FLOAT,
    is_analyzed BOOLEAN DEFAULT false,
    is_processed BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'
);

-- Raw comments extracted
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES posts(id),
    instagram_comment_id VARCHAR(255),
    username VARCHAR(255),
    username_anonymized VARCHAR(255), -- with asterisks
    text TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    commented_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    is_reply BOOLEAN DEFAULT false,
    parent_comment_id UUID REFERENCES comments(id),
    UNIQUE(post_id, instagram_comment_id)
);

-- Sentiment analysis results
CREATE TABLE comment_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID REFERENCES comments(id) UNIQUE,
    sentiment VARCHAR(20), -- 'positive', 'negative', 'neutral'
    sentiment_score FLOAT, -- -1.0 to 1.0
    toxicity_score FLOAT, -- 0.0 to 1.0
    emotion_tags VARCHAR(50)[], -- ['funny', 'angry', 'supportive', etc.]
    is_top_positive BOOLEAN DEFAULT false,
    is_top_negative BOOLEAN DEFAULT false,
    analyzed_at TIMESTAMP DEFAULT NOW(),
    analysis_metadata JSONB DEFAULT '{}'
);

-- Post-level analysis summary
CREATE TABLE post_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES posts(id) UNIQUE,
    total_comments_analyzed INTEGER,
    positive_count INTEGER,
    negative_count INTEGER,
    neutral_count INTEGER,
    positive_percentage FLOAT,
    negative_percentage FLOAT,
    neutral_percentage FLOAT,
    average_sentiment_score FLOAT,
    top_positive_comment_ids UUID[],
    top_negative_comment_ids UUID[],
    controversy_score FLOAT, -- How divisive the post is
    analyzed_at TIMESTAMP DEFAULT NOW(),
    ai_summary TEXT, -- Claude's summary of the vibe
    ai_insights JSONB -- Additional AI insights
);

-- Generated content for our page
CREATE TABLE generated_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_analysis_id UUID REFERENCES post_analysis(id),
    content_type VARCHAR(50), -- 'image', 'carousel', 'reel'
    title VARCHAR(255),
    caption TEXT,
    hashtags VARCHAR(50)[],
    media_urls TEXT[], -- URLs to generated images/videos
    thumbnail_url TEXT,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'pending_review', 'approved', 'published', 'rejected'
    scheduled_for TIMESTAMP,
    published_at TIMESTAMP,
    instagram_post_id VARCHAR(255), -- After publishing
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    generation_metadata JSONB DEFAULT '{}'
);

-- Our page's engagement tracking
CREATE TABLE our_engagement (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_content_id UUID REFERENCES generated_content(id),
    checked_at TIMESTAMP DEFAULT NOW(),
    like_count INTEGER,
    comment_count INTEGER,
    share_count INTEGER,
    save_count INTEGER,
    reach INTEGER,
    impressions INTEGER,
    engagement_rate FLOAT,
    follower_change INTEGER -- Net follower change after this post
);

-- Learning & optimization data
CREATE TABLE content_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generated_content_id UUID REFERENCES generated_content(id),
    celebrity_category VARCHAR(50),
    content_type VARCHAR(50),
    post_hour INTEGER, -- 0-23
    post_day_of_week INTEGER, -- 0-6
    controversy_level VARCHAR(20), -- 'low', 'medium', 'high'
    engagement_score FLOAT,
    virality_score FLOAT,
    features JSONB, -- ML features
    created_at TIMESTAMP DEFAULT NOW()
);

-- System settings
CREATE TABLE settings (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Scraper account management
CREATE TABLE scraper_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(255) NOT NULL,
    password_encrypted TEXT NOT NULL,
    session_data TEXT,
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    requests_today INTEGER DEFAULT 0,
    is_banned BOOLEAN DEFAULT false,
    banned_at TIMESTAMP,
    proxy_id UUID,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Proxy management
CREATE TABLE proxies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    username VARCHAR(255),
    password_encrypted TEXT,
    protocol VARCHAR(20) DEFAULT 'http',
    is_active BOOLEAN DEFAULT true,
    last_used_at TIMESTAMP,
    failure_count INTEGER DEFAULT 0,
    country_code VARCHAR(5),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔧 Core Service Implementations

### 1. Instagram Scraper Service

```python
# backend/app/services/scraper/instagram_scraper.py

"""
Instagram Scraper Service
- Discovers trending Nigerian celebrities
- Monitors their posts for viral content
- Extracts comments with rate limiting and account rotation
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List, Optional
import instaloader
from instagrapi import Client
from app.services.scraper.account_manager import AccountManager
from app.services.scraper.proxy_manager import ProxyManager
from app.services.scraper.rate_limiter import RateLimiter
from app.models import Celebrity, Post, Comment
from app.database import get_db
from app.config import settings

class InstagramScraper:
    """
    Main Instagram scraping service with:
    - Account rotation (throwaway accounts)
    - Proxy rotation
    - Rate limiting
    - Error recovery
    """
    
    def __init__(self):
        self.account_manager = AccountManager()
        self.proxy_manager = ProxyManager()
        self.rate_limiter = RateLimiter(
            max_requests_per_hour=100,
            max_requests_per_day=500
        )
        self.loader = None
        self.client = None
        
    async def initialize(self):
        """Initialize with a working account and proxy."""
        account = await self.account_manager.get_available_account()
        proxy = await self.proxy_manager.get_available_proxy()
        
        # Setup instaloader
        self.loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_comments=False,
            save_metadata=False,
            quiet=True
        )
        
        # Setup instagrapi (for publishing later)
        self.client = Client()
        if proxy:
            self.client.set_proxy(proxy.to_url())
        
        # Login
        try:
            self.loader.login(account.username, account.password)
            self.client.login(account.username, account.password)
        except Exception as e:
            await self.account_manager.mark_account_failed(account.id)
            raise
    
    async def discover_trending_nigerian_celebrities(
        self,
        min_followers: int = 1_500_000,
        categories: List[str] = ['musician', 'actor', 'influencer']
    ) -> List[dict]:
        """
        Discover trending Nigerian celebrities.
        
        Strategy:
        1. Start from known Nigerian celebrity accounts
        2. Explore their following/tagged accounts
        3. Check Nigerian hashtags (#naija, #nigeria, #nollywood, etc.)
        4. Filter by follower count and engagement
        """
        await self.rate_limiter.wait_if_needed()
        
        # Seed accounts (well-known Nigerian celebrities)
        seed_accounts = [
            'davaborofficial',   # Davido
            'burabornaboy',      # Burna Boy
            'wiaborzkidayo',     # Wizkid
            'tayaboriajayi',     # Tiwa Savage
            'funaborkeakindele', # Funke Akindele
            # Add more seed accounts
        ]
        
        discovered = []
        
        # Strategy 1: Explore seed account connections
        for seed in seed_accounts:
            try:
                profile = instaloader.Profile.from_username(
                    self.loader.context, seed
                )
                
                # Get tagged accounts from recent posts
                for post in profile.get_posts():
                    if len(discovered) >= 50:
                        break
                    # Extract tagged users
                    # Check if they meet criteria
                    
            except Exception as e:
                continue
        
        # Strategy 2: Nigerian hashtag exploration
        nigerian_hashtags = [
            'naijacelebs', 'nollywood', 'afrobeats',
            'naijamusicisabors', 'lagoscelebs'
        ]
        
        # ... implementation continues
        
        return discovered
    
    async def get_viral_posts(
        self,
        celebrity_username: str,
        min_likes: int = 100_000,
        min_comments: int = 25_000,
        max_age_days: int = 3
    ) -> List[dict]:
        """
        Get viral posts from a celebrity that meet our criteria.
        """
        await self.rate_limiter.wait_if_needed()
        
        try:
            profile = instaloader.Profile.from_username(
                self.loader.context, celebrity_username
            )
            
            viral_posts = []
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            
            for post in profile.get_posts():
                # Check age
                if post.date_utc < cutoff_date:
                    break  # Posts are chronological, stop here
                
                # Check viral criteria
                if post.likes >= min_likes and post.comments >= min_comments:
                    viral_posts.append({
                        'shortcode': post.shortcode,
                        'url': f"https://instagram.com/p/{post.shortcode}/",
                        'caption': post.caption,
                        'likes': post.likes,
                        'comments': post.comments,
                        'posted_at': post.date_utc,
                        'viral_score': self._calculate_viral_score(post)
                    })
            
            return viral_posts
            
        except Exception as e:
            await self._handle_error(e)
            return []
    
    async def extract_comments(
        self,
        post_shortcode: str,
        max_comments: int = 500
    ) -> List[dict]:
        """
        Extract comments from a post with full metadata.
        """
        await self.rate_limiter.wait_if_needed()
        
        comments = []
        
        try:
            post = instaloader.Post.from_shortcode(
                self.loader.context, post_shortcode
            )
            
            count = 0
            for comment in post.get_comments():
                if count >= max_comments:
                    break
                
                comments.append({
                    'instagram_comment_id': str(comment.id),
                    'username': comment.owner.username,
                    'username_anonymized': self._anonymize_username(comment.owner.username),
                    'text': comment.text,
                    'like_count': getattr(comment, 'likes_count', 0),
                    'commented_at': comment.created_at_utc,
                    'is_reply': False,
                    'replies': []
                })
                
                # Get replies
                if hasattr(comment, 'answers'):
                    for reply in comment.answers:
                        comments[-1]['replies'].append({
                            'instagram_comment_id': str(reply.id),
                            'username': reply.owner.username,
                            'username_anonymized': self._anonymize_username(reply.owner.username),
                            'text': reply.text,
                            'commented_at': reply.created_at_utc,
                        })
                
                count += 1
                
                # Micro-delay to avoid detection
                if count % 20 == 0:
                    await asyncio.sleep(random.uniform(1, 3))
            
            return comments
            
        except Exception as e:
            await self._handle_error(e)
            return []
    
    def _anonymize_username(self, username: str) -> str:
        """
        Anonymize username with asterisks.
        Example: 'johndoe123' -> 'joh***123'
        """
        if len(username) <= 4:
            return username[0] + '***'
        
        visible_start = len(username) // 3
        visible_end = len(username) // 3
        
        return (
            username[:visible_start] + 
            '*' * (len(username) - visible_start - visible_end) + 
            username[-visible_end:]
        )
    
    def _calculate_viral_score(self, post) -> float:
        """
        Calculate a viral score based on engagement metrics.
        """
        # Engagement rate = (likes + comments) / followers
        # Controversy factor = comments / likes ratio (more comments = more discussion)
        
        likes = post.likes
        comments = post.comments
        
        # Base score from raw numbers
        base_score = (likes / 100_000) + (comments / 10_000)
        
        # Controversy bonus (high comment-to-like ratio = heated discussion)
        controversy_bonus = min((comments / max(likes, 1)) * 10, 5)
        
        return min(base_score + controversy_bonus, 100)
    
    async def _handle_error(self, error: Exception):
        """Handle scraping errors with appropriate recovery."""
        error_str = str(error).lower()
        
        if 'rate' in error_str or '429' in error_str:
            # Rate limited - wait and rotate
            await self.rate_limiter.backoff()
            await self.account_manager.rotate_account()
            
        elif 'login' in error_str or 'credential' in error_str:
            # Account issue - rotate
            await self.account_manager.mark_current_failed()
            await self.initialize()
            
        elif 'proxy' in error_str or 'connection' in error_str:
            # Proxy issue - rotate
            await self.proxy_manager.mark_current_failed()
            await self.initialize()
```

### 2. Sentiment Analyzer Service (Claude AI)

```python
# backend/app/services/analyzer/sentiment_analyzer.py

"""
Sentiment Analyzer using Claude AI
- Analyzes comment sentiment (positive, negative, neutral)
- Detects toxicity levels
- Identifies emotional tone
- Understands Nigerian context and slang
"""

import anthropic
from typing import List, Dict, Tuple
import json
from app.config import settings

class SentimentAnalyzer:
    """
    AI-powered sentiment analysis using Claude API.
    Optimized for Nigerian English, pidgin, and cultural context.
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20250514"
    
    async def analyze_comments_batch(
        self,
        comments: List[Dict],
        celebrity_name: str,
        post_context: str
    ) -> List[Dict]:
        """
        Analyze a batch of comments for sentiment.
        
        Returns enriched comments with:
        - sentiment: 'positive', 'negative', 'neutral'
        - sentiment_score: -1.0 to 1.0
        - toxicity_score: 0.0 to 1.0
        - emotion_tags: ['funny', 'angry', 'supportive', etc.]
        """
        
        # Prepare comments for analysis
        comments_text = "\n".join([
            f"[{i+1}] @{c['username_anonymized']}: {c['text']}"
            for i, c in enumerate(comments[:50])  # Batch of 50
        ])
        
        prompt = f"""You are analyzing Instagram comments on a Nigerian celebrity's post.

CELEBRITY: {celebrity_name}
POST CONTEXT: {post_context[:500]}

COMMENTS TO ANALYZE:
{comments_text}

IMPORTANT CONTEXT:
- These comments are from Nigerian Instagram users
- Understand Nigerian Pidgin English (e.g., "na wa", "e no easy", "omo", "abeg")
- Understand Nigerian slang and expressions
- Consider cultural context (Nigerian entertainment, music, Nollywood, etc.)
- "Drag" culture is common - harsh criticism can be entertainment
- Emojis like 🔥💯😂 often indicate support

For EACH comment, analyze and return a JSON array with:
1. "index": The comment number
2. "sentiment": "positive", "negative", or "neutral"
3. "sentiment_score": Float from -1.0 (very negative) to 1.0 (very positive)
4. "toxicity_score": Float from 0.0 (not toxic) to 1.0 (very toxic)
5. "emotion_tags": Array of emotions like ["funny", "angry", "supportive", "jealous", "sarcastic", "loving", "critical", "trolling"]
6. "is_notable": Boolean - true if this comment is particularly interesting (very positive, very negative, or funny)
7. "summary": Brief 5-10 word summary of the comment's vibe

Return ONLY valid JSON array, no other text.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            analysis_results = json.loads(response.content[0].text)
            
            # Merge analysis back into comments
            for result in analysis_results:
                idx = result['index'] - 1
                if 0 <= idx < len(comments):
                    comments[idx].update({
                        'sentiment': result['sentiment'],
                        'sentiment_score': result['sentiment_score'],
                        'toxicity_score': result['toxicity_score'],
                        'emotion_tags': result['emotion_tags'],
                        'is_notable': result['is_notable'],
                        'ai_summary': result['summary']
                    })
            
            return comments
            
        except json.JSONDecodeError:
            # Fallback to individual analysis
            return await self._analyze_individually(comments, celebrity_name, post_context)
    
    async def get_top_comments(
        self,
        analyzed_comments: List[Dict],
        top_n: int = 3
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Get the top N most positive and most negative/toxic comments.
        
        Returns:
            (top_positive, top_negative)
        """
        
        # Sort by sentiment score
        sorted_by_sentiment = sorted(
            analyzed_comments,
            key=lambda x: x.get('sentiment_score', 0),
            reverse=True
        )
        
        # Sort by toxicity
        sorted_by_toxicity = sorted(
            analyzed_comments,
            key=lambda x: x.get('toxicity_score', 0),
            reverse=True
        )
        
        # Get top positive (high sentiment, low toxicity)
        top_positive = [
            c for c in sorted_by_sentiment
            if c.get('sentiment') == 'positive' and c.get('toxicity_score', 0) < 0.3
        ][:top_n]
        
        # Get top negative/toxic
        top_negative = [
            c for c in sorted_by_toxicity
            if c.get('toxicity_score', 0) > 0.5 or c.get('sentiment') == 'negative'
        ][:top_n]
        
        return top_positive, top_negative
    
    async def generate_post_summary(
        self,
        celebrity_name: str,
        post_caption: str,
        stats: Dict,
        top_positive: List[Dict],
        top_negative: List[Dict]
    ) -> Dict:
        """
        Generate an AI summary of the overall vibe and insights.
        """
        
        prompt = f"""You are a witty Nigerian social media analyst creating content for a Gen Z audience.

CELEBRITY: {celebrity_name}
POST: {post_caption[:300]}

STATS:
- Total comments analyzed: {stats['total']}
- Positive: {stats['positive_pct']:.1f}%
- Negative: {stats['negative_pct']:.1f}%
- Neutral: {stats['neutral_pct']:.1f}%

TOP POSITIVE VIBES:
{chr(10).join([f"- {c['text'][:100]}" for c in top_positive])}

TOP TOXIC/NEGATIVE:
{chr(10).join([f"- {c['text'][:100]}" for c in top_negative])}

Generate a response with:
1. "headline": Catchy, meme-worthy headline (max 10 words) for our post. Use Nigerian slang appropriately.
2. "vibe_summary": 2-3 sentence summary of the overall vibe in fun, Gen Z Nigerian style
3. "spicy_take": One witty observation about the comments (for engagement)
4. "controversy_level": "chill", "mid", or "wahala" (how heated is the discussion)
5. "recommended_hashtags": 5 relevant Nigerian Instagram hashtags

Return as JSON only.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return json.loads(response.content[0].text)
```

### 3. Content Generator Service

```python
# backend/app/services/generator/image_generator.py

"""
Visual Content Generator
Creates eye-catching Instagram posts displaying comment analytics.
"""

from PIL import Image, ImageDraw, ImageFont
import cairo
from pathlib import Path
from typing import Dict, List, Tuple
import io
from app.config import settings

class ImageGenerator:
    """
    Generates Instagram-ready images with:
    - Statistics overlays
    - Comment spotlights
    - Vibe meters
    - Brand styling
    """
    
    def __init__(self):
        self.brand_colors = {
            'primary': '#FF6B35',      # Vibrant orange
            'secondary': '#004E89',    # Deep blue
            'accent': '#FFBE0B',       # Yellow
            'positive': '#2EC4B6',     # Teal/green
            'negative': '#E71D36',     # Red
            'neutral': '#7B8794',      # Gray
            'background': '#1A1A2E',   # Dark purple-black
            'text': '#FFFFFF',
            'text_secondary': '#A0A0A0'
        }
        
        self.fonts_dir = Path(settings.TEMPLATES_DIR) / 'fonts'
        self.templates_dir = Path(settings.TEMPLATES_DIR)
        
    def generate_stats_card(
        self,
        celebrity_name: str,
        post_preview: str,
        stats: Dict,
        headline: str,
        size: Tuple[int, int] = (1080, 1350)  # Instagram portrait
    ) -> bytes:
        """
        Generate a statistics card showing sentiment breakdown.
        
        Layout:
        ┌─────────────────────────┐
        │     [BRAND LOGO]        │
        │                         │
        │   {Celebrity Name}      │
        │   📊 Comment Breakdown  │
        │                         │
        │   ┌─────────────────┐   │
        │   │  VIBE METER     │   │
        │   │  [===========]  │   │
        │   └─────────────────┘   │
        │                         │
        │   😊 Positive: 45%      │
        │   😤 Negative: 30%      │
        │   😐 Neutral: 25%       │
        │                         │
        │   "Headline here"       │
        │                         │
        │   @naijavibecheck       │
        └─────────────────────────┘
        """
        
        width, height = size
        
        # Create Cairo surface for better graphics
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        
        # Background gradient
        gradient = cairo.LinearGradient(0, 0, 0, height)
        gradient.add_color_stop_rgb(0, 0.1, 0.1, 0.18)  # Dark top
        gradient.add_color_stop_rgb(1, 0.05, 0.05, 0.1)  # Darker bottom
        ctx.set_source(gradient)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()
        
        # Add decorative elements
        self._draw_decorative_elements(ctx, width, height)
        
        # Brand logo area (top)
        self._draw_brand_header(ctx, width)
        
        # Celebrity name
        self._draw_text(
            ctx, celebrity_name.upper(),
            width // 2, 200,
            font_size=48, bold=True, color=self.brand_colors['text'],
            align='center'
        )
        
        # "Comment Breakdown" subtitle
        self._draw_text(
            ctx, "📊 COMMENT BREAKDOWN",
            width // 2, 270,
            font_size=28, color=self.brand_colors['text_secondary'],
            align='center'
        )
        
        # Vibe Meter
        self._draw_vibe_meter(
            ctx,
            x=100, y=350,
            width=width - 200,
            positive_pct=stats['positive_pct'],
            negative_pct=stats['negative_pct'],
            neutral_pct=stats['neutral_pct']
        )
        
        # Stats breakdown
        y_offset = 550
        stats_items = [
            ('😊', 'Positive', stats['positive_pct'], self.brand_colors['positive']),
            ('😤', 'Negative', stats['negative_pct'], self.brand_colors['negative']),
            ('😐', 'Neutral', stats['neutral_pct'], self.brand_colors['neutral']),
        ]
        
        for emoji, label, pct, color in stats_items:
            self._draw_stat_row(ctx, emoji, label, pct, color, width // 2, y_offset)
            y_offset += 100
        
        # Headline
        self._draw_text(
            ctx, f'"{headline}"',
            width // 2, 950,
            font_size=36, italic=True, color=self.brand_colors['accent'],
            align='center', max_width=width - 100
        )
        
        # Total comments analyzed
        self._draw_text(
            ctx, f"Based on {stats['total']:,} comments",
            width // 2, 1050,
            font_size=24, color=self.brand_colors['text_secondary'],
            align='center'
        )
        
        # Brand footer
        self._draw_brand_footer(ctx, width, height)
        
        # Convert to PNG bytes
        buf = io.BytesIO()
        surface.write_to_png(buf)
        buf.seek(0)
        
        return buf.getvalue()
    
    def generate_carousel(
        self,
        celebrity_name: str,
        stats: Dict,
        top_positive: List[Dict],
        top_negative: List[Dict],
        ai_insights: Dict
    ) -> List[bytes]:
        """
        Generate a carousel (multiple slides):
        1. Stats overview
        2. Top positive comments
        3. Top negative/toxic comments
        4. AI insights/summary
        """
        
        slides = []
        
        # Slide 1: Stats card
        slides.append(self.generate_stats_card(
            celebrity_name,
            "",
            stats,
            ai_insights.get('headline', 'The vibes are in!')
        ))
        
        # Slide 2: Top positive comments
        slides.append(self.generate_comments_slide(
            title="TOP POSITIVE VIBES 💚",
            comments=top_positive,
            theme='positive'
        ))
        
        # Slide 3: Top negative comments
        slides.append(self.generate_comments_slide(
            title="THE TOXIC ZONE ☠️",
            comments=top_negative,
            theme='negative'
        ))
        
        # Slide 4: Summary/insights
        slides.append(self.generate_insights_slide(
            celebrity_name,
            ai_insights
        ))
        
        return slides
    
    def generate_comments_slide(
        self,
        title: str,
        comments: List[Dict],
        theme: str = 'positive',
        size: Tuple[int, int] = (1080, 1350)
    ) -> bytes:
        """
        Generate a slide showcasing specific comments.
        
        Layout:
        ┌─────────────────────────┐
        │   {Title}               │
        │                         │
        │   ┌─────────────────┐   │
        │   │ @use***name     │   │
        │   │ "Comment text"  │   │
        │   └─────────────────┘   │
        │                         │
        │   ┌─────────────────┐   │
        │   │ @ano***user     │   │
        │   │ "Comment text"  │   │
        │   └─────────────────┘   │
        │                         │
        │   ...                   │
        │                         │
        │   @naijavibecheck       │
        └─────────────────────────┘
        """
        
        width, height = size
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)
        
        # Theme colors
        theme_color = self.brand_colors['positive'] if theme == 'positive' else self.brand_colors['negative']
        
        # Background
        self._draw_themed_background(ctx, width, height, theme)
        
        # Title
        self._draw_text(
            ctx, title,
            width // 2, 100,
            font_size=42, bold=True, color=theme_color,
            align='center'
        )
        
        # Comment cards
        y_offset = 200
        for i, comment in enumerate(comments[:3]):
            self._draw_comment_card(
                ctx,
                x=60, y=y_offset,
                width=width - 120,
                username=comment['username_anonymized'],
                text=comment['text'][:150],
                theme=theme,
                number=i + 1
            )
            y_offset += 320
        
        # Brand footer
        self._draw_brand_footer(ctx, width, height)
        
        buf = io.BytesIO()
        surface.write_to_png(buf)
        buf.seek(0)
        
        return buf.getvalue()
    
    # ... additional helper methods
```

### 4. Publisher Service

```python
# backend/app/services/publisher/instagram_publisher.py

"""
Instagram Publisher Service
Handles posting content to the NaijaVibeCheck Instagram page.
"""

from instagrapi import Client
from instagrapi.types import Media
from typing import List, Optional
from datetime import datetime
import asyncio
from app.config import settings
from app.models import GeneratedContent
from app.services.publisher.optimal_time import OptimalTimeCalculator

class InstagramPublisher:
    """
    Publishes generated content to Instagram.
    Supports: images, carousels, and reels.
    """
    
    def __init__(self):
        self.client = Client()
        self.time_calculator = OptimalTimeCalculator()
        self.account_username = settings.INSTAGRAM_PAGE_USERNAME
        self.account_password = settings.INSTAGRAM_PAGE_PASSWORD
        
    async def initialize(self):
        """Login to the main posting account."""
        try:
            # Try to load session first
            session_file = f"sessions/{self.account_username}.json"
            self.client.load_settings(session_file)
            self.client.login(self.account_username, self.account_password)
        except Exception:
            # Fresh login
            self.client.login(self.account_username, self.account_password)
            self.client.dump_settings(session_file)
    
    async def publish_image(
        self,
        image_path: str,
        caption: str,
        hashtags: List[str] = None
    ) -> Optional[str]:
        """
        Publish a single image post.
        
        Returns:
            Instagram media ID if successful, None otherwise.
        """
        full_caption = self._build_caption(caption, hashtags)
        
        try:
            media = self.client.photo_upload(
                path=image_path,
                caption=full_caption
            )
            return media.pk
        except Exception as e:
            # Log error
            return None
    
    async def publish_carousel(
        self,
        image_paths: List[str],
        caption: str,
        hashtags: List[str] = None
    ) -> Optional[str]:
        """
        Publish a carousel (album) post.
        """
        full_caption = self._build_caption(caption, hashtags)
        
        try:
            media = self.client.album_upload(
                paths=image_paths,
                caption=full_caption
            )
            return media.pk
        except Exception as e:
            return None
    
    async def publish_reel(
        self,
        video_path: str,
        caption: str,
        thumbnail_path: str = None,
        hashtags: List[str] = None
    ) -> Optional[str]:
        """
        Publish a reel (short video).
        """
        full_caption = self._build_caption(caption, hashtags)
        
        try:
            media = self.client.clip_upload(
                path=video_path,
                caption=full_caption,
                thumbnail=thumbnail_path
            )
            return media.pk
        except Exception as e:
            return None
    
    async def schedule_post(
        self,
        content: GeneratedContent,
        scheduled_time: datetime = None
    ):
        """
        Schedule a post for optimal time if not specified.
        """
        if not scheduled_time:
            scheduled_time = await self.time_calculator.get_optimal_time(
                day_of_week=datetime.now().weekday(),
                content_type=content.content_type,
                target_timezone='Africa/Lagos'
            )
        
        # Store scheduled time
        content.scheduled_for = scheduled_time
        # Celery task will pick this up
        
    def _build_caption(self, caption: str, hashtags: List[str] = None) -> str:
        """Build full caption with hashtags and brand mention."""
        
        parts = [caption]
        
        # Add line breaks
        parts.append("\n\n")
        
        # Add call to action
        parts.append("Follow @naijavibecheck for more! 🔥\n")
        
        # Add hashtags
        if hashtags:
            parts.append("\n")
            parts.append(" ".join([f"#{tag}" for tag in hashtags]))
        
        # Default hashtags
        default_tags = [
            "NaijaVibeCheck", "NaijaCelebs", "Naija", "Lagos",
            "NigeriaEntertainment", "Gist", "Gossip"
        ]
        parts.append(" ")
        parts.append(" ".join([f"#{tag}" for tag in default_tags]))
        
        return "".join(parts)
```

---

## 🖥️ Dashboard Features

### Key Pages

1. **Dashboard Home**
   - Quick stats (posts today, engagement, follower growth)
   - Recent activity feed
   - Trending celebrities right now
   - Content queue status

2. **Celebrity Management**
   - List of tracked celebrities
   - Add/remove celebrities
   - Set priority levels
   - View per-celebrity analytics

3. **Content Queue**
   - Pending approval posts
   - Scheduled posts
   - Published posts history
   - Edit/preview before publishing

4. **Analytics**
   - Your page's engagement over time
   - Best performing content types
   - Optimal posting times analysis
   - Follower growth trends

5. **Settings**
   - Scraper account management
   - Proxy configuration
   - Viral thresholds (likes, comments)
   - Automation toggles (full auto vs approval required)
   - AI behavior settings
   - Branding customization

---

## 🤖 Automation Modes

### Mode 1: Full Autonomous
```
Scrape → Analyze → Generate → Publish (automatically)
```

### Mode 2: Semi-Autonomous (Default)
```
Scrape → Analyze → Generate → [Human Review] → Publish
```

### Mode 3: Manual
```
Scrape → Analyze → Generate → [Human Edit & Approve] → [Manual Publish]
```

---

## 📈 Learning Engine

The system should learn from:

1. **Our Page's Performance**
   - Which content types get most engagement
   - Best posting times for our audience
   - Which celebrities drive most followers
   - Caption styles that work

2. **Celebrity Posts**
   - What makes posts go viral
   - Controversy patterns
   - Emerging celebrities
   - Trending topics

---

## 🚀 Development Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Project setup (Docker, database, API skeleton)
- [ ] Database models and migrations
- [ ] Basic Instagram scraper with account rotation
- [ ] Basic sentiment analyzer integration

### Phase 2: Analysis Engine (Week 3-4)
- [ ] Full sentiment analysis pipeline
- [ ] Top comment selection algorithm
- [ ] Post-level analytics aggregation
- [ ] Viral detection system

### Phase 3: Content Generation (Week 5-6)
- [ ] Image generator (stats cards)
- [ ] Carousel generator
- [ ] Caption generator
- [ ] Brand template system

### Phase 4: Publishing System (Week 7-8)
- [ ] Instagram publisher integration
- [ ] Scheduling system
- [ ] Content queue management
- [ ] Approval workflow

### Phase 5: Dashboard (Week 9-10)
- [ ] Next.js dashboard setup
- [ ] Celebrity management UI
- [ ] Content queue UI
- [ ] Analytics visualizations

### Phase 6: Learning & Optimization (Week 11-12)
- [ ] Engagement tracking
- [ ] Performance analysis
- [ ] Recommendation engine
- [ ] A/B testing framework

### Phase 7: Polish & Launch (Week 13-14)
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] Production deployment

---

## ⚠️ Important Implementation Notes

### Scraping Best Practices
1. **Never use the main page account for scraping**
2. Rotate through 5-10 throwaway accounts
3. Use residential proxies (Nigerian IPs preferred)
4. Implement exponential backoff on rate limits
5. Scrape during off-peak hours (2-6 AM Lagos time)
6. Maximum 100 requests per account per day

### Content Guidelines
1. Always anonymize usernames (partial asterisks)
2. Never use celebrity images directly (copyright)
3. Create original graphics referencing posts
4. Include disclaimer: "For entertainment purposes"
5. Censor extreme profanity if needed

### Data Retention
1. Keep raw comments for 30 days only
2. Keep analytics for 6 months
3. Keep generated content permanently
4. Implement GDPR-style deletion on request

---

## 🔧 Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/naijavibecheck

# Redis
REDIS_URL=redis://localhost:6379/0

# Anthropic AI
ANTHROPIC_API_KEY=sk-ant-...

# Instagram Main Account (for posting)
INSTAGRAM_PAGE_USERNAME=naijavibecheck
INSTAGRAM_PAGE_PASSWORD=secure_password

# Storage
DO_SPACES_KEY=...
DO_SPACES_SECRET=...
DO_SPACES_BUCKET=naijavibecheck-media
DO_SPACES_REGION=nyc3

# App
SECRET_KEY=...
DEBUG=false
ENVIRONMENT=production

# Scraping
MAX_SCRAPER_ACCOUNTS=10
REQUESTS_PER_ACCOUNT_PER_DAY=100
```

---

## 📝 Additional Requirements

1. **All code must be production-ready** with proper error handling
2. **Include comprehensive logging** throughout
3. **Write tests** for critical paths (scraper, analyzer, generator)
4. **Use type hints** in Python code
5. **Follow PEP 8** style guidelines
6. **Include docstrings** for all classes and functions
7. **Create Alembic migrations** for database schema
8. **Dockerize** everything for easy deployment
9. **Include CI/CD** configuration (GitHub Actions)
10. **Write API documentation** (OpenAPI/Swagger)

---

## 🎯 Success Metrics

The system is successful when it can:
1. ✅ Automatically discover viral Nigerian celebrity posts
2. ✅ Extract and analyze 500+ comments per post
3. ✅ Generate visually appealing content in under 2 minutes
4. ✅ Post content at optimal times without manual intervention
5. ✅ Grow followers by learning from engagement patterns
6. ✅ Run 24/7 with minimal maintenance

---

Now build this system step by step, starting with the project structure and core infrastructure. Ask clarifying questions if needed before proceeding with implementation.
