# NaijaVibeCheck - Quickstart Guide

Get up and running in 5 minutes.

---

## What This Does

```
Instagram Post → Scrape Comments → Analyze Sentiment → Show Results
     📱              📥                 🧠                  📊
```

---

## Prerequisites

- Docker Desktop installed
- An Anthropic API key ([get one here](https://console.anthropic.com))
- A throwaway Instagram account (for scraping)

---

## Setup (5 minutes)

### Step 1: Clone & Configure

```bash
git clone https://github.com/aydeggy-dot/naijavibecheck.git
cd naijavibecheck
cp .env.example .env
```

### Step 2: Edit `.env` file

```env
# REQUIRED - Add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# REQUIRED - Instagram account for scraping (use a throwaway!)
INSTAGRAM_SCRAPER_USERNAME=your_scraper_account
INSTAGRAM_SCRAPER_PASSWORD=your_password
```

### Step 3: Start Services

```bash
docker-compose up -d
```

### Step 4: Open Dashboard

Go to: **http://localhost:3000**

---

## Run Your First Analysis

### Option A: From Dashboard

1. Go to http://localhost:3000
2. Click "New Analysis"
3. Paste Instagram post URL
4. Enter celebrity name
5. Click "Start Analysis"
6. Wait for results (check "Analysis" page)

### Option B: From Command Line

```bash
cd backend

# Run analysis on a post
python -c "
import asyncio
from app.services.vibe_check_pipeline import VibeCheckPipeline

async def main():
    pipeline = VibeCheckPipeline()
    result = await pipeline.run_full_analysis(
        shortcode='DULsWrPjwef',  # Post ID from URL
        celebrity_name='Davido'
    )
    print(pipeline.get_publishable_report(result))

asyncio.run(main())
"
```

---

## Understanding the Output

```
============================================================
NAIJA VIBE CHECK REPORT
============================================================

📊 POST: Davido
🔗 https://www.instagram.com/p/DULsWrPjwef/

SENTIMENT BREAKDOWN:
✅ Positive: 17,175 (75.0%)
❌ Negative: 229 (1.0%)
➖ Neutral: 5,496 (24.0%)

HEADLINE: Davido Post Scatter Internet - Fans No Gree Rest!

VIBE SUMMARY:
OBO don capture everybody heart again o! The streets dey
totally behind am, 75% pure love from the comment section.

CONTROVERSY LEVEL: CHILL 😎

============================================================
```

---

## How Much Does It Cost?

| What | Cost |
|------|------|
| Scraping comments | FREE |
| Local sentiment analysis | FREE |
| Claude AI summary | ~$0.05 |
| **Total per analysis** | **~$0.05** |

Even for posts with 1 million comments, the cost stays around $0.10.

---

## Troubleshooting

### "Instagram login failed"
- Make sure your scraper account credentials are correct
- Try logging into Instagram manually first to clear any verification
- Use a throwaway account, not your main account

### "Anthropic API error"
- Check your API key is correct in `.env`
- Make sure you have credits in your Anthropic account

### "Database connection error"
- Make sure Docker is running: `docker-compose ps`
- Restart services: `docker-compose restart`

---

## Next Steps

- Read [HOW_IT_WORKS.md](./HOW_IT_WORKS.md) for detailed documentation
- Check `backend/app/services/` for code details
- Add more celebrities to track in the dashboard

---

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Frontend   │────▶│   Backend   │────▶│  Database   │
│  (Next.js)  │     │  (FastAPI)  │     │ (PostgreSQL)│
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Workers   │
                    │  (Celery)   │
                    └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ Scraper  │ │ Analyzer │ │Publisher │
        └──────────┘ └──────────┘ └──────────┘
```

That's it! You're ready to vibe check Nigerian celebrity posts.
