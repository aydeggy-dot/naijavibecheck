"""
Test Full NaijaVibeCheck Pipeline
=================================
Tests the complete flow: Analyze → Generate Content → Publish

Uses sample data to test without needing real Instagram credentials.
"""

import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from uuid import uuid4

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Sample Nigerian comments (realistic test data)
SAMPLE_COMMENTS = [
    # Positive comments
    {"text": "Davido no dey disappoint! This guy na real legend 🔥🔥🔥", "like_count": 1250},
    {"text": "OBO to the world! Always showing love to Nigeria", "like_count": 890},
    {"text": "Best artist in Africa no cap! 30BG gang where una dey? 💪", "like_count": 765},
    {"text": "This man dey carry naija flag everywhere e go. Proud of you baba!", "like_count": 654},
    {"text": "E choke! Davido na correct guy abeg", "like_count": 543},
    {"text": "Na why we love am! Always humble despite the fame", "like_count": 432},
    {"text": "30BG for life! Nobody do am like OBO", "like_count": 321},
    {"text": "This na why Wizkid no fit compete. Real vs Fake!", "like_count": 298},
    {"text": "Chai! This guy too much! Na him be the GOAT 🐐", "like_count": 267},
    {"text": "Forever supporting! OBO way ✨", "like_count": 245},
    {"text": "Baddest! No long talk. Just facts!", "like_count": 234},
    {"text": "My president! Always representing Nigeria well", "like_count": 212},
    {"text": "Baba for the culture forever! 🇳🇬", "like_count": 198},
    {"text": "This is why he's my favorite! So real!", "like_count": 187},
    {"text": "Living legend no cap! OBO for president 😂", "like_count": 176},

    # Negative comments
    {"text": "See as e dey form! Na who e think e be? 😒", "like_count": 156},
    {"text": "Wetin concern us? Abeg shift make person see road", "like_count": 134},
    {"text": "Overrated artist tbh. Wizkid better pass am 100 times", "like_count": 123},
    {"text": "Na money make una dey hype this guy. E no get real talent", "like_count": 112},
    {"text": "Fake humble! All na PR stunts", "like_count": 98},
    {"text": "Burna better pass both of una combined 😤", "like_count": 87},
    {"text": "See showoff! We no care abeg", "like_count": 76},
    {"text": "All this na just vibes. Where the substance dey?", "like_count": 65},

    # Neutral/Mixed comments
    {"text": "Okay o. Next post please", "like_count": 45},
    {"text": "Hmm... interesting. Let me mind my business sha", "like_count": 34},
    {"text": "Na wa o. Social media these days 🤷‍♂️", "like_count": 28},
    {"text": "Alright then. Moving on...", "like_count": 23},
    {"text": "Noted.", "like_count": 18},
    {"text": "K", "like_count": 12},
    {"text": "👀", "like_count": 8},
    {"text": "Nice one", "like_count": 6},

    # More positive to balance
    {"text": "Omo! This guy too much! 001 of Africa! 🌍", "like_count": 445},
    {"text": "We move! OBO gang rise up! 💯", "like_count": 389},
    {"text": "Legendary behavior as usual! No be today!", "like_count": 334},
    {"text": "Naija to the world! Davido represent! 🇳🇬", "like_count": 298},
    {"text": "The people's champion! Always showing love!", "like_count": 276},
    {"text": "E no send anybody! Na why we love am!", "like_count": 254},
    {"text": "Baddest! Simple! No long story!", "like_count": 232},
    {"text": "OBO! OBO!! OBO!!! 🔥🔥🔥", "like_count": 210},
]


def prepare_sample_comments():
    """Prepare sample comments with all required fields."""
    comments = []
    for i, c in enumerate(SAMPLE_COMMENTS):
        username = f"user{i+1:03d}"
        comments.append({
            "comment_id": str(uuid4()),
            "username": username,
            "username_anonymized": f"{username[:3]}***{username[-2:]}",
            "text": c["text"],
            "like_count": c["like_count"],
            "commented_at": datetime.now().isoformat(),
        })
    return comments


async def test_analysis():
    """Test the sentiment analysis with sample data."""
    from app.services.analyzer.cost_effective_analyzer import CostEffectiveAnalyzer

    logger.info("=" * 60)
    logger.info("TESTING SENTIMENT ANALYSIS")
    logger.info("=" * 60)

    comments = prepare_sample_comments()
    analyzer = CostEffectiveAnalyzer()

    result = await analyzer.full_analysis(
        comments=comments,
        celebrity_name="Davido",
        post_context="I be Africa man original I no be gentleman at all o",
    )

    logger.info(f"\n📊 ANALYSIS RESULTS:")
    logger.info(f"Total comments: {result['stats']['total']}")
    logger.info(f"Positive: {result['stats']['positive']} ({result['stats']['positive_pct']:.1f}%)")
    logger.info(f"Negative: {result['stats']['negative']} ({result['stats']['negative_pct']:.1f}%)")
    logger.info(f"Neutral: {result['stats']['neutral']} ({result['stats']['neutral_pct']:.1f}%)")

    logger.info(f"\n📰 AI SUMMARY:")
    summary = result.get('summary', {})
    logger.info(f"Headline: {summary.get('headline', 'N/A')}")
    logger.info(f"Vibe Summary: {summary.get('vibe_summary', 'N/A')}")
    logger.info(f"Controversy Level: {summary.get('controversy_level', 'N/A')}")

    return result


async def test_content_generation(analysis_result):
    """Test content generation (images)."""
    from app.services.generator.image_generator import ImageGenerator
    from app.services.generator.carousel_generator import CarouselGenerator
    from app.services.generator.caption_generator import CaptionGenerator
    from app.services.generator.brand_config import get_brand_config

    logger.info("\n" + "=" * 60)
    logger.info("TESTING CONTENT GENERATION")
    logger.info("=" * 60)

    brand = get_brand_config()
    image_gen = ImageGenerator(brand)
    carousel_gen = CarouselGenerator(brand)
    caption_gen = CaptionGenerator(brand)

    stats = analysis_result['stats']
    summary = analysis_result.get('summary', {})
    top_positive = analysis_result.get('top_positive', [])
    top_negative = analysis_result.get('top_negative', [])
    celebrity_name = "Davido"

    # Format stats for image generator
    image_stats = {
        "positive_pct": stats['positive_pct'],
        "negative_pct": stats['negative_pct'],
        "neutral_pct": stats['neutral_pct'],
        "total": stats['total'],
    }

    # Generate carousel images
    logger.info("Generating carousel images...")

    images = carousel_gen.generate_standard_carousel(
        celebrity_name=celebrity_name,
        stats=image_stats,
        top_positive=top_positive[:3],
        top_negative=top_negative[:3],
        ai_insights=summary,
    )

    # Save images to test output folder
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    image_paths = []
    for i, img_bytes in enumerate(images):
        filepath = output_dir / f"slide_{i+1}.png"
        filepath.write_bytes(img_bytes)
        image_paths.append(str(filepath))
        logger.info(f"  Saved: {filepath}")

    # Generate caption
    logger.info("\nGenerating caption...")
    caption_data = await caption_gen.generate_caption(
        celebrity_name=celebrity_name,
        stats=image_stats,
        ai_insights=summary,
        content_type="carousel",
    )

    full_caption = caption_gen.build_full_caption(
        caption_data["caption"],
        caption_data["call_to_action"],
        caption_data["hashtags"],
    )

    logger.info(f"\n📝 GENERATED CAPTION:\n{full_caption}")

    # Save caption to file
    caption_path = output_dir / "caption.txt"
    caption_path.write_text(full_caption, encoding='utf-8')

    return {
        "image_paths": image_paths,
        "caption": full_caption,
        "stats": image_stats,
    }


async def test_publishing(content_result):
    """Test publishing with mock publisher."""
    from app.services.publisher.instagram_publisher import MockInstagramPublisher

    logger.info("\n" + "=" * 60)
    logger.info("TESTING PUBLISHING (MOCK)")
    logger.info("=" * 60)

    publisher = MockInstagramPublisher()
    await publisher.initialize()

    # Test carousel publish
    logger.info("Publishing carousel (mock)...")
    media_id = await publisher.publish_carousel(
        image_paths=content_result["image_paths"],
        caption=content_result["caption"],
    )

    logger.info(f"✅ Mock publish successful!")
    logger.info(f"   Media ID: {media_id}")

    # Get mock insights
    insights = await publisher.get_media_insights(media_id)
    logger.info(f"   Mock likes: {insights['like_count']}")
    logger.info(f"   Mock comments: {insights['comment_count']}")

    return {
        "media_id": media_id,
        "insights": insights,
    }


async def run_full_test():
    """Run the complete pipeline test."""
    logger.info("\n")
    logger.info("🇳🇬" * 30)
    logger.info("  NAIJA VIBE CHECK - FULL PIPELINE TEST")
    logger.info("🇳🇬" * 30)
    logger.info("\n")

    try:
        # Step 1: Analysis
        analysis_result = await test_analysis()

        # Step 2: Content Generation
        content_result = await test_content_generation(analysis_result)

        # Step 3: Publishing (Mock)
        publish_result = await test_publishing(content_result)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 FULL PIPELINE TEST COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"""
RESULTS SUMMARY:
----------------
📊 Analysis:
   - Comments analyzed: {analysis_result['stats']['total']}
   - Sentiment: {analysis_result['stats']['positive_pct']:.0f}% positive / {analysis_result['stats']['negative_pct']:.0f}% negative
   - Headline: {analysis_result.get('summary', {}).get('headline', 'N/A')}

🖼️ Content Generated:
   - {len(content_result['image_paths'])} carousel slides
   - Images saved to: test_output/

📤 Publishing (Mock):
   - Media ID: {publish_result['media_id']}
   - Status: SUCCESS

✅ All pipeline stages working!

To test with REAL data:
1. Set ANTHROPIC_API_KEY in .env (for AI summaries)
2. Set INSTAGRAM credentials in .env (for real publishing)
3. Run: python -m app.services.vibe_check_pipeline
        """)

        return True

    except Exception as e:
        logger.error(f"\n❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_full_test())
    exit(0 if success else 1)
