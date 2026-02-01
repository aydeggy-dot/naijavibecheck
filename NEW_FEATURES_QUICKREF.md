# NaijaVibeCheck - New Features Quick Reference

## 🚨 IMPORTANT: This is an ADDENDUM

Tell Claude Code: *"This is an extension to the existing NaijaVibeCheck project. Add these features to the existing codebase."*

---

## 📋 New Features Summary

| Feature | What It Does | Content Type |
|---------|--------------|--------------|
| **Wahala Detector** | Real-time drama/beef alerts | Alert posts, Stories |
| **Who Said It? Quiz** | Daily guessing game with comments | Quiz cards, Polls |
| **Comment Awards** | Weekly awards for best/worst comments | Award cards, Carousels |
| **Fanbase Wars** | Compare celebrity fanbases | Comparison graphics |
| **Predict the Outcome** | Polls about drama outcomes | Poll posts |
| **Subliminal Decoder** | Detect and explain shade | Decoder posts |
| **Vibe Match** | Fanbase personality profiles | Profile cards |
| **Your Comment Roast** | AI roasts fan-submitted comments | Roast cards |
| **AI Gist Narrator** | Voice/video drama summaries | Reels |
| **Drama Timeline** | Visual history of beefs | Timeline infographics |

---

## 🗄️ New Database Tables Needed

```
drama_events          - Track ongoing drama/wahala
drama_timeline_entries - Evidence for drama timelines
fanbases              - Fanbase personality profiles
fanbase_wars          - Comparison events
quiz_questions        - Daily quiz content
quiz_responses        - Anonymous response tracking
predictions           - Predict the Outcome polls
award_categories      - Award types (static)
award_nominations     - Weekly nominations
subliminals           - Detected shade
celebrity_relationships - Couple tracking
relationship_signals  - Evidence for relationships
roast_submissions     - User-submitted comments
narration_scripts     - AI narrator scripts
```

---

## 📁 New Files to Create

```
backend/app/services/
├── detector/
│   ├── wahala_detector.py      ⭐ Priority 1
│   ├── subliminal_decoder.py
│   ├── relationship_tracker.py
│   └── beef_classifier.py
├── games/
│   ├── quiz_generator.py       ⭐ Priority 1
│   ├── awards_manager.py       ⭐ Priority 1
│   ├── prediction_engine.py
│   └── roast_generator.py
├── fanbase/
│   ├── fanbase_profiler.py     ⭐ Priority 1
│   ├── fanbase_comparator.py
│   └── commenter_classifier.py
└── narrator/
    ├── script_writer.py
    ├── voice_generator.py
    └── video_assembler.py
```

---

## 🎯 Implementation Priority

### Week 1-2: HIGH PRIORITY
1. ✅ Wahala Detector - Drama is the #1 engagement driver
2. ✅ Quiz Generator - Daily habit = retention
3. ✅ Awards Manager - Weekly highlight content

### Week 3-4: HIGH PRIORITY
4. ✅ Fanbase Profiler - Foundation for comparisons
5. ✅ Fanbase Comparator - Viral potential

### Week 5-6: MEDIUM PRIORITY
6. Prediction Engine
7. Subliminal Decoder

### Week 7+: LOWER PRIORITY
8. AI Gist Narrator (complex)
9. Relationship Tracker
10. Drama Timeline Generator

---

## 🔑 Key Prompts for Claude Code

### To start integration:
```
I have an existing NaijaVibeCheck project. Please review the 
NAIJAVIBECHECK_ADDENDUM.md and integrate these new features:

1. First, create the new database migrations for all the 
   additional tables listed.

2. Then implement the Wahala Detector service as the first 
   new feature.

The existing project has: FastAPI backend, PostgreSQL, Celery, 
and the basic scraper/analyzer/generator pipeline working.
```

### To add specific feature:
```
Add the "Who Said It? Quiz" feature to NaijaVibeCheck:
1. Create the quiz_questions and quiz_responses tables
2. Implement the QuizGenerator service
3. Add the quiz card generator for visuals
4. Create the /games/quiz dashboard page
5. Set up the Celery task for daily quiz generation

Reference NAIJAVIBECHECK_ADDENDUM.md for the full specification.
```

---

## ⚡ Quick Wins (Implement First)

These features are LOW EFFORT but HIGH IMPACT:

| Feature | Why It's Quick | Impact |
|---------|----------------|--------|
| **Comment Awards** | Just AI selection + 1 template | Weekly viral content |
| **Who Said It Quiz** | Simple game logic | Daily engagement |
| **Predict the Outcome** | Poll + AI generation | Interactive content |

---

## 📊 New Content Calendar

| Day | Content Type |
|-----|--------------|
| **Monday** | Weekly Awards Announcement |
| **Daily** | Who Said It? Quiz |
| **When Drama Hits** | Wahala Alert |
| **Wednesday** | Fanbase Wars |
| **Friday** | Predictions Reveal |
| **Ongoing** | Stats cards, Subliminal Decodes |

---

## 🎨 New Visual Templates Needed

1. **Wahala Alert Card** - Red/urgent styling, breaking news vibe
2. **Quiz Card** - Question + 4 options layout
3. **Award Winner Card** - Trophy/celebration theme per category
4. **Fanbase Profile Card** - Stats + personality summary
5. **Fanbase Battle Card** - Side-by-side comparison
6. **Prediction Poll Card** - Question + voting options
7. **Subliminal Decoder Card** - Detective/magnifying glass theme

---

## ✅ Testing Checklist

Before going live with each feature:

- [ ] Drama detection triggers within 2 hours of real drama
- [ ] Quiz generates daily without manual intervention  
- [ ] Awards nominate correctly (AI picks genuinely good comments)
- [ ] Fanbase profiles are accurate and entertaining
- [ ] Predictions resolve correctly when outcome happens
- [ ] All generated images look professional
- [ ] Dashboard controls work (approve/reject/edit)
- [ ] Celery tasks run on schedule
- [ ] Error handling doesn't crash the system

---

Good luck! 🚀 These features will make NaijaVibeCheck absolutely addictive for Nigerian Gen Z!
