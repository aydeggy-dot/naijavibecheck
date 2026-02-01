# NaijaVibeCheck - How It Works

A comprehensive guide explaining how NaijaVibeCheck scrapes Instagram comments, analyzes sentiment, and publishes results for users to view.

---

## Table of Contents

1. [Overview](#overview)
2. [The Big Picture](#the-big-picture)
3. [Step-by-Step Flow](#step-by-step-flow)
4. [Component Details](#component-details)
5. [Background Services](#background-services)
6. [Data Flow Diagram](#data-flow-diagram)
7. [Cost Structure](#cost-structure)
8. [Running the System](#running-the-system)

---

## Overview

NaijaVibeCheck is an automated system that:
1. **Scrapes** comments from Nigerian celebrity Instagram posts
2. **Analyzes** the sentiment (positive/negative/neutral) of those comments
3. **Generates** engaging summaries with Nigerian Gen-Z style
4. **Publishes** the results as content for users to view

Think of it as a "vibe check" machine - it reads thousands of comments and tells you what the general feeling is about a celebrity's post.

---

## The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NAIJAVIBECHECK SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐       │
│   │ INSTAGRAM │ ──▶ │ SCRAPER  │ ──▶ │ ANALYZER │ ──▶ │ PUBLISHER │       │
│   │   POST    │      │ SERVICE  │      │ SERVICE  │      │ SERVICE  │       │
│   └──────────┘      └──────────┘      └──────────┘      └──────────┘       │
│                           │                 │                 │             │
│                           ▼                 ▼                 ▼             │
│                     ┌─────────────────────────────────────────────┐         │
│                     │              DATABASE                        │         │
│                     │  (Stores comments, analysis, results)        │         │
│                     └─────────────────────────────────────────────┘         │
│                                          │                                   │
│                                          ▼                                   │
│                     ┌─────────────────────────────────────────────┐         │
│                     │           FRONTEND DASHBOARD                 │         │
│                     │     (Users view the vibe check results)      │         │
│                     └─────────────────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Flow

### Step 1: A Celebrity Posts on Instagram

```
Davido posts a new photo with caption:
"I be Africa man original I no be gentleman at all o"

The post gets 22,900 comments from fans
```

### Step 2: NaijaVibeCheck Detects the Post

The system can be triggered in two ways:
- **Manually**: Admin enters the post URL in the dashboard
- **Automatically**: Background job checks tracked celebrities every few hours

```python
# Example: Starting an analysis
POST /api/v1/analysis/start
{
    "post_url": "https://www.instagram.com/p/DULsWrPjwef/",
    "celebrity_name": "Davido"
}
```

### Step 3: Scraper Service Gets All Comments

The **Scraper Service** connects to Instagram and downloads all comments:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SCRAPER SERVICE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Login to Instagram (using scraper account)                   │
│  2. Navigate to the post                                         │
│  3. Use Instagram's GraphQL API to fetch comments                │
│  4. Handle pagination (get page 1, then page 2, etc.)            │
│  5. Save comments with metadata (username, time, likes)          │
│  6. Respect rate limits (wait between requests)                  │
│                                                                  │
│  Rate Limiting:                                                  │
│  - Max 200 requests per hour                                     │
│  - 2-5 second delay between requests                             │
│  - Pause 30 seconds every 100 requests                           │
│  - If blocked, wait and retry with exponential backoff           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Output**: A JSON file with all comments:
```json
[
    {
        "id": "comment_123",
        "username": "fan_user_001",
        "text": "OBO na the GOAT 🔥🔥🔥",
        "timestamp": "2024-01-15T10:30:00Z",
        "likes": 245
    },
    {
        "id": "comment_124",
        "username": "fan_user_002",
        "text": "Legend! 001 for life",
        "timestamp": "2024-01-15T10:31:00Z",
        "likes": 89
    }
    // ... 22,898 more comments
]
```

### Step 4: Analyzer Service Processes Comments

The **Analyzer Service** reads each comment and determines if it's positive, negative, or neutral:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYZER SERVICE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  HYBRID APPROACH (Cost-Effective):                               │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ STEP A: Local Analysis (FREE - runs on your server)      │    │
│  │                                                          │    │
│  │ For EACH comment:                                        │    │
│  │ 1. Check for Nigerian positive words:                    │    │
│  │    omo, correct, fire, goat, legend, boss, 001, etc.     │    │
│  │                                                          │    │
│  │ 2. Check for Nigerian negative words:                    │    │
│  │    werey, mumu, ode, fake, rubbish, nonsense, etc.       │    │
│  │                                                          │    │
│  │ 3. Check emojis:                                         │    │
│  │    Positive: 🔥💯❤️😍🙌👏✨💪🏆👑                         │    │
│  │    Negative: 😡🤮👎💩😤😠🤡💔                            │    │
│  │                                                          │    │
│  │ 4. Use TextBlob for English sentiment                    │    │
│  │                                                          │    │
│  │ 5. Combine signals → positive/negative/neutral           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ STEP B: Claude AI Summary (Costs ~$0.05)                 │    │
│  │                                                          │    │
│  │ Send to Claude:                                          │    │
│  │ - Statistics (75% positive, 1% negative, 24% neutral)    │    │
│  │ - Sample of 100 interesting comments                     │    │
│  │                                                          │    │
│  │ Claude generates:                                        │    │
│  │ - Catchy headline in Nigerian style                      │    │
│  │ - Vibe summary (2-3 sentences)                           │    │
│  │ - Key themes                                             │    │
│  │ - Spicy take / hot observation                           │    │
│  │ - Controversy level (chill/mid/wahala)                   │    │
│  │ - Recommended hashtags                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Output**: Analysis results:
```json
{
    "stats": {
        "total": 22900,
        "positive": 17175,
        "negative": 229,
        "neutral": 5496,
        "positive_pct": 75.0,
        "negative_pct": 1.0,
        "neutral_pct": 24.0
    },
    "summary": {
        "headline": "Davido Post Scatter Internet - Fans No Gree Rest!",
        "vibe_summary": "OBO don capture everybody heart again o! The streets dey totally behind am, 75% pure love from the comment section. Na only small small haters dey shake body.",
        "spicy_take": "Even the people wey say dem no like Davido still dey comment - that na influence!",
        "controversy_level": "chill",
        "themes": ["support", "GOAT status", "30BG loyalty", "music appreciation"],
        "recommended_hashtags": ["Davido", "OBO", "30BG", "NaijaMusic", "Afrobeats"]
    },
    "top_comments": {
        "positive": [...],
        "negative": [...],
        "notable": [...]
    }
}
```

### Step 5: Results Stored in Database

All results are saved to the PostgreSQL database:

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATABASE TABLES                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  celebrities          - Tracked celebrities (Davido, Wizkid...)  │
│       │                                                          │
│       ▼                                                          │
│  posts                - Instagram posts being analyzed           │
│       │                                                          │
│       ▼                                                          │
│  comments             - All scraped comments (anonymized)        │
│       │                                                          │
│       ▼                                                          │
│  analyses             - Sentiment analysis results               │
│       │                                                          │
│       ▼                                                          │
│  generated_content    - Ready-to-publish content                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 6: Frontend Dashboard Displays Results

Users access the **Frontend Dashboard** to view results:

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND DASHBOARD                            │
│                    (Next.js Web App)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pages:                                                          │
│                                                                  │
│  /                    - Dashboard overview                       │
│  /celebrities         - List of tracked celebrities              │
│  /posts               - Recent posts being analyzed              │
│  /analysis            - Detailed analysis results                │
│  /content             - Generated content ready to publish       │
│  /publishing          - Schedule and publish content             │
│  /analytics           - Performance metrics                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**What users see on the Analysis page:**

```
┌─────────────────────────────────────────────────────────────────┐
│  NAIJA VIBE CHECK RESULTS                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📊 Davido - Post Analysis                                       │
│  🔗 instagram.com/p/DULsWrPjwef/                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  HEADLINE                                                │    │
│  │  "Davido Post Scatter Internet - Fans No Gree Rest!"     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  SENTIMENT BREAKDOWN                                             │
│  ┌──────────────────────────────────────────────┐               │
│  │ ████████████████████████░░░░░░░░ 75% Positive │               │
│  │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  1% Negative │               │
│  │ ████████░░░░░░░░░░░░░░░░░░░░░░░░ 24% Neutral  │               │
│  └──────────────────────────────────────────────┘               │
│                                                                  │
│  Comments Analyzed: 22,900                                       │
│  Controversy Level: CHILL 😎                                     │
│                                                                  │
│  TOP POSITIVE COMMENTS:                                          │
│  • "OBO na the GOAT 🔥🔥🔥" - @fan_001                           │
│  • "Legend! 001 for life" - @fan_002                             │
│  • "Best artist in Africa no cap" - @fan_003                     │
│                                                                  │
│  THEMES: #support #GOATstatus #30BGloyalty #music                │
│                                                                  │
│  [Generate Content]  [Schedule Post]  [Export Report]            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 7: Content Generation (Optional)

If the admin clicks "Generate Content", the system creates publishable graphics:

```
┌─────────────────────────────────────────────────────────────────┐
│                 CONTENT GENERATOR SERVICE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Creates:                                                        │
│  1. Instagram carousel images with stats                         │
│  2. Caption with hashtags                                        │
│  3. Story-ready graphics                                         │
│                                                                  │
│  Example output:                                                 │
│  ┌─────────────────────┐                                        │
│  │  ┌───────────────┐  │                                        │
│  │  │   DAVIDO      │  │  Image 1: Celebrity name + headline    │
│  │  │  VIBE CHECK   │  │                                        │
│  │  └───────────────┘  │                                        │
│  │                     │                                        │
│  │  ┌───────────────┐  │                                        │
│  │  │  75% POSITIVE │  │  Image 2: Sentiment stats              │
│  │  │   1% NEGATIVE │  │                                        │
│  │  └───────────────┘  │                                        │
│  │                     │                                        │
│  │  ┌───────────────┐  │                                        │
│  │  │ TOP COMMENTS  │  │  Image 3: Best comments                │
│  │  │  "OBO na..."  │  │                                        │
│  │  └───────────────┘  │                                        │
│  └─────────────────────┘                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Step 8: Publishing (Optional)

The **Publisher Service** can automatically post to Instagram:

```
┌─────────────────────────────────────────────────────────────────┐
│                   PUBLISHER SERVICE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Login to NaijaVibeCheck Instagram page                       │
│  2. Upload generated carousel images                             │
│  3. Add caption with hashtags                                    │
│  4. Post at optimal time (calculated for Nigerian audience)      │
│  5. Track engagement after posting                               │
│                                                                  │
│  Optimal posting times for Nigeria:                              │
│  - Weekdays: 12pm-2pm, 7pm-9pm                                   │
│  - Weekends: 10am-12pm, 6pm-10pm                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### Backend Services (Python/FastAPI)

| Service | Location | Purpose |
|---------|----------|---------|
| **Browser Scraper** | `app/services/scraper/browser_scraper.py` | Login to Instagram, fetch comments via GraphQL |
| **Robust Scraper** | `app/services/scraper/robust_scraper.py` | Handle rate limits, retries, checkpoints |
| **Cost-Effective Analyzer** | `app/services/analyzer/cost_effective_analyzer.py` | Local sentiment + Claude summary |
| **Vibe Check Pipeline** | `app/services/vibe_check_pipeline.py` | Orchestrates the full flow |
| **Content Generator** | `app/services/generator/` | Creates publishable images |
| **Publisher** | `app/services/publisher/` | Posts to Instagram |

### Background Workers (Celery)

| Worker | Location | Purpose |
|--------|----------|---------|
| **Scraping Tasks** | `app/workers/scraping_tasks.py` | Run scraping jobs in background |
| **Analysis Tasks** | `app/workers/analysis_tasks.py` | Run analysis jobs in background |
| **Publishing Tasks** | `app/workers/publishing_tasks.py` | Schedule and publish content |

### Frontend (Next.js)

| Page | Location | Purpose |
|------|----------|---------|
| **Dashboard** | `src/app/page.tsx` | Overview of all activity |
| **Celebrities** | `src/app/celebrities/page.tsx` | Manage tracked celebrities |
| **Posts** | `src/app/posts/page.tsx` | View posts being analyzed |
| **Analysis** | `src/app/analysis/page.tsx` | Detailed analysis results |
| **Content** | `src/app/content/page.tsx` | Generated content library |
| **Publishing** | `src/app/publishing/page.tsx` | Schedule posts |

---

## Background Services

### How Background Jobs Work

NaijaVibeCheck uses **Celery** for background processing. This allows long-running tasks (like scraping 100,000 comments) to run without blocking the web server.

```
┌─────────────────────────────────────────────────────────────────┐
│                    BACKGROUND JOB SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User clicks                                                    │
│   "Start Analysis"                                               │
│        │                                                         │
│        ▼                                                         │
│   ┌─────────┐     ┌─────────┐     ┌─────────────────┐           │
│   │   API   │ ──▶ │  Redis  │ ──▶ │  Celery Worker  │           │
│   │ Server  │     │ (Queue) │     │  (Background)   │           │
│   └─────────┘     └─────────┘     └─────────────────┘           │
│        │                                 │                       │
│        │ Returns immediately:            │ Runs for minutes      │
│        │ "Job started, ID: abc123"       │ or hours...           │
│        │                                 │                       │
│        ▼                                 ▼                       │
│   User can check                   Saves results                 │
│   progress anytime                 to database                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Job Types

#### 1. Scraping Job
```python
# Triggered by API or scheduler
@celery_app.task
def scrape_post_comments(shortcode: str, max_comments: int = 0):
    """
    Scrapes all comments from an Instagram post.

    - Can take minutes to hours depending on comment count
    - Saves progress checkpoints every 500 comments
    - Can resume if interrupted
    - Respects rate limits automatically
    """
    scraper = RobustInstagramScraper()
    result = await scraper.scrape_all_comments(shortcode, max_comments)
    save_to_database(result)
    return result
```

#### 2. Analysis Job
```python
@celery_app.task
def analyze_comments(post_id: str, use_cost_effective: bool = True):
    """
    Analyzes sentiment of all comments for a post.

    - Processes comments in batches
    - Uses local analysis (free) + Claude summary (~$0.05)
    - Saves results to database
    """
    comments = get_comments_from_database(post_id)
    analyzer = CostEffectiveAnalyzer()
    result = await analyzer.full_analysis(comments)
    save_analysis_to_database(result)
    return result
```

#### 3. Full Pipeline Job
```python
@celery_app.task
def run_full_vibe_check(shortcode: str, celebrity_name: str):
    """
    Runs the complete pipeline:
    1. Scrape comments
    2. Analyze sentiment
    3. Generate summary
    4. Save results

    Can run overnight for posts with millions of comments.
    """
    pipeline = VibeCheckPipeline()
    result = await pipeline.run_full_analysis(
        shortcode=shortcode,
        celebrity_name=celebrity_name,
        cost_effective=True
    )
    return result
```

### Scheduled Jobs (Celery Beat)

The system can automatically check for new posts:

```python
# Runs every 6 hours
@celery_app.task
def check_tracked_celebrities():
    """
    Checks all tracked celebrities for new posts.
    If new post found, starts analysis automatically.
    """
    celebrities = get_tracked_celebrities()
    for celeb in celebrities:
        new_posts = check_for_new_posts(celeb.instagram_username)
        for post in new_posts:
            run_full_vibe_check.delay(post.shortcode, celeb.name)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              COMPLETE DATA FLOW                              │
└─────────────────────────────────────────────────────────────────────────────┘

    INSTAGRAM                    NAIJAVIBECHECK                      USERS
    ─────────                    ──────────────                      ─────

    ┌─────────┐
    │Celebrity│
    │  Post   │
    └────┬────┘
         │
         │ 1. Scraper fetches
         │    comments via API
         ▼
    ┌─────────┐         ┌──────────────┐
    │ 22,900  │────────▶│   SCRAPER    │
    │Comments │         │   SERVICE    │
    └─────────┘         └──────┬───────┘
                               │
                               │ 2. Raw comments saved
                               ▼
                        ┌──────────────┐
                        │   DATABASE   │
                        │  (comments   │
                        │   table)     │
                        └──────┬───────┘
                               │
                               │ 3. Analyzer reads comments
                               ▼
                        ┌──────────────┐
                        │   ANALYZER   │
                        │   SERVICE    │
                        │              │
                        │ Local: FREE  │
                        │ Claude: $0.05│
                        └──────┬───────┘
                               │
                               │ 4. Results saved
                               ▼
                        ┌──────────────┐
                        │   DATABASE   │
                        │  (analyses   │
                        │   table)     │
                        └──────┬───────┘
                               │
                               │ 5. API serves results
                               ▼
                        ┌──────────────┐         ┌──────────────┐
                        │   FASTAPI    │────────▶│   FRONTEND   │
                        │   BACKEND    │         │  DASHBOARD   │
                        └──────────────┘         └──────┬───────┘
                                                        │
                                                        │ 6. Users view
                                                        │    results
                                                        ▼
                                                 ┌──────────────┐
                                                 │    USERS     │
                                                 │  (Browsers)  │
                                                 └──────────────┘

    OPTIONAL: Auto-publish to Instagram page
    ─────────────────────────────────────────

                        ┌──────────────┐
                        │  GENERATOR   │
                        │   SERVICE    │
                        └──────┬───────┘
                               │
                               │ Creates images
                               ▼
                        ┌──────────────┐
                        │  PUBLISHER   │
                        │   SERVICE    │
                        └──────┬───────┘
                               │
                               │ Posts to Instagram
                               ▼
                        ┌──────────────┐
                        │ NAIJAVIBECHECK│
                        │ INSTAGRAM    │
                        │    PAGE      │
                        └──────────────┘
```

---

## Cost Structure

### Per-Analysis Costs

| Component | Cost | Notes |
|-----------|------|-------|
| Instagram Scraping | $0 | Free (uses your server) |
| Local Sentiment Analysis | $0 | Free (TextBlob + keywords) |
| Claude AI Summary | ~$0.05 | One API call per analysis |
| **TOTAL per analysis** | **~$0.05-0.10** | Regardless of comment count |

### Comparison with Full AI Analysis

| Comment Count | Full Claude Analysis | NaijaVibeCheck Hybrid |
|---------------|---------------------|----------------------|
| 1,000 | ~$1 | ~$0.05 |
| 10,000 | ~$9 | ~$0.05 |
| 100,000 | ~$90 | ~$0.10 |
| 1,000,000 | ~$900 | ~$0.10 |

**99% cost savings** using the hybrid approach!

---

## Running the System

### Prerequisites

1. **Docker** installed
2. **Instagram scraper account** (throwaway account for scraping)
3. **Anthropic API key** (for Claude AI)

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/aydeggy-dot/naijavibecheck.git
cd naijavibecheck

# 2. Create environment file
cp .env.example .env
# Edit .env with your credentials

# 3. Start all services
docker-compose up -d

# 4. Access the dashboard
open http://localhost:3000
```

### Environment Variables

```env
# Required
ANTHROPIC_API_KEY=sk-ant-xxxxx          # For Claude AI
INSTAGRAM_SCRAPER_USERNAME=your_account  # For scraping (throwaway)
INSTAGRAM_SCRAPER_PASSWORD=your_password

# Optional (for auto-publishing)
INSTAGRAM_PAGE_USERNAME=naijavibecheck   # Your main page
INSTAGRAM_PAGE_PASSWORD=your_password

# Infrastructure (defaults work for Docker)
DATABASE_URL=postgresql://user:pass@localhost:5432/naijavibecheck
REDIS_URL=redis://localhost:6379/0
```

### Manual Analysis (Python)

```python
from app.services.vibe_check_pipeline import VibeCheckPipeline

# Create pipeline
pipeline = VibeCheckPipeline()

# Run analysis
result = await pipeline.run_full_analysis(
    shortcode="DULsWrPjwef",      # From Instagram URL
    celebrity_name="Davido",
    cost_effective=True           # Use hybrid approach
)

# Print report
report = pipeline.get_publishable_report(result)
print(report)
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/analysis/start` | POST | Start new analysis |
| `/api/v1/analysis/{id}` | GET | Get analysis status/results |
| `/api/v1/celebrities` | GET/POST | Manage tracked celebrities |
| `/api/v1/posts` | GET | List analyzed posts |
| `/api/v1/content/generate` | POST | Generate publishable content |

---

## Summary

NaijaVibeCheck automates the entire process of:

1. **Scraping** - Getting thousands/millions of comments from Instagram
2. **Analyzing** - Understanding the sentiment using AI (cost-effectively)
3. **Summarizing** - Creating engaging Nigerian-style headlines and insights
4. **Publishing** - Making results available to users (and optionally auto-posting)

The system is designed to be:
- **Cost-effective**: ~$0.05 per analysis instead of hundreds of dollars
- **Robust**: Handles rate limits, retries, and can resume from interruptions
- **Scalable**: Can process millions of comments by running overnight
- **Nigerian-focused**: Understands pidgin, slang, and local context

---

## Questions?

If you have questions about how any part works, check:
- `backend/app/services/` - All service code with comments
- `backend/app/workers/` - Background job definitions
- `frontend/src/app/` - Dashboard pages

Or open an issue on GitHub!
