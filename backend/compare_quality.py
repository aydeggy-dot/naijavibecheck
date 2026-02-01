"""
Quality Comparison: Full Claude vs Hybrid (Local + Claude Summary)

This script compares the sentiment analysis quality between:
1. Full Claude analysis (what we already ran)
2. Local TextBlob + Nigerian pidgin analysis (cost-effective)
"""

import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.analyzer.cost_effective_analyzer import CostEffectiveAnalyzer

def compare_quality():
    # Load Claude-analyzed comments
    claude_results_path = Path("sessions/analysis_checkpoints/analysis_latest.json")

    if not claude_results_path.exists():
        # Try browser comments
        claude_results_path = Path("sessions/browser_comments.json")

    print(f"Loading comments from {claude_results_path}...")

    with open(claude_results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different formats
    if isinstance(data, list):
        comments = data
    elif 'comments' in data:
        comments = data['comments']
    else:
        comments = data.get('analyzed_comments', data.get('all_comments', []))

    print(f"Loaded {len(comments):,} comments")

    # Get Claude sentiment results
    claude_positive = 0
    claude_negative = 0
    claude_neutral = 0

    for c in comments:
        sentiment = c.get('sentiment', '').lower()
        if 'positive' in sentiment:
            claude_positive += 1
        elif 'negative' in sentiment:
            claude_negative += 1
        else:
            claude_neutral += 1

    print(f"\n{'='*60}")
    print("FULL CLAUDE ANALYSIS RESULTS (already computed)")
    print(f"{'='*60}")
    print(f"Positive: {claude_positive:,} ({claude_positive/len(comments)*100:.1f}%)")
    print(f"Negative: {claude_negative:,} ({claude_negative/len(comments)*100:.1f}%)")
    print(f"Neutral:  {claude_neutral:,} ({claude_neutral/len(comments)*100:.1f}%)")

    # Run local analysis
    print(f"\n{'='*60}")
    print("RUNNING FREE LOCAL ANALYSIS...")
    print(f"{'='*60}")

    analyzer = CostEffectiveAnalyzer()

    local_positive = 0
    local_negative = 0
    local_neutral = 0

    # Track agreement
    agreements = 0
    disagreements = []

    for c in comments:
        text = c.get('text', '')
        local_result = analyzer._local_sentiment(text)

        local_sent = local_result['sentiment']
        if local_sent == 'positive':
            local_positive += 1
        elif local_sent == 'negative':
            local_negative += 1
        else:
            local_neutral += 1

        # Compare with Claude
        claude_sent = c.get('sentiment', '').lower()
        if 'positive' in claude_sent:
            claude_sent = 'positive'
        elif 'negative' in claude_sent:
            claude_sent = 'negative'
        else:
            claude_sent = 'neutral'

        if local_sent == claude_sent:
            agreements += 1
        else:
            disagreements.append({
                'text': text[:100],
                'claude': claude_sent,
                'local': local_sent
            })

    print(f"\n{'='*60}")
    print("FREE LOCAL ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Positive: {local_positive:,} ({local_positive/len(comments)*100:.1f}%)")
    print(f"Negative: {local_negative:,} ({local_negative/len(comments)*100:.1f}%)")
    print(f"Neutral:  {local_neutral:,} ({local_neutral/len(comments)*100:.1f}%)")

    print(f"\n{'='*60}")
    print("QUALITY COMPARISON")
    print(f"{'='*60}")

    agreement_rate = agreements / len(comments) * 100
    print(f"\nAgreement with Claude: {agreements:,}/{len(comments):,} ({agreement_rate:.1f}%)")

    # Calculate aggregate difference
    pos_diff = abs(claude_positive - local_positive)
    neg_diff = abs(claude_negative - local_negative)

    print(f"\nAggregate Differences:")
    print(f"  Positive: {pos_diff:,} comments ({pos_diff/len(comments)*100:.1f}%)")
    print(f"  Negative: {neg_diff:,} comments ({neg_diff/len(comments)*100:.1f}%)")

    print(f"\n{'='*60}")
    print("SAMPLE DISAGREEMENTS (Claude vs Local)")
    print(f"{'='*60}")

    for d in disagreements[:10]:
        text_preview = d['text'].encode('ascii', 'ignore').decode()
        print(f"\nText: {text_preview}...")
        print(f"  Claude: {d['claude']}, Local: {d['local']}")

    print(f"\n{'='*60}")
    print("VERDICT")
    print(f"{'='*60}")

    if agreement_rate >= 80:
        print("\n EXCELLENT: Local analysis closely matches Claude!")
        print("  The hybrid approach will work great for this dataset.")
    elif agreement_rate >= 70:
        print("\n GOOD: Local analysis reasonably matches Claude.")
        print("  Aggregate stats will be accurate, some individual differences.")
    else:
        print("\n MODERATE: Significant differences between methods.")
        print("  Consider using Claude for more complex pidgin analysis.")

    print(f"\nCOST COMPARISON:")
    print(f"  Full Claude for {len(comments):,} comments: ~$3-5")
    print(f"  Hybrid approach: ~$0.05 (summary only)")
    print(f"  Savings: ~99%")

    return {
        'claude': {'positive': claude_positive, 'negative': claude_negative, 'neutral': claude_neutral},
        'local': {'positive': local_positive, 'negative': local_negative, 'neutral': local_neutral},
        'agreement_rate': agreement_rate
    }


if __name__ == "__main__":
    compare_quality()
