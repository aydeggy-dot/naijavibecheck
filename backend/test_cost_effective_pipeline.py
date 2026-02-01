"""
Test the cost-effective analysis pipeline.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Mock the settings to avoid pydantic validation
import os
os.environ['ANTHROPIC_API_KEY'] = os.environ.get('ANTHROPIC_API_KEY', '')
os.environ['DATABASE_URL'] = 'postgresql://test:test@localhost/test'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'


async def test_pipeline():
    from app.services.analyzer.cost_effective_analyzer import CostEffectiveAnalyzer

    # Load comments
    comments_path = Path(__file__).parent / "sessions/browser_comments.json"
    with open(comments_path, 'r', encoding='utf-8') as f:
        comments = json.load(f)

    print(f"\n{'='*60}")
    print("TESTING COST-EFFECTIVE ANALYSIS PIPELINE")
    print(f"{'='*60}")
    print(f"\nComments to analyze: {len(comments):,}")

    analyzer = CostEffectiveAnalyzer()

    def progress(current, total):
        if current % 1000 == 0:
            print(f"Progress: {current:,}/{total:,}")

    result = await analyzer.full_analysis(
        comments=comments,
        celebrity_name="Davido",
        post_context="I be Africa man original I no be gentleman at all o",
        progress_callback=progress
    )

    stats = result['stats']
    summary = result['summary']

    print(f"\n{'='*60}")
    print("ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"\nTotal: {stats['total']:,}")
    print(f"Positive: {stats['positive']:,} ({stats['positive_pct']:.1f}%)")
    print(f"Negative: {stats['negative']:,} ({stats['negative_pct']:.1f}%)")
    print(f"Neutral: {stats['neutral']:,} ({stats['neutral_pct']:.1f}%)")

    print(f"\n{'='*60}")
    print("AI-GENERATED SUMMARY (Claude)")
    print(f"{'='*60}")
    print(f"\nHeadline: {summary.get('headline', 'N/A')}")
    print(f"Vibe: {summary.get('vibe_summary', 'N/A')}")
    print(f"Spicy Take: {summary.get('spicy_take', 'N/A')}")
    print(f"Controversy: {summary.get('controversy_level', 'N/A')}")
    print(f"Themes: {summary.get('themes', [])}")
    print(f"Hashtags: #{' #'.join(summary.get('recommended_hashtags', []))}")

    print(f"\n{'='*60}")
    print(f"Cost estimate: {result.get('cost_estimate', '$0.05-0.10')}")
    print(f"{'='*60}")

    # Save result
    output_path = Path(__file__).parent / "sessions/cost_effective_test_result.json"
    save_result = {k: v for k, v in result.items() if k != 'comments'}
    save_result['sample_comments'] = result['comments'][:50]
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(save_result, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nResults saved to: {output_path}")

    return result


if __name__ == "__main__":
    asyncio.run(test_pipeline())
