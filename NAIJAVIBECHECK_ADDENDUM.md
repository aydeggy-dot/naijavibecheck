# 🚀 NaijaVibeCheck - Feature Expansion Addendum

## ⚠️ IMPORTANT: This is an ADDENDUM to the existing NaijaVibeCheck project

This document extends the existing NaijaVibeCheck codebase with additional AI-powered features. **Do not start a new project** - integrate these features into the existing architecture.

**Reference:** This builds upon the original `CLAUDE_CODE_PROMPT.md` specification.

---

## 📋 New Features to Add

### Feature Summary Table

| # | Feature Name | Type | Priority | Effort |
|---|--------------|------|----------|--------|
| 1 | **Wahala Detector** | Drama Detection | 🔴 HIGH | Medium |
| 2 | **Predict the Outcome** | Interactive Polls | 🔴 HIGH | Low |
| 3 | **Fanbase Wars** | Analytics | 🔴 HIGH | Medium |
| 4 | **Comment of the Week Awards** | Gamification | 🔴 HIGH | Low |
| 5 | **Who Said It? Quiz** | Daily Game | 🔴 HIGH | Low |
| 6 | **Subliminal Decoder** | Drama Detection | 🟡 MEDIUM | Medium |
| 7 | **AI Gist Narrator** | Video Content | 🟡 MEDIUM | High |
| 8 | **Drama Timeline (Receipts)** | Content | 🟡 MEDIUM | High |
| 9 | **Vibe Match** | Analytics | 🟡 MEDIUM | Medium |
| 10 | **Your Comment Roast** | Interactive | 🟡 MEDIUM | Low |
| 11 | **Fan Translation Service** | Content | 🟡 MEDIUM | Low |
| 12 | **Relationship Tracker** | Monitoring | 🟢 LOW | High |
| 13 | **Engagement Predictor** | Analytics | 🟢 LOW | High |
| 14 | **Comment Simulator** | Content | 🟢 LOW | Low |

---

## 🗄️ Additional Database Tables

Add these tables to the existing database schema:

```sql
-- ============================================
-- DRAMA & WAHALA DETECTION
-- ============================================

-- Drama events detected by the system
CREATE TABLE drama_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL, -- 'beef', 'shade', 'subliminal', 'breakup', 'clash'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'nuclear'
    status VARCHAR(20) DEFAULT 'developing', -- 'developing', 'peaked', 'resolved', 'ongoing'
    
    -- Involved parties
    primary_celebrity_id UUID REFERENCES celebrities(id),
    secondary_celebrity_id UUID REFERENCES celebrities(id),
    involved_celebrity_ids UUID[], -- For multi-party drama
    
    -- Evidence
    trigger_post_id UUID REFERENCES posts(id),
    related_post_ids UUID[],
    evidence_summary TEXT,
    
    -- Metrics
    wahala_score FLOAT, -- 0-100, how serious is this
    virality_score FLOAT,
    
    -- Timestamps
    detected_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    peaked_at TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- AI analysis
    ai_summary TEXT,
    ai_prediction TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Drama timeline events (for Receipts feature)
CREATE TABLE drama_timeline_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drama_event_id UUID REFERENCES drama_events(id),
    entry_type VARCHAR(50), -- 'post', 'comment', 'unfollow', 'subliminal', 'response'
    celebrity_id UUID REFERENCES celebrities(id),
    description TEXT NOT NULL,
    evidence_url TEXT,
    evidence_screenshot_url TEXT,
    occurred_at TIMESTAMP NOT NULL,
    added_at TIMESTAMP DEFAULT NOW(),
    ai_interpretation TEXT,
    importance_score FLOAT DEFAULT 5.0 -- 1-10
);

-- ============================================
-- FANBASE TRACKING
-- ============================================

-- Fanbase profiles
CREATE TABLE fanbases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    celebrity_id UUID REFERENCES celebrities(id) UNIQUE,
    fanbase_name VARCHAR(100), -- '30BG', 'Wizkid FC', 'Titans', etc.
    
    -- Personality metrics (updated periodically)
    toxicity_score FLOAT DEFAULT 0.5, -- 0-1
    loyalty_score FLOAT DEFAULT 0.5, -- 0-1
    humor_score FLOAT DEFAULT 0.5, -- 0-1
    defensiveness_score FLOAT DEFAULT 0.5, -- 0-1
    creativity_score FLOAT DEFAULT 0.5, -- 0-1
    
    -- Stats
    total_comments_analyzed INTEGER DEFAULT 0,
    positive_comment_ratio FLOAT,
    negative_comment_ratio FLOAT,
    
    -- Common phrases/behaviors
    common_phrases TEXT[],
    common_emojis TEXT[],
    
    -- AI-generated profile
    personality_summary TEXT,
    
    last_updated TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Fanbase war events
CREATE TABLE fanbase_wars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fanbase_a_id UUID REFERENCES fanbases(id),
    fanbase_b_id UUID REFERENCES fanbases(id),
    trigger_event TEXT,
    trigger_post_id UUID REFERENCES posts(id),
    
    -- Battle stats
    fanbase_a_comment_count INTEGER DEFAULT 0,
    fanbase_b_comment_count INTEGER DEFAULT 0,
    fanbase_a_toxicity FLOAT,
    fanbase_b_toxicity FLOAT,
    
    -- Winner determination
    winner_fanbase_id UUID REFERENCES fanbases(id),
    winning_reason TEXT,
    
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'ended', 'legendary'
    
    ai_commentary TEXT,
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- GAMES & INTERACTIVE FEATURES
-- ============================================

-- Daily quiz questions (Who Said It?)
CREATE TABLE quiz_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_type VARCHAR(50) DEFAULT 'who_said_it', -- 'who_said_it', 'which_post', 'predict'
    
    -- The comment/content being quizzed
    featured_comment_id UUID REFERENCES comments(id),
    correct_post_id UUID REFERENCES posts(id),
    correct_celebrity_id UUID REFERENCES celebrities(id),
    
    -- Multiple choice options (post IDs or celebrity IDs)
    option_ids UUID[] NOT NULL,
    correct_option_index INTEGER NOT NULL,
    
    -- Display
    question_text TEXT NOT NULL,
    hint_text TEXT,
    reveal_text TEXT, -- Shown after answer
    
    -- Scheduling
    scheduled_for DATE,
    published_at TIMESTAMP,
    reveal_published_at TIMESTAMP,
    
    -- Engagement
    total_responses INTEGER DEFAULT 0,
    correct_responses INTEGER DEFAULT 0,
    
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'scheduled', 'live', 'revealed', 'archived'
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- User quiz responses (anonymous tracking)
CREATE TABLE quiz_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_question_id UUID REFERENCES quiz_questions(id),
    selected_option_index INTEGER NOT NULL,
    is_correct BOOLEAN NOT NULL,
    response_source VARCHAR(50), -- 'instagram_poll', 'story_quiz', 'dm'
    responded_at TIMESTAMP DEFAULT NOW()
);

-- Prediction polls
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_type VARCHAR(50), -- 'beef_outcome', 'relationship', 'viral', 'response'
    
    -- Context
    related_drama_id UUID REFERENCES drama_events(id),
    related_celebrity_ids UUID[],
    
    -- The prediction
    question_text TEXT NOT NULL,
    options JSONB NOT NULL, -- [{id, text, emoji}]
    
    -- AI's prediction
    ai_predicted_option_id VARCHAR(50),
    ai_confidence FLOAT, -- 0-1
    ai_reasoning TEXT,
    
    -- Outcome
    actual_outcome_option_id VARCHAR(50),
    outcome_explanation TEXT,
    outcome_verified_at TIMESTAMP,
    
    -- Engagement
    total_votes INTEGER DEFAULT 0,
    votes_per_option JSONB DEFAULT '{}',
    
    -- Scheduling
    poll_opens_at TIMESTAMP,
    poll_closes_at TIMESTAMP,
    outcome_deadline TIMESTAMP, -- When we expect to know the answer
    
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'open', 'closed', 'resolved'
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- AWARDS SYSTEM
-- ============================================

-- Award categories
CREATE TABLE award_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    emoji VARCHAR(10),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0
);

-- Insert default categories
INSERT INTO award_categories (name, slug, emoji, description, sort_order) VALUES
('The Shakespeare', 'shakespeare', '🏆', 'Most eloquent drag of the week', 1),
('Comedy Gold', 'comedy-gold', '😂', 'Funniest comment that had everyone dying', 2),
('Violation of the Week', 'violation', '💀', 'Most brutal roast - no survivors', 3),
('Stan of the Week', 'stan', '🥰', 'Most dedicated supporter showing love', 4),
('Clown Award', 'clown', '🤡', 'Most delusional take of the week', 5),
('Ratio King', 'ratio', '🔥', 'Reply that got more likes than the original', 6),
('Prophet Award', 'prophet', '🔮', 'Comment that aged like fine wine', 7),
('Wahala Starter', 'wahala', '🚨', 'Comment that sparked the most drama', 8);

-- Weekly award nominations
CREATE TABLE award_nominations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES award_categories(id),
    comment_id UUID REFERENCES comments(id),
    week_start DATE NOT NULL, -- Monday of the award week
    
    -- Nomination details
    nominated_reason TEXT,
    ai_score FLOAT, -- How strongly AI recommends this
    
    -- Voting
    vote_count INTEGER DEFAULT 0,
    
    -- Status
    is_winner BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'nominated', -- 'nominated', 'finalist', 'winner', 'rejected'
    
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- SUBLIMINAL DETECTION
-- ============================================

-- Detected subliminals
CREATE TABLE subliminals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID REFERENCES posts(id),
    celebrity_id UUID REFERENCES celebrities(id), -- Who posted
    
    -- Detection
    suspicious_text TEXT NOT NULL, -- The caption/text analyzed
    detected_phrases TEXT[], -- Specific phrases flagged
    
    -- AI Analysis
    is_subliminal_probability FLOAT, -- 0-1
    likely_target_celebrity_id UUID REFERENCES celebrities(id),
    likely_target_reasoning TEXT,
    context_events TEXT, -- What happened recently that makes this suspicious
    
    -- Alternative interpretations
    alternative_interpretations JSONB, -- [{target, probability, reasoning}]
    
    -- Verification
    is_confirmed BOOLEAN DEFAULT false,
    confirmed_by VARCHAR(50), -- 'response', 'insider', 'celebrity_confirmed'
    
    detected_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- RELATIONSHIP TRACKING
-- ============================================

-- Celebrity relationships
CREATE TABLE celebrity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    celebrity_a_id UUID REFERENCES celebrities(id),
    celebrity_b_id UUID REFERENCES celebrities(id),
    relationship_type VARCHAR(50), -- 'romantic', 'friendship', 'professional', 'rivalry'
    
    -- Current status
    current_status VARCHAR(50) DEFAULT 'unknown', -- 'together', 'broken_up', 'complicated', 'rumored', 'married'
    status_confidence FLOAT, -- 0-1
    
    -- Health metrics (updated regularly)
    health_score FLOAT DEFAULT 0.5, -- 0-1, higher = healthier
    
    -- Tracking signals
    last_interaction_at TIMESTAMP,
    interaction_frequency VARCHAR(20), -- 'daily', 'weekly', 'monthly', 'rare'
    mutual_follows BOOLEAN DEFAULT true,
    
    -- History
    status_history JSONB DEFAULT '[]', -- [{status, date, evidence}]
    
    first_detected TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Relationship signals (evidence)
CREATE TABLE relationship_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    relationship_id UUID REFERENCES celebrity_relationships(id),
    signal_type VARCHAR(50), -- 'comment', 'like', 'unfollow', 'follow', 'tag', 'caption_mention', 'spotted_together'
    signal_sentiment VARCHAR(20), -- 'positive', 'negative', 'neutral'
    
    description TEXT,
    evidence_url TEXT,
    
    -- Scoring
    importance_weight FLOAT DEFAULT 1.0,
    
    detected_at TIMESTAMP DEFAULT NOW()
);

-- ============================================
-- CONTENT ROASTS (Interactive Feature)
-- ============================================

-- User-submitted comments for roasting
CREATE TABLE roast_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Submission
    submitted_comment TEXT NOT NULL,
    submission_source VARCHAR(50), -- 'dm', 'form', 'story_reply'
    submitted_at TIMESTAMP DEFAULT NOW(),
    
    -- AI Roast
    roast_text TEXT,
    roast_severity VARCHAR(20), -- 'gentle', 'medium', 'spicy', 'nuclear'
    roast_score INTEGER, -- 1-10 rating of the original comment
    roast_generated_at TIMESTAMP,
    
    -- Publishing
    is_approved BOOLEAN DEFAULT false,
    is_published BOOLEAN DEFAULT false,
    published_at TIMESTAMP,
    
    metadata JSONB DEFAULT '{}'
);

-- ============================================
-- AI GIST NARRATOR (Video Content)
-- ============================================

-- Generated narration scripts
CREATE TABLE narration_scripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Source
    source_type VARCHAR(50), -- 'drama_event', 'post_analysis', 'fanbase_war', 'weekly_recap'
    source_id UUID, -- ID of the source record
    
    -- Script content
    title VARCHAR(255),
    script_text TEXT NOT NULL,
    script_style VARCHAR(50), -- 'formal', 'pidgin', 'gen_z', 'mixed'
    estimated_duration_seconds INTEGER,
    
    -- Generated media
    audio_url TEXT,
    video_url TEXT,
    thumbnail_url TEXT,
    
    -- Voice settings
    voice_id VARCHAR(100), -- ElevenLabs voice ID
    voice_style VARCHAR(50), -- 'excited', 'dramatic', 'casual'
    
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'audio_generated', 'video_generated', 'published'
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
```

---

## 📁 Additional Project Structure

Add these new files/folders to the existing project:

```
backend/app/
├── services/
│   ├── detector/                      # NEW: Drama & Wahala Detection
│   │   ├── __init__.py
│   │   ├── wahala_detector.py         # Real-time drama detection
│   │   ├── subliminal_decoder.py      # Shade/subliminal detection
│   │   ├── relationship_tracker.py    # Couple status monitoring
│   │   └── beef_classifier.py         # Classify type of drama
│   │
│   ├── games/                         # NEW: Interactive Features
│   │   ├── __init__.py
│   │   ├── quiz_generator.py          # Who Said It? quiz
│   │   ├── prediction_engine.py       # Predict the Outcome polls
│   │   ├── awards_manager.py          # Comment of the Week
│   │   └── roast_generator.py         # Your Comment Roast
│   │
│   ├── fanbase/                       # NEW: Fanbase Analytics
│   │   ├── __init__.py
│   │   ├── fanbase_profiler.py        # Build fanbase personalities
│   │   ├── fanbase_comparator.py      # Fanbase Wars comparisons
│   │   └── commenter_classifier.py    # Identify which fanbase a commenter belongs to
│   │
│   ├── narrator/                      # NEW: AI Gist Narrator
│   │   ├── __init__.py
│   │   ├── script_writer.py           # Generate narration scripts
│   │   ├── voice_generator.py         # Text-to-speech
│   │   └── video_assembler.py         # Combine audio + visuals
│   │
│   ├── generator/                     # EXTEND existing
│   │   ├── ...existing files...
│   │   ├── quiz_card_generator.py     # NEW: Quiz visual cards
│   │   ├── prediction_card_generator.py # NEW: Poll cards
│   │   ├── award_card_generator.py    # NEW: Award winner cards
│   │   ├── drama_timeline_generator.py # NEW: Timeline infographics
│   │   ├── fanbase_war_generator.py   # NEW: Comparison graphics
│   │   └── relationship_status_generator.py # NEW: Couple status cards
│   │
│   └── translator/                    # NEW: Fan Translation
│       ├── __init__.py
│       └── stan_translator.py         # Translate stan language
│
├── api/routes/
│   ├── ...existing files...
│   ├── drama.py                       # NEW: Drama/wahala endpoints
│   ├── games.py                       # NEW: Quiz, predictions, awards
│   ├── fanbases.py                    # NEW: Fanbase analytics
│   └── narrator.py                    # NEW: Video content
│
├── models/
│   ├── ...existing files...
│   ├── drama.py                       # NEW
│   ├── fanbase.py                     # NEW
│   ├── game.py                        # NEW (quiz, predictions, awards)
│   ├── relationship.py                # NEW
│   └── narration.py                   # NEW
│
└── workers/
    ├── ...existing files...
    ├── drama_detection_tasks.py       # NEW
    ├── game_tasks.py                  # NEW
    ├── fanbase_tasks.py               # NEW
    └── narration_tasks.py             # NEW

dashboard/src/app/
├── ...existing pages...
├── drama/                             # NEW: Drama Center
│   ├── page.tsx                       # Active drama list
│   ├── [id]/page.tsx                  # Drama detail + timeline
│   └── alerts/page.tsx                # Wahala alerts config
│
├── games/                             # NEW: Games Hub
│   ├── page.tsx                       # Games overview
│   ├── quiz/page.tsx                  # Who Said It? management
│   ├── predictions/page.tsx           # Predictions management
│   └── awards/page.tsx                # Weekly awards
│
├── fanbases/                          # NEW: Fanbase Analytics
│   ├── page.tsx                       # Fanbase profiles
│   ├── wars/page.tsx                  # Active/past fanbase wars
│   └── compare/page.tsx               # Side-by-side comparison
│
└── relationships/                     # NEW: Relationship Tracker
    ├── page.tsx                       # Tracked couples
    └── [id]/page.tsx                  # Relationship detail
```

---

## 🔧 New Service Implementations

### 1. Wahala Detector Service

```python
# backend/app/services/detector/wahala_detector.py

"""
Wahala Detector - Real-time Drama Detection
Monitors comments and posts for signs of brewing drama.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import anthropic
from app.config import settings
from app.models import Post, Comment, Celebrity, DramaEvent
from app.database import get_db

class WahalaDetector:
    """
    Detects drama, beef, and controversy in real-time.
    
    Detection triggers:
    1. Sudden spike in negative comments
    2. Keywords indicating drama (shade, beef, drag, etc.)
    3. Cross-mentions between feuding parties
    4. Unusual comment patterns (brigading)
    5. Celebrity unfollows/blocks
    """
    
    DRAMA_KEYWORDS_ENGLISH = [
        'shade', 'beef', 'drag', 'fake', 'liar', 'snake', 'clout',
        'jealous', 'copying', 'stealing', 'exposed', 'receipts',
        'blocked', 'unfollowed', 'subliminal', 'shot', 'diss'
    ]
    
    DRAMA_KEYWORDS_PIDGIN = [
        'wahala', 'yawa', 'gist', 'ment', 'cruise', 'las las',
        'una don see', 'e don happen', 'na wa', 'see trouble',
        'dem don start', 'wetin be this', 'abeg', 'shege'
    ]
    
    DRAMA_KEYWORDS_SLANG = [
        'the streets', 'main character', 'villain arc', 'caught in 4k',
        'ratio', 'dead', 'finished', 'ended', 'clocked', 'dragged'
    ]
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20250514"
        self.all_keywords = (
            self.DRAMA_KEYWORDS_ENGLISH + 
            self.DRAMA_KEYWORDS_PIDGIN + 
            self.DRAMA_KEYWORDS_SLANG
        )
    
    async def scan_for_drama(
        self,
        post_id: str,
        comments: List[Dict]
    ) -> Optional[Dict]:
        """
        Scan a post's comments for signs of drama.
        
        Returns drama event data if detected, None otherwise.
        """
        
        # Step 1: Quick keyword scan
        keyword_hits = self._scan_keywords(comments)
        
        # Step 2: Check sentiment spike
        sentiment_anomaly = await self._check_sentiment_anomaly(comments)
        
        # Step 3: Detect cross-mentions (e.g., "Wizkid would never")
        cross_mentions = self._detect_cross_mentions(comments)
        
        # Calculate drama probability
        drama_score = self._calculate_drama_score(
            keyword_hits, 
            sentiment_anomaly, 
            cross_mentions
        )
        
        if drama_score < 0.4:
            return None
        
        # Step 4: Deep AI analysis
        drama_analysis = await self._ai_analyze_drama(
            comments, 
            keyword_hits, 
            cross_mentions
        )
        
        return drama_analysis
    
    def _scan_keywords(self, comments: List[Dict]) -> Dict:
        """Quick scan for drama-related keywords."""
        hits = {
            'total_hits': 0,
            'keyword_frequency': {},
            'flagged_comments': []
        }
        
        for comment in comments:
            text_lower = comment['text'].lower()
            for keyword in self.all_keywords:
                if keyword in text_lower:
                    hits['total_hits'] += 1
                    hits['keyword_frequency'][keyword] = hits['keyword_frequency'].get(keyword, 0) + 1
                    hits['flagged_comments'].append({
                        'comment_id': comment['id'],
                        'text': comment['text'][:200],
                        'keyword': keyword
                    })
        
        return hits
    
    async def _check_sentiment_anomaly(self, comments: List[Dict]) -> Dict:
        """Check if negative sentiment is unusually high."""
        if not comments:
            return {'is_anomaly': False}
        
        negative_count = sum(1 for c in comments if c.get('sentiment') == 'negative')
        negative_ratio = negative_count / len(comments)
        
        # Average negative ratio is ~25%, anomaly if >40%
        return {
            'is_anomaly': negative_ratio > 0.40,
            'negative_ratio': negative_ratio,
            'severity': 'high' if negative_ratio > 0.60 else 'medium' if negative_ratio > 0.45 else 'low'
        }
    
    def _detect_cross_mentions(self, comments: List[Dict]) -> List[Dict]:
        """Detect when fans mention rival celebrities."""
        # This would use a list of known celebrity names/handles
        # and detect comparison/shade patterns
        cross_mentions = []
        
        comparison_patterns = [
            'would never', 'could never', 'better than', 'unlike',
            'at least', 'meanwhile', 'but when', 'same energy'
        ]
        
        for comment in comments:
            text_lower = comment['text'].lower()
            for pattern in comparison_patterns:
                if pattern in text_lower:
                    cross_mentions.append({
                        'comment_id': comment['id'],
                        'text': comment['text'][:200],
                        'pattern': pattern
                    })
                    break
        
        return cross_mentions
    
    def _calculate_drama_score(
        self,
        keyword_hits: Dict,
        sentiment_anomaly: Dict,
        cross_mentions: List
    ) -> float:
        """Calculate overall drama probability score (0-1)."""
        score = 0.0
        
        # Keyword contribution (max 0.3)
        if keyword_hits['total_hits'] > 20:
            score += 0.3
        elif keyword_hits['total_hits'] > 10:
            score += 0.2
        elif keyword_hits['total_hits'] > 5:
            score += 0.1
        
        # Sentiment anomaly contribution (max 0.4)
        if sentiment_anomaly.get('is_anomaly'):
            if sentiment_anomaly.get('severity') == 'high':
                score += 0.4
            elif sentiment_anomaly.get('severity') == 'medium':
                score += 0.25
            else:
                score += 0.15
        
        # Cross-mentions contribution (max 0.3)
        if len(cross_mentions) > 15:
            score += 0.3
        elif len(cross_mentions) > 8:
            score += 0.2
        elif len(cross_mentions) > 3:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _ai_analyze_drama(
        self,
        comments: List[Dict],
        keyword_hits: Dict,
        cross_mentions: List
    ) -> Dict:
        """Use Claude to deeply analyze the drama situation."""
        
        # Prepare sample comments for analysis
        sample_comments = "\n".join([
            f"- {c['text'][:150]}" 
            for c in (keyword_hits.get('flagged_comments', []) + cross_mentions)[:30]
        ])
        
        prompt = f"""You are analyzing a potentially dramatic situation on a Nigerian celebrity's Instagram post.

FLAGGED COMMENTS (showing signs of drama):
{sample_comments}

KEYWORD HITS: {keyword_hits['total_hits']} drama-related keywords found
TOP KEYWORDS: {list(keyword_hits.get('keyword_frequency', {}).keys())[:5]}

Analyze this situation and return a JSON response with:

1. "is_drama": Boolean - Is this actually drama/beef/wahala?
2. "drama_type": String - One of: "beef", "shade", "fanbase_clash", "scandal", "breakup_rumor", "call_out", "false_alarm"
3. "severity": String - "low", "medium", "high", "nuclear"
4. "title": String - Catchy headline for this drama (max 10 words, Nigerian style)
5. "summary": String - 2-3 sentence summary of what's happening
6. "involved_parties": Array - Names/descriptions of who's involved
7. "likely_cause": String - What triggered this
8. "prediction": String - How this might develop
9. "content_potential": String - "low", "medium", "high" - How good would this be for our page
10. "recommended_action": String - "monitor", "create_content_now", "wait_for_development", "skip"

Return only valid JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
    
    async def generate_wahala_alert(self, drama_data: Dict) -> Dict:
        """Generate an alert post for breaking drama."""
        
        prompt = f"""Create a "WAHALA ALERT" Instagram post for NaijaVibeCheck.

DRAMA INFO:
Title: {drama_data.get('title')}
Type: {drama_data.get('drama_type')}
Summary: {drama_data.get('summary')}
Involved: {drama_data.get('involved_parties')}

Generate:
1. "alert_headline": Catchy, dramatic headline (emoji included)
2. "alert_body": 2-3 sentences, Gen Z Nigerian style, create suspense
3. "call_to_action": Get people to follow for updates
4. "hashtags": 5-7 relevant Nigerian hashtags

Style: Fun, gossipy, use Nigerian slang naturally, create FOMO

Return as JSON only.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
```

### 2. Quiz Generator Service (Who Said It?)

```python
# backend/app/services/games/quiz_generator.py

"""
Quiz Generator - Creates "Who Said It?" daily quiz content
"""

from typing import List, Dict, Tuple
import random
from datetime import date, timedelta
import anthropic
from app.config import settings
from app.models import Comment, Post, Celebrity, QuizQuestion
from app.database import get_db

class QuizGenerator:
    """
    Generates daily "Who Said It?" quizzes.
    
    Game format:
    - Show an interesting/funny/controversial comment
    - Give 4 celebrity options
    - Followers guess which celeb's post it came from
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20250514"
    
    async def generate_daily_quiz(
        self,
        target_date: date,
        num_questions: int = 1
    ) -> List[Dict]:
        """
        Generate quiz questions for a specific date.
        """
        
        # Step 1: Find interesting comments from recent posts
        interesting_comments = await self._find_quiz_worthy_comments(limit=20)
        
        # Step 2: AI selects the best ones for quiz
        selected = await self._ai_select_best_comments(interesting_comments, num_questions)
        
        questions = []
        for comment_data in selected:
            # Step 3: Generate wrong options (other celebrities)
            options = await self._generate_options(comment_data)
            
            # Step 4: Create quiz question
            question = {
                'question_type': 'who_said_it',
                'featured_comment_id': comment_data['comment_id'],
                'correct_post_id': comment_data['post_id'],
                'correct_celebrity_id': comment_data['celebrity_id'],
                'question_text': self._format_question_text(comment_data['text']),
                'options': options,
                'correct_option_index': options['correct_index'],
                'hint_text': comment_data.get('hint'),
                'reveal_text': self._generate_reveal_text(comment_data),
                'scheduled_for': target_date
            }
            questions.append(question)
        
        return questions
    
    async def _find_quiz_worthy_comments(self, limit: int = 20) -> List[Dict]:
        """Find comments that would make good quiz questions."""
        
        # Query for comments that are:
        # - Funny, controversial, or notable
        # - Not too identifying (don't mention celeb name directly)
        # - Recent (within last 7 days)
        
        # This would be a database query
        # For now, returning placeholder
        pass
    
    async def _ai_select_best_comments(
        self,
        comments: List[Dict],
        num_to_select: int
    ) -> List[Dict]:
        """Use AI to select the best comments for quiz."""
        
        comments_text = "\n".join([
            f"[{i+1}] Post by @{c['celebrity']}: \"{c['text'][:150]}\""
            for i, c in enumerate(comments)
        ])
        
        prompt = f"""You are selecting comments for a "Who Said It?" quiz game on NaijaVibeCheck.

AVAILABLE COMMENTS:
{comments_text}

Select the {num_to_select} BEST comments for a quiz. Good quiz comments:
- Are entertaining, funny, or spicy
- Don't directly mention the celebrity's name
- Could plausibly be on multiple celebs' posts
- Would make people think before guessing
- Are appropriate (no extreme content)

Return JSON array with:
[
  {{
    "index": <comment number>,
    "reason": "<why this is good for quiz>",
    "difficulty": "easy" | "medium" | "hard",
    "hint": "<optional hint without giving away answer>"
  }}
]
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        selections = json.loads(response.content[0].text)
        
        # Map back to original comments
        selected_comments = []
        for sel in selections:
            idx = sel['index'] - 1
            if 0 <= idx < len(comments):
                comments[idx]['hint'] = sel.get('hint')
                comments[idx]['difficulty'] = sel.get('difficulty')
                selected_comments.append(comments[idx])
        
        return selected_comments
    
    async def _generate_options(self, comment_data: Dict) -> Dict:
        """Generate multiple choice options (1 correct + 3 wrong)."""
        
        correct_celeb = comment_data['celebrity_id']
        
        # Get 3 other celebrities in similar category
        # This would be a database query
        wrong_options = await self._get_similar_celebrities(
            correct_celeb,
            exclude=[correct_celeb],
            count=3
        )
        
        # Combine and shuffle
        all_options = [
            {'id': correct_celeb, 'name': comment_data['celebrity_name']}
        ] + wrong_options
        
        random.shuffle(all_options)
        correct_index = next(
            i for i, opt in enumerate(all_options) 
            if opt['id'] == correct_celeb
        )
        
        return {
            'options': all_options,
            'correct_index': correct_index
        }
    
    def _format_question_text(self, comment_text: str) -> str:
        """Format the comment for display as a question."""
        # Truncate if too long
        if len(comment_text) > 200:
            comment_text = comment_text[:197] + "..."
        
        return f'WHO SAID IT? 🤔\n\n"{comment_text}"'
    
    def _generate_reveal_text(self, comment_data: Dict) -> str:
        """Generate the reveal text shown after answer."""
        return (
            f"This comment was on @{comment_data['celebrity_username']}'s post! "
            f"The post had {comment_data.get('post_likes', 'thousands of')} likes. "
            f"Did you get it right? 👀"
        )
```

### 3. Awards Manager Service

```python
# backend/app/services/games/awards_manager.py

"""
Awards Manager - Comment of the Week Awards System
"""

from typing import List, Dict, Optional
from datetime import date, timedelta
import anthropic
from app.config import settings
from app.models import Comment, AwardCategory, AwardNomination
from app.database import get_db

class AwardsManager:
    """
    Manages weekly "Comment of the Week" awards.
    
    Categories:
    - The Shakespeare (most eloquent drag)
    - Comedy Gold (funniest comment)
    - Violation of the Week (most brutal roast)
    - Stan of the Week (most dedicated supporter)
    - Clown Award (most delusional take)
    - Ratio King (best ratio)
    - Prophet Award (comment that aged well)
    - Wahala Starter (sparked the most drama)
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20250514"
    
    async def nominate_comments_for_week(
        self,
        week_start: date
    ) -> Dict[str, List[Dict]]:
        """
        Analyze all comments from the week and nominate for each category.
        """
        
        week_end = week_start + timedelta(days=7)
        
        # Get all notable comments from the week
        comments = await self._get_weeks_notable_comments(week_start, week_end)
        
        # AI nominates for each category
        nominations = await self._ai_nominate_all_categories(comments)
        
        return nominations
    
    async def _ai_nominate_all_categories(
        self,
        comments: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """Use AI to nominate comments for all award categories."""
        
        comments_text = "\n".join([
            f"[{i+1}] @{c['username_anonymized']}: \"{c['text'][:200]}\" "
            f"(sentiment: {c.get('sentiment')}, toxicity: {c.get('toxicity_score', 0):.2f})"
            for i, c in enumerate(comments[:100])  # Limit to 100
        ])
        
        prompt = f"""You are the judge for NaijaVibeCheck's weekly "Comment of the Week" awards.

THIS WEEK'S COMMENTS:
{comments_text}

Nominate TOP 3 comments for EACH category:

1. **The Shakespeare** 🏆 - Most eloquent, well-written drag/criticism
2. **Comedy Gold** 😂 - Funniest comment (intentionally or not)
3. **Violation of the Week** 💀 - Most brutal, devastating roast
4. **Stan of the Week** 🥰 - Most dedicated, wholesome supporter
5. **Clown Award** 🤡 - Most delusional, out-of-touch take
6. **Ratio King** 🔥 - Comment that deserves the most likes (best comeback/reply energy)
7. **Wahala Starter** 🚨 - Comment most likely to start drama

Return JSON:
{{
  "shakespeare": [
    {{"index": <num>, "reason": "<why>", "winner_quote": "<shortened quote for display>"}}
  ],
  "comedy_gold": [...],
  "violation": [...],
  "stan": [...],
  "clown": [...],
  "ratio_king": [...],
  "wahala_starter": [...]
}}

Nigerian context matters! Understand pidgin, slang, and cultural references.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
    
    async def generate_award_announcement(
        self,
        category_slug: str,
        winner: Dict,
        runners_up: List[Dict]
    ) -> Dict:
        """Generate the award announcement content."""
        
        category_info = {
            'shakespeare': ('The Shakespeare', '🏆', 'Most Eloquent Drag'),
            'comedy_gold': ('Comedy Gold', '😂', 'Funniest Comment'),
            'violation': ('Violation of the Week', '💀', 'Most Brutal Roast'),
            'stan': ('Stan of the Week', '🥰', 'Most Dedicated Fan'),
            'clown': ('Clown Award', '🤡', 'Most Delusional Take'),
            'ratio_king': ('Ratio King', '🔥', 'Best Comeback Energy'),
            'wahala_starter': ('Wahala Starter', '🚨', 'Drama Catalyst')
        }
        
        name, emoji, description = category_info.get(category_slug, ('Award', '🏆', ''))
        
        prompt = f"""Create an award announcement post for NaijaVibeCheck.

AWARD: {emoji} {name}
DESCRIPTION: {description}

WINNER:
@{winner['username_anonymized']}: "{winner['text'][:150]}"
Reason: {winner['reason']}

RUNNERS UP:
{chr(10).join([f"- @{r['username_anonymized']}: \"{r['text'][:100]}\"" for r in runners_up])}

Generate:
1. "headline": Dramatic announcement headline
2. "winner_intro": Fun intro for the winner (2 sentences, Gen Z Nigerian style)
3. "caption": Full Instagram caption with winner + honorable mentions
4. "hashtags": 5-7 relevant hashtags

Style: Celebratory, funny, Nigerian slang welcome, hype up the winner!

Return as JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
```

### 4. Fanbase Profiler Service

```python
# backend/app/services/fanbase/fanbase_profiler.py

"""
Fanbase Profiler - Builds personality profiles for celebrity fanbases
"""

from typing import List, Dict
import anthropic
from app.config import settings
from app.models import Celebrity, Comment, Fanbase

class FanbaseProfiler:
    """
    Analyzes and profiles celebrity fanbases.
    
    Metrics tracked:
    - Toxicity level
    - Loyalty/defensiveness
    - Humor/meme game
    - Creativity
    - Common phrases/emojis
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20250514"
    
    async def build_fanbase_profile(
        self,
        celebrity_id: str,
        comments: List[Dict]
    ) -> Dict:
        """
        Build a comprehensive profile of a celebrity's fanbase.
        """
        
        # Aggregate basic stats
        total = len(comments)
        positive = sum(1 for c in comments if c.get('sentiment') == 'positive')
        negative = sum(1 for c in comments if c.get('sentiment') == 'negative')
        avg_toxicity = sum(c.get('toxicity_score', 0) for c in comments) / max(total, 1)
        
        # AI deep analysis
        profile = await self._ai_analyze_fanbase(comments)
        
        # Combine
        return {
            'celebrity_id': celebrity_id,
            'total_comments_analyzed': total,
            'positive_ratio': positive / max(total, 1),
            'negative_ratio': negative / max(total, 1),
            'toxicity_score': avg_toxicity,
            **profile
        }
    
    async def _ai_analyze_fanbase(self, comments: List[Dict]) -> Dict:
        """Deep AI analysis of fanbase personality."""
        
        sample_comments = "\n".join([
            f"- {c['text'][:150]}" for c in comments[:50]
        ])
        
        prompt = f"""Analyze this celebrity's fanbase based on their Instagram comments.

SAMPLE COMMENTS FROM FANS:
{sample_comments}

Create a fanbase profile with:

1. "fanbase_name_suggestion": Creative name for this fanbase if unknown (e.g., "30BG", "Titans")
2. "toxicity_score": 0.0-1.0 (how toxic/aggressive)
3. "loyalty_score": 0.0-1.0 (how ride-or-die)
4. "humor_score": 0.0-1.0 (how funny/memey)
5. "defensiveness_score": 0.0-1.0 (how quick to defend)
6. "creativity_score": 0.0-1.0 (originality of comments)
7. "common_phrases": Array of 5 phrases they often use
8. "common_emojis": Array of 5 emojis they love
9. "personality_type": One of ["Loyal Soldiers", "Meme Warriors", "Toxic Avengers", "Wholesome Stans", "Casual Fans", "Clout Chasers"]
10. "personality_summary": 2-3 sentence summary of the fanbase vibe
11. "strengths": 2-3 positive traits
12. "weaknesses": 2-3 negative traits
13. "rival_fanbase_energy": Which other fanbase they clash with most (general type)

Nigerian context important! Understand pidgin and slang.

Return as JSON only.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
    
    async def compare_fanbases(
        self,
        fanbase_a: Dict,
        fanbase_b: Dict
    ) -> Dict:
        """Generate a comparison between two fanbases for Fanbase Wars."""
        
        prompt = f"""Create a "FANBASE WARS" comparison for NaijaVibeCheck.

FANBASE A: {fanbase_a.get('fanbase_name', 'Team A')}
- Toxicity: {fanbase_a.get('toxicity_score', 0):.2f}
- Loyalty: {fanbase_a.get('loyalty_score', 0):.2f}
- Humor: {fanbase_a.get('humor_score', 0):.2f}
- Type: {fanbase_a.get('personality_type')}
- Summary: {fanbase_a.get('personality_summary')}

FANBASE B: {fanbase_b.get('fanbase_name', 'Team B')}
- Toxicity: {fanbase_b.get('toxicity_score', 0):.2f}
- Loyalty: {fanbase_b.get('loyalty_score', 0):.2f}
- Humor: {fanbase_b.get('humor_score', 0):.2f}
- Type: {fanbase_b.get('personality_type')}
- Summary: {fanbase_b.get('personality_summary')}

Generate:
1. "headline": Spicy comparison headline
2. "intro": Fun intro for the battle (2 sentences)
3. "category_winners": For each category, who wins and why
   - "toxicity_winner": Which fanbase is more toxic
   - "loyalty_winner": Which fanbase is more loyal
   - "humor_winner": Which fanbase is funnier
   - "overall_winner": Overall champion
4. "commentary": Witty 2-3 sentence commentary on the battle
5. "controversial_take": One spicy opinion that will get people debating
6. "caption": Full Instagram caption

Style: Fun, provocative (but not mean), encourage debate!

Return as JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
```

### 5. Prediction Engine Service

```python
# backend/app/services/games/prediction_engine.py

"""
Prediction Engine - Generates "Predict the Outcome" polls
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import anthropic
from app.config import settings
from app.models import DramaEvent, Prediction

class PredictionEngine:
    """
    Generates prediction polls based on ongoing drama/situations.
    
    Prediction types:
    - Beef outcomes (who will respond, who wins)
    - Relationship status (will they break up?)
    - Viral potential (will this blow up?)
    - Celebrity actions (will they apologize, clap back, etc.)
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20250514"
    
    async def generate_prediction_from_drama(
        self,
        drama_event: Dict
    ) -> Dict:
        """
        Generate a prediction poll based on an ongoing drama event.
        """
        
        prompt = f"""Create a "PREDICT THE OUTCOME" poll for NaijaVibeCheck based on this drama.

DRAMA EVENT:
Title: {drama_event.get('title')}
Type: {drama_event.get('drama_type')}
Summary: {drama_event.get('summary')}
Involved: {drama_event.get('involved_parties')}
Current Status: {drama_event.get('status')}

Generate a prediction poll:

1. "question": The prediction question (engaging, creates suspense)
2. "options": Array of 4 possible outcomes, each with:
   - "id": Unique short ID (e.g., "opt_a")
   - "text": The option text
   - "emoji": Relevant emoji
3. "ai_prediction": Which option AI thinks is most likely
4. "ai_confidence": 0.0-1.0 confidence level
5. "ai_reasoning": Brief reasoning (don't show to users initially)
6. "outcome_deadline": Suggested date to check results (ISO format)
7. "engagement_hook": One sentence to get people voting
8. "caption": Full Instagram caption for the poll post

Style: Fun, suspenseful, make people NEED to vote!

Return as JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
    
    async def check_prediction_outcome(
        self,
        prediction: Dict,
        recent_events: List[Dict]
    ) -> Optional[Dict]:
        """
        Check if a prediction can be resolved based on recent events.
        """
        
        prompt = f"""Check if this prediction can be resolved.

ORIGINAL PREDICTION:
Question: {prediction.get('question')}
Options: {prediction.get('options')}

RECENT EVENTS:
{chr(10).join([f"- {e.get('description')}" for e in recent_events])}

Can this prediction be resolved? If yes:
1. "is_resolved": true
2. "winning_option_id": Which option won
3. "explanation": What happened that resolved it
4. "reveal_text": Fun reveal announcement

If no:
1. "is_resolved": false
2. "reason": Why it can't be resolved yet

Return as JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
```

### 6. Subliminal Decoder Service

```python
# backend/app/services/detector/subliminal_decoder.py

"""
Subliminal Decoder - Detects and interprets potential shade in captions
"""

from typing import List, Dict, Optional
import anthropic
from app.config import settings
from app.models import Post, Celebrity, Subliminal

class SubliminalDecoder:
    """
    Detects potential subliminals (shade) in celebrity captions.
    
    Detection signals:
    - Vague, pointed statements
    - Timing (posted after drama)
    - Quote tweets/reposts
    - Cryptic messages
    - Emojis used passive-aggressively
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-5-20250514"
    
    async def analyze_caption_for_subliminal(
        self,
        post: Dict,
        celebrity: Dict,
        recent_drama: List[Dict],
        recent_events: List[Dict]
    ) -> Optional[Dict]:
        """
        Analyze if a caption might be a subliminal/shade.
        """
        
        prompt = f"""Analyze if this Instagram caption might be a subliminal (shade/indirect diss).

CELEBRITY: @{celebrity.get('username')} ({celebrity.get('full_name')})

CAPTION: "{post.get('caption')}"

POSTED AT: {post.get('posted_at')}

RECENT DRAMA INVOLVING THIS CELEBRITY:
{chr(10).join([f"- {d.get('title')}: {d.get('summary')}" for d in recent_drama[:5]])}

RECENT EVENTS IN NIGERIAN ENTERTAINMENT:
{chr(10).join([f"- {e}" for e in recent_events[:5]])}

Analyze:

1. "is_potential_subliminal": true/false
2. "confidence": 0.0-1.0 (how confident this is shade)
3. "suspicious_phrases": Array of specific phrases that seem shady
4. "likely_target": Who this might be aimed at (if any)
5. "target_reasoning": Why you think it's aimed at them
6. "alternative_interpretations": Array of other possible meanings
7. "context_connection": How this connects to recent events
8. "decoder_explanation": 2-3 sentences explaining the potential shade (for our audience)

Nigerian celebrity context matters! Know the beefs, relationships, and dynamics.

Return as JSON. If not a subliminal, still return with is_potential_subliminal: false.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        result = json.loads(response.content[0].text)
        
        # Only return if confidence is high enough
        if result.get('confidence', 0) < 0.5:
            return None
        
        return result
    
    async def generate_decoder_post(
        self,
        subliminal_data: Dict,
        celebrity: Dict,
        post: Dict
    ) -> Dict:
        """
        Generate a "SUBLIMINAL DECODED" post.
        """
        
        prompt = f"""Create a "SUBLIMINAL DECODED" Instagram post for NaijaVibeCheck.

CELEBRITY: @{celebrity.get('username')}
ORIGINAL CAPTION: "{post.get('caption')[:200]}"

ANALYSIS:
- Likely Target: {subliminal_data.get('likely_target')}
- Suspicious Phrases: {subliminal_data.get('suspicious_phrases')}
- Reasoning: {subliminal_data.get('target_reasoning')}
- Confidence: {subliminal_data.get('confidence'):.0%}

Generate:
1. "headline": Catchy headline (e.g., "🔍 SUBLIMINAL DECODED")
2. "decoded_explanation": Fun explanation of the potential shade (3-4 sentences)
3. "evidence_points": 3 bullet points of evidence
4. "alternative_take": One alternative interpretation (to be fair)
5. "engagement_question": Question to get comments (e.g., "What do you think? 👀")
6. "caption": Full Instagram caption
7. "hashtags": 5-7 relevant hashtags
8. "disclaimer": Short disclaimer that this is speculation/entertainment

Style: Detective/investigative vibe, fun, not accusatory, Nigerian slang welcome!

Return as JSON.
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            messages=[{"role": "user", "content": prompt}]
        )
        
        import json
        return json.loads(response.content[0].text)
```

---

## 🖥️ New Dashboard Pages

### Add these pages to the existing dashboard:

#### 1. Drama Center (`/drama`)
- Active drama list with severity indicators
- Wahala alerts feed
- Drama timeline viewer
- Subliminal detection queue

#### 2. Games Hub (`/games`)
- **Quiz Management** (`/games/quiz`)
  - Daily quiz queue
  - Past quizzes with stats
  - Generate new quiz
  
- **Predictions** (`/games/predictions`)
  - Active polls
  - Pending resolution
  - Accuracy tracking
  
- **Awards** (`/games/awards`)
  - This week's nominations
  - Past winners
  - Award announcement generator

#### 3. Fanbase Analytics (`/fanbases`)
- Fanbase profile cards
- Comparison tool (select 2 to compare)
- Fanbase wars history
- Toxicity leaderboard

---

## 📅 Implementation Order

### Phase 1: Core Detection (Week 1-2)
1. Wahala Detector service
2. Drama events database tables
3. Alert generation

### Phase 2: Games Foundation (Week 3-4)
1. Quiz generator service
2. Awards manager service
3. Games database tables
4. Basic dashboard pages

### Phase 3: Fanbase Analytics (Week 5-6)
1. Fanbase profiler service
2. Comparison engine
3. Fanbase dashboard

### Phase 4: Advanced Features (Week 7-8)
1. Prediction engine
2. Subliminal decoder
3. Relationship tracker

### Phase 5: Content Generation (Week 9-10)
1. Quiz card generator
2. Award card generator
3. Fanbase war graphics
4. Drama timeline graphics

### Phase 6: Polish & Integration (Week 11-12)
1. Integrate all features with main pipeline
2. Dashboard polish
3. Testing & optimization

---

## 🔧 Additional Environment Variables

Add these to your existing `.env`:

```env
# Voice Generation (for AI Gist Narrator)
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_VOICE_ID=voice_id_for_narrator

# Optional: Nigerian TTS alternative
GTTS_LANG=en
GTTS_TLD=com.ng

# Feature Flags
FEATURE_WAHALA_DETECTOR=true
FEATURE_QUIZ_GAME=true
FEATURE_AWARDS=true
FEATURE_FANBASE_WARS=true
FEATURE_PREDICTIONS=true
FEATURE_SUBLIMINAL_DECODER=true
FEATURE_AI_NARRATOR=false  # Enable when ready

# Game Settings
QUIZ_DAILY_COUNT=1
AWARD_NOMINATIONS_PER_CATEGORY=3
PREDICTION_OPTIONS_COUNT=4
```

---

## ✅ Updated Definition of Done

The expanded system is complete when:

**Core (from original):**
- [x] Discover Nigerian celebrities automatically
- [x] Detect viral posts (100k+ likes, 25k+ comments)
- [x] Extract 500+ comments from a post
- [x] Analyze sentiment with 80%+ accuracy
- [x] Generate stats card images
- [x] Generate carousels
- [x] Post to Instagram
- [x] Dashboard with content queue

**New Features:**
- [ ] Wahala Detector catches 80% of drama within 2 hours
- [ ] Daily "Who Said It?" quiz generates automatically
- [ ] Weekly awards nominate and announce winners
- [ ] Fanbase profiles exist for top 20 celebrities
- [ ] Fanbase Wars comparisons generate on demand
- [ ] Predictions create from active drama automatically
- [ ] Subliminal Decoder flags suspicious captions
- [ ] Dashboard shows drama alerts in real-time
- [ ] Games hub manages all interactive content

---

## 🎯 Success Metrics (Updated)

| Metric | Target |
|--------|--------|
| Drama detection speed | < 2 hours from start |
| Quiz engagement rate | > 15% response rate |
| Award post engagement | 2x normal post engagement |
| Fanbase Wars shares | > 500 shares per post |
| Prediction accuracy | > 60% correct |
| Follower growth | 10k+ new followers/month |

---

Now integrate these features into the existing NaijaVibeCheck codebase. Start with the database migrations, then implement services in the order specified above. Ask if you need clarification on any feature!
