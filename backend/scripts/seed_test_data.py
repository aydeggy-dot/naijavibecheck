"""Seed test data for NaijaVibeCheck."""

import asyncio
import sys
from datetime import datetime, timedelta
from uuid import uuid4
import random

# Add parent directory to path for imports
sys.path.insert(0, '/app')

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import Celebrity, Post, Comment, CommentAnalysis, PostAnalysis, GeneratedContent


def anonymize_username(username: str) -> str:
    """Anonymize username with asterisks."""
    if len(username) <= 3:
        return username[0] + "*" * (len(username) - 1)
    return username[:2] + "*" * (len(username) - 4) + username[-2:]


# Test Nigerian celebrities (fictional for testing)
TEST_CELEBRITIES = [
    {
        "instagram_username": "davido",
        "full_name": "Davido",
        "follower_count": 29_000_000,
        "category": "musician",
        "is_active": True,
        "scrape_priority": 10,
    },
    {
        "instagram_username": "wiikidzworldwide",
        "full_name": "Wizkid",
        "follower_count": 18_000_000,
        "category": "musician",
        "is_active": True,
        "scrape_priority": 10,
    },
    {
        "instagram_username": "burabornaandthem",
        "full_name": "Burna Boy",
        "follower_count": 12_000_000,
        "category": "musician",
        "is_active": True,
        "scrape_priority": 10,
    },
    {
        "instagram_username": "funaborinkoye",
        "full_name": "Funke Akindele",
        "follower_count": 16_000_000,
        "category": "actor",
        "is_active": True,
        "scrape_priority": 8,
    },
    {
        "instagram_username": "mrmacaronii",
        "full_name": "Mr Macaroni",
        "follower_count": 4_500_000,
        "category": "influencer",
        "is_active": True,
        "scrape_priority": 7,
    },
]

# Sample comments (Nigerian style)
POSITIVE_COMMENTS = [
    "E choke! This is fire! 🔥🔥🔥",
    "King don't miss! OBO forever 💪",
    "The greatest of all time, no cap!",
    "Nigeria to the world! We move different",
    "Nobody dey your level abeg 👑",
    "Baddest! Na you we go follow reach heaven",
    "This one na hit! Straight banger 💯",
    "Una too much! Keep making us proud",
    "Omo this one sweet die! Vibes only",
    "GOAT things! Legend behavior only",
    "Na you be the realest! Facts only",
    "E clear! No competition anywhere",
    "Shey you wan wound us? This is crazy good!",
    "Mad o! This one pass everything",
    "Wahala for who no support! Top tier",
]

NEGATIVE_COMMENTS = [
    "Wetin be this one now? Na wa o",
    "I no understand this content at all",
    "Person no fit rest for this Lagos? Hian",
    "Abeg shift jor, this one no sweet",
    "Make we see something else abeg",
    "E no reach sha, I expected better",
    "Why everybody dey gas this one? Average at best",
    "Na hype dey carry this one o, substance zero",
    "I tire for this kind content honestly",
    "Person need explain this one to me o",
]

NEUTRAL_COMMENTS = [
    "Okay o, we have heard",
    "Nice one sha",
    "I see am, next please",
    "No comment, just watching",
    "Interesting perspective",
]


async def seed_data():
    """Seed test data into the database."""
    print("Starting data seeding...")

    async with AsyncSessionLocal() as db:
        # Check if data already exists
        from sqlalchemy import select, func
        result = await db.execute(select(func.count(Celebrity.id)))
        count = result.scalar()

        if count > 0:
            print(f"Database already has {count} celebrities. Skipping seed.")
            return

        celebrities = []
        posts = []
        comments_data = []

        # Create celebrities
        print("Creating celebrities...")
        for celeb_data in TEST_CELEBRITIES:
            celebrity = Celebrity(
                id=uuid4(),
                **celeb_data,
                last_scraped_at=datetime.utcnow() - timedelta(hours=random.randint(1, 12)),
            )
            db.add(celebrity)
            celebrities.append(celebrity)

        await db.flush()

        # Create posts for each celebrity
        print("Creating posts...")
        for celebrity in celebrities:
            num_posts = random.randint(3, 6)
            for i in range(num_posts):
                is_viral = random.random() > 0.5
                like_count = random.randint(100000, 500000) if is_viral else random.randint(10000, 99999)
                comment_count = random.randint(5000, 30000) if is_viral else random.randint(500, 4999)
                shortcode = f"test{random.randint(100000, 999999)}"

                post = Post(
                    id=uuid4(),
                    celebrity_id=celebrity.id,
                    instagram_post_id=f"{random.randint(1000000000000000000, 9999999999999999999)}",
                    shortcode=shortcode,
                    post_url=f"https://instagram.com/p/{shortcode}",
                    caption=f"Test post {i+1} from {celebrity.full_name}. This is a sample caption for testing. #Nigeria #Naija #Test",
                    like_count=like_count,
                    comment_count=comment_count,
                    posted_at=datetime.utcnow() - timedelta(days=random.randint(0, 5), hours=random.randint(0, 23)),
                    scraped_at=datetime.utcnow(),
                    is_viral=is_viral,
                    viral_score=random.uniform(60, 95) if is_viral else random.uniform(20, 59),
                    is_analyzed=False,
                    is_processed=False,
                    metadata_={},
                )
                db.add(post)
                posts.append(post)

        await db.flush()

        # Create comments for posts
        print("Creating comments...")
        for post in posts:
            num_comments = random.randint(10, 25)
            for j in range(num_comments):
                sentiment_roll = random.random()
                if sentiment_roll < 0.6:
                    text = random.choice(POSITIVE_COMMENTS)
                    sentiment = "positive"
                elif sentiment_roll < 0.85:
                    text = random.choice(NEGATIVE_COMMENTS)
                    sentiment = "negative"
                else:
                    text = random.choice(NEUTRAL_COMMENTS)
                    sentiment = "neutral"

                username = f"user_{random.randint(100, 999)}"
                comment = Comment(
                    id=uuid4(),
                    post_id=post.id,
                    instagram_comment_id=f"{random.randint(10000000000000000, 99999999999999999)}",
                    username=username,
                    username_anonymized=anonymize_username(username),
                    text=text,
                    like_count=random.randint(0, 500),
                    commented_at=post.posted_at + timedelta(hours=random.randint(0, 24)),
                    scraped_at=datetime.utcnow(),
                    is_reply=False,
                )
                db.add(comment)
                comments_data.append((comment, sentiment))

        await db.flush()

        # Create comment analyses
        print("Creating comment analyses...")
        for comment, sentiment in comments_data:
            sentiment_score = random.uniform(0.5, 0.95) if sentiment == "positive" else (
                random.uniform(-0.95, -0.5) if sentiment == "negative" else random.uniform(-0.2, 0.2)
            )
            analysis = CommentAnalysis(
                id=uuid4(),
                comment_id=comment.id,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                toxicity_score=random.uniform(0.0, 0.3) if sentiment != "negative" else random.uniform(0.2, 0.6),
                emotion_tags=["joy", "support"] if sentiment == "positive" else (
                    ["frustration"] if sentiment == "negative" else ["neutral"]
                ),
                is_top_positive=sentiment == "positive" and random.random() > 0.7,
                is_top_negative=sentiment == "negative" and random.random() > 0.7,
                analyzed_at=datetime.utcnow(),
                analysis_metadata={},
            )
            db.add(analysis)

        await db.flush()

        # Create post analyses for viral posts
        print("Creating post analyses...")
        viral_posts = [p for p in posts if p.is_viral]
        for post in viral_posts[:5]:  # Analyze top 5 viral posts
            positive_pct = random.uniform(50, 70)
            negative_pct = random.uniform(10, 25)
            neutral_pct = 100 - positive_pct - negative_pct

            post_analysis = PostAnalysis(
                id=uuid4(),
                post_id=post.id,
                total_comments_analyzed=random.randint(15, 25),
                positive_count=int(positive_pct * 0.2),
                negative_count=int(negative_pct * 0.2),
                neutral_count=int(neutral_pct * 0.2),
                positive_percentage=positive_pct,
                negative_percentage=negative_pct,
                neutral_percentage=neutral_pct,
                average_sentiment_score=random.uniform(0.2, 0.6),
                controversy_score=random.uniform(0.1, 0.4),
                analyzed_at=datetime.utcnow(),
                ai_summary=f"This post from {post.celebrity_id} has generated strong positive engagement. Nigerian fans are showing overwhelming support with typical Naija slang expressions.",
                ai_insights={
                    "key_themes": ["support", "excitement", "pride"],
                    "slang_detected": True,
                },
            )
            db.add(post_analysis)
            await db.flush()

            # Mark post as analyzed
            post.is_analyzed = True

            # Create generated content for some analyses
            if random.random() > 0.3:
                content = GeneratedContent(
                    id=uuid4(),
                    post_analysis_id=post_analysis.id,
                    content_type=random.choice(["image", "carousel"]),
                    title=f"What Nigerians Are Saying",
                    caption="The reactions are in! Check out what the internet is saying 🇳🇬 #NaijaVibeCheck",
                    hashtags=["NaijaVibeCheck", "Nigeria", "Trending", "Viral"],
                    media_urls=["https://via.placeholder.com/1080x1080.png?text=Generated+Content"],
                    thumbnail_url="https://via.placeholder.com/640x640.png?text=Generated+Content",
                    generation_metadata={"theme": "naija_green", "template": "stats_card"},
                    status=random.choice(["pending_review", "approved", "draft"]),
                    scheduled_for=datetime.utcnow() + timedelta(hours=random.randint(1, 48)) if random.random() > 0.5 else None,
                    created_at=datetime.utcnow(),
                )
                db.add(content)

        await db.commit()
        print(f"✓ Seeded {len(celebrities)} celebrities")
        print(f"✓ Seeded {len(posts)} posts")
        print(f"✓ Seeded {len(comments_data)} comments with analyses")
        print(f"✓ Seeded post analyses and generated content")
        print("Data seeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_data())
