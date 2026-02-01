# NaijaVibeCheck - Project Checklist & Quick Reference

## 📋 Pre-Development Checklist

### Accounts & Services Needed
- [ ] **Instagram Accounts**
  - [ ] Main page account (@naijavibecheck or chosen name)
  - [ ] 5-10 throwaway scraper accounts (create with different emails)
  
- [ ] **API Keys**
  - [ ] Anthropic API key (claude.ai → Settings → API Keys)
  
- [ ] **Hosting** (when ready for production)
  - [ ] DigitalOcean account
  - [ ] Domain name (optional: naijavibecheck.com)

- [ ] **Proxies** (recommended)
  - [ ] Residential proxy service (Bright Data, Smartproxy, or similar)
  - [ ] Preferably Nigerian IP addresses

### Local Development Setup
- [ ] Python 3.11+
- [ ] Node.js 18+
- [ ] Docker & Docker Compose
- [ ] PostgreSQL (or use Docker)
- [ ] Redis (or use Docker)

---

## 🚀 How to Use the Prompt

### Option 1: Fresh Start with Claude Code
1. Open Claude Code in your terminal
2. Create a new project folder: `mkdir naijavibecheck && cd naijavibecheck`
3. Paste the entire prompt from `CLAUDE_CODE_PROMPT.md`
4. Claude will start building the project step by step

### Option 2: Iterative Development
Start with this shorter prompt to begin Phase 1:

```
I want to build NaijaVibeCheck - an Instagram analytics platform for Nigerian celebrities.

Start by:
1. Creating the project structure (Python FastAPI backend + Next.js dashboard)
2. Setting up Docker Compose with PostgreSQL and Redis
3. Creating the database models for: celebrities, posts, comments, analysis
4. Building a basic Instagram scraper with account rotation

Reference the full spec in CLAUDE_CODE_PROMPT.md for details.
Let's begin with the project structure.
```

---

## 🎨 Brand Quick Reference

### Suggested Names (pick one)
| Name | Instagram Handle |
|------|------------------|
| NaijaVibeCheck | @naijavibecheck |
| 9jaReacts | @9jareacts |
| NaijaTea | @naijatea |
| CommentCourt | @commentcourt |

### Color Palette
```
Primary:    #FF6B35 (Vibrant Orange)
Secondary:  #004E89 (Deep Blue)
Accent:     #FFBE0B (Yellow)
Positive:   #2EC4B6 (Teal)
Negative:   #E71D36 (Red)
Neutral:    #7B8794 (Gray)
Background: #1A1A2E (Dark Purple)
Text:       #FFFFFF (White)
```

### Tone of Voice
- Fun, meme-style, gossip-ish
- Nigerian slang welcome (omo, na wa, e choke, etc.)
- Gen Z friendly
- Not too serious

---

## 📊 Viral Thresholds (Configurable)

| Metric | Minimum Value |
|--------|--------------|
| Celebrity Followers | 1,500,000+ |
| Post Likes | 100,000+ |
| Post Comments | 25,000+ |
| Post Age | ≤ 3 days |

---

## 🔄 Workflow Overview

```
[Discovery] → [Scraping] → [Analysis] → [Generation] → [Review] → [Publishing] → [Learning]
     ↓            ↓            ↓             ↓            ↓            ↓            ↓
  Find viral   Extract     Sentiment    Create      Human      Post to    Track
  posts from   comments    analysis     graphics    approval   Instagram  engagement
  celebs       (500+)      via Claude   & captions  (optional)            & optimize
```

---

## 📁 Key Files Reference

| File | Purpose |
|------|---------|
| `backend/app/services/scraper/` | Instagram scraping logic |
| `backend/app/services/analyzer/` | Claude AI sentiment analysis |
| `backend/app/services/generator/` | Image/video generation |
| `backend/app/services/publisher/` | Instagram posting |
| `backend/app/workers/` | Background task definitions |
| `dashboard/src/app/` | Next.js pages |

---

## ⚠️ Risk Mitigation

### Scraper Account Bans
- Rotate accounts every 50-100 requests
- Use different proxies per account
- Scrape during off-peak hours (2-6 AM Lagos)
- If banned, replace account and continue

### Rate Limiting
- Max 100 requests per account per day
- Exponential backoff on 429 errors
- Queue system prevents overload

### Copyright Protection
- Never use celebrity images directly
- Create original graphics
- Always reference "based on public comments"
- Include entertainment disclaimer

---

## 💰 Estimated Monthly Costs (Production)

| Service | Cost |
|---------|------|
| DigitalOcean Droplet (4GB) | $24 |
| Managed PostgreSQL | $15 |
| Spaces (storage) | $5 |
| Anthropic API | $50-150 |
| Proxies (residential) | $50-100 |
| **Total** | **~$150-300/month** |

---

## 🎯 Quick Commands

### Development
```bash
# Start all services
docker-compose up -d

# Run backend
cd backend && uvicorn app.main:app --reload

# Run dashboard
cd dashboard && npm run dev

# Run Celery workers
celery -A app.workers.celery_app worker -l info
```

### Database
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Run migrations
alembic upgrade head
```

---

## ✅ Definition of Done (MVP)

The MVP is complete when:
- [ ] Can discover Nigerian celebrities automatically
- [ ] Can detect viral posts (100k+ likes, 25k+ comments)
- [ ] Can extract 500+ comments from a post
- [ ] Can analyze sentiment with 80%+ accuracy
- [ ] Can generate a stats card image
- [ ] Can generate a carousel (4 slides)
- [ ] Can post to Instagram
- [ ] Dashboard shows content queue
- [ ] Dashboard allows approve/reject
- [ ] System runs for 24 hours without crashing
