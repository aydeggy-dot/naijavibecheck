# NaijaVibeCheck

Nigerian celebrity Instagram analytics and content generation platform. This system monitors Nigerian celebrities' Instagram posts, analyzes comment sentiment, generates eye-catching content showcasing the analysis, and autonomously manages an Instagram page.

## Features

- **Celebrity Discovery** - Track trending Nigerian celebrities on Instagram
- **Viral Post Detection** - Identify posts meeting engagement thresholds (100K+ likes, 25K+ comments)
- **Sentiment Analysis** - AI-powered analysis using Claude API with Nigerian Pidgin/slang understanding
- **Content Generation** - Create visually stunning posts (images, carousels, reels) displaying analytics
- **Automated Publishing** - Schedule and publish content to Instagram at optimal times
- **Learning Engine** - Optimize content based on engagement patterns
- **Dashboard** - Web interface for monitoring and control

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend API | Python (FastAPI) |
| Database | PostgreSQL |
| Cache/Queue | Redis + Celery |
| AI/ML | Anthropic Claude API |
| Frontend | Next.js 16 + TypeScript + Tailwind CSS |
| Image Generation | Pillow + Cairo |
| Instagram Integration | instagrapi |
| Hosting | Docker + Docker Compose |

## Project Structure

```
naijavibecheck/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   │   └── routes/     # Endpoint handlers
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   │   ├── scraper/    # Instagram scraping
│   │   │   ├── analyzer/   # Sentiment analysis, viral detection
│   │   │   ├── generator/  # Content generation
│   │   │   └── publisher/  # Instagram publishing
│   │   ├── workers/        # Celery tasks
│   │   └── utils/          # Utilities
│   ├── alembic/            # Database migrations
│   └── tests/              # Tests
├── frontend/               # Next.js dashboard
│   ├── src/
│   │   ├── app/           # Pages (App Router)
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # Utilities
│   │   ├── services/      # API client
│   │   └── types/         # TypeScript types
├── templates/              # Visual templates for content
└── docker-compose.yml      # Docker orchestration
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 20+ (for dashboard)

### Setup

1. **Clone and configure**
   ```bash
   cd naijavibecheck
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start all services with Docker**
   ```bash
   docker-compose up -d
   ```

3. **Run database migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **Access the applications**
   - Dashboard: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development

1. **Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Run Celery Worker**
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```

3. **Run Celery Beat (scheduler)**
   ```bash
   celery -A app.workers.celery_app beat --loglevel=info
   ```

4. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## API Endpoints

### Health
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/db` - Database health

### Celebrities
- `GET /api/v1/celebrities` - List celebrities
- `POST /api/v1/celebrities` - Add celebrity
- `GET /api/v1/celebrities/{id}` - Get celebrity
- `PATCH /api/v1/celebrities/{id}` - Update celebrity
- `DELETE /api/v1/celebrities/{id}` - Delete celebrity
- `POST /api/v1/celebrities/{id}/scrape` - Trigger scraping

### Posts
- `GET /api/v1/posts` - List posts
- `GET /api/v1/posts/viral` - List viral posts
- `GET /api/v1/posts/{id}` - Get post details
- `GET /api/v1/posts/{id}/comments` - Get post comments

### Analysis
- `GET /api/v1/analysis/post/{id}` - Get post analysis
- `POST /api/v1/analysis/post/{id}/analyze` - Trigger analysis
- `GET /api/v1/analysis/recent` - Recent analyses

### Content Generation
- `POST /api/v1/generate/{post_analysis_id}` - Generate content
- `GET /api/v1/content` - List generated content
- `GET /api/v1/content/{id}` - Get content details

### Publishing
- `POST /api/v1/publish/content/{id}/schedule` - Schedule content
- `POST /api/v1/publish/content/{id}/approve` - Approve content
- `POST /api/v1/publish/content/{id}/reject` - Reject content
- `POST /api/v1/publish/content/{id}/publish` - Publish immediately
- `GET /api/v1/publish/queue` - Publishing queue
- `GET /api/v1/publish/optimal-times` - Get optimal posting times
- `GET /api/v1/publish/stats` - Publishing statistics

### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard stats
- `GET /api/v1/analytics/trending` - Trending content

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `ANTHROPIC_API_KEY` | Claude API key |
| `INSTAGRAM_PAGE_USERNAME` | Main Instagram account username |
| `INSTAGRAM_PAGE_PASSWORD` | Main Instagram account password |
| `SECRET_KEY` | Application secret key |
| `ENVIRONMENT` | `development` or `production` |

See `.env.example` for all available options.

## Development Phases

- [x] **Phase 1**: Core Infrastructure (Docker, DB, API)
- [x] **Phase 2**: Analysis Engine (sentiment, viral detection)
- [x] **Phase 3**: Content Generation (images, carousels)
- [x] **Phase 4**: Publishing System (Instagram posting)
- [x] **Phase 5**: Dashboard (Next.js frontend)
- [ ] **Phase 6**: Learning & Optimization
- [ ] **Phase 7**: Production Deployment

## Testing

```bash
# Backend tests
cd backend
pytest -v

# Frontend (type check)
cd frontend
npm run build
```

## Brand Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Nigerian Green | `#008751` | Primary, CTAs |
| White | `#FFFFFF` | Backgrounds |
| Gold | `#FFD700` | Accents, highlights |
| Coral | `#FF6B6B` | Alerts, negative |
| Dark | `#1A1A2E` | Text, sidebar |

## License

Private - All rights reserved.
