"""Run full sentiment analysis on all scraped comments."""
import asyncio
import json
import time
from pathlib import Path

from app.services.analyzer.sentiment_analyzer import SentimentAnalyzer


async def run_full_analysis():
    """Analyze all comments in batches."""

    # Load comments
    with open('sessions/browser_comments.json', 'r', encoding='utf-8') as f:
        all_comments = json.load(f)

    # Filter valid comments
    valid_comments = [c for c in all_comments if c.get('text', '').strip()]
    total = len(valid_comments)

    print(f"=" * 60)
    print(f"NAIJA VIBE CHECK - Full Analysis")
    print(f"=" * 60)
    print(f"Total comments to analyze: {total}")
    print(f"Batches needed: {(total + 49) // 50}")
    print(f"=" * 60)

    analyzer = SentimentAnalyzer()

    all_analyzed = []
    batch_size = 50
    batch_num = 0
    start_time = time.time()

    for i in range(0, total, batch_size):
        batch_num += 1
        batch = valid_comments[i:i + batch_size]

        print(f"\rAnalyzing batch {batch_num}/{(total + 49) // 50} ({i + len(batch)}/{total} comments)...", end="", flush=True)

        try:
            analyzed_batch = await analyzer.analyze_comments_batch(
                comments=batch,
                celebrity_name='Davido',
                post_context='I be Africa man original I no be gentleman at all o'
            )
            all_analyzed.extend(analyzed_batch)

            # Small delay between batches to avoid rate limits
            await asyncio.sleep(0.5)

        except Exception as e:
            print(f"\nError in batch {batch_num}: {e}")
            # Add unanalyzed comments with default values
            for c in batch:
                c['sentiment'] = 'unknown'
                c['sentiment_score'] = 0.0
                all_analyzed.append(c)

    elapsed = time.time() - start_time
    print(f"\n\nAnalysis complete in {elapsed:.1f} seconds")

    # Calculate statistics
    positive = [c for c in all_analyzed if c.get('sentiment') == 'positive']
    negative = [c for c in all_analyzed if c.get('sentiment') == 'negative']
    neutral = [c for c in all_analyzed if c.get('sentiment') == 'neutral']
    unknown = [c for c in all_analyzed if c.get('sentiment') not in ['positive', 'negative', 'neutral']]

    stats = {
        'total': len(all_analyzed),
        'positive': len(positive),
        'negative': len(negative),
        'neutral': len(neutral),
        'unknown': len(unknown),
        'positive_pct': (len(positive) / len(all_analyzed)) * 100 if all_analyzed else 0,
        'negative_pct': (len(negative) / len(all_analyzed)) * 100 if all_analyzed else 0,
        'neutral_pct': (len(neutral) / len(all_analyzed)) * 100 if all_analyzed else 0,
    }

    print(f"\n" + "=" * 60)
    print(f"SENTIMENT BREAKDOWN")
    print(f"=" * 60)
    print(f"Positive: {stats['positive']:,} ({stats['positive_pct']:.1f}%)")
    print(f"Negative: {stats['negative']:,} ({stats['negative_pct']:.1f}%)")
    print(f"Neutral:  {stats['neutral']:,} ({stats['neutral_pct']:.1f}%)")
    if stats['unknown'] > 0:
        print(f"Unknown:  {stats['unknown']:,}")

    # Get top comments
    top_positive, top_negative = await analyzer.get_top_comments(all_analyzed, top_n=5)

    print(f"\n" + "=" * 60)
    print(f"TOP POSITIVE COMMENTS")
    print(f"=" * 60)
    for i, c in enumerate(top_positive[:5], 1):
        text = c['text'][:80].encode('ascii', 'ignore').decode()
        score = c.get('sentiment_score', 0)
        print(f"{i}. [{score:.2f}] @{c['username']}: {text}")

    print(f"\n" + "=" * 60)
    print(f"TOP NEGATIVE/TOXIC COMMENTS")
    print(f"=" * 60)
    if top_negative:
        for i, c in enumerate(top_negative[:5], 1):
            text = c['text'][:80].encode('ascii', 'ignore').decode()
            toxicity = c.get('toxicity_score', 0)
            print(f"{i}. [toxicity: {toxicity:.2f}] @{c['username']}: {text}")
    else:
        print("No significantly negative comments found!")

    # Generate overall summary
    print(f"\n" + "=" * 60)
    print(f"GENERATING AI SUMMARY...")
    print(f"=" * 60)

    summary = await analyzer.generate_post_summary(
        celebrity_name='Davido',
        post_caption='I be Africa man original I no be gentleman at all o',
        stats=stats,
        top_positive=top_positive,
        top_negative=top_negative
    )

    headline = summary.get('headline', 'N/A')
    vibe = summary.get('vibe_summary', 'N/A')
    spicy = summary.get('spicy_take', 'N/A')
    controversy = summary.get('controversy_level', 'N/A')
    hashtags = summary.get('recommended_hashtags', [])

    print(f"\n{'=' * 60}")
    print(f"NAIJA VIBE CHECK RESULTS")
    print(f"{'=' * 60}")
    print(f"\nHEADLINE: {headline}")
    print(f"\nVIBE SUMMARY:\n{vibe}")
    print(f"\nSPICY TAKE:\n{spicy}")
    print(f"\nCONTROVERSY LEVEL: {controversy}")
    print(f"\nRECOMMENDED HASHTAGS: #{' #'.join(hashtags)}")
    print(f"{'=' * 60}")

    # Save full results
    results = {
        'post': {
            'shortcode': 'DULsWrPjwef',
            'celebrity': 'Davido',
            'caption': 'I be Africa man original I no be gentleman at all o'
        },
        'stats': stats,
        'summary': summary,
        'top_positive': [{
            'username': c['username'],
            'text': c['text'],
            'sentiment_score': c.get('sentiment_score', 0),
            'ai_summary': c.get('ai_summary', '')
        } for c in top_positive],
        'top_negative': [{
            'username': c['username'],
            'text': c['text'],
            'toxicity_score': c.get('toxicity_score', 0),
            'ai_summary': c.get('ai_summary', '')
        } for c in top_negative],
        'analyzed_comments': all_analyzed
    }

    with open('sessions/full_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nFull results saved to sessions/full_analysis_results.json")

    return results


if __name__ == "__main__":
    asyncio.run(run_full_analysis())
