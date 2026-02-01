"""
Quality Comparison: Full Claude vs Local Analysis (Standalone)
"""

import json
import re
from pathlib import Path

try:
    from textblob import TextBlob
    HAS_TEXTBLOB = True
except ImportError:
    HAS_TEXTBLOB = False
    print("TextBlob not available, using keyword-only analysis")

# Nigerian pidgin indicators
NAIJA_POSITIVE = [
    'omo', 'correct', 'sha', 'e sweet', 'mad o', 'fire', 'goat', 'legend',
    'king', 'queen', 'boss', 'oga', 'chairman', 'dey reign', 'no cap',
    'sabi', 'better', 'sweet', 'valid', '001', '30bg', 'odogwu', 'baddest',
    'amen', 'congrats', 'proud', 'love', 'best', 'greatest', 'win', 'winner'
]

NAIJA_NEGATIVE = [
    'werey', 'mumu', 'ode', 'olodo', 'yeye', 'craze', 'foolish', 'fake',
    'clout', 'chasing', 'cap', 'lie', 'liar', 'shame', 'fall', 'fail',
    'rubbish', 'nonsense', 'trash', 'hate', 'worst', 'bad', 'terrible'
]


def local_sentiment(text):
    """FREE local sentiment analysis."""
    text_lower = text.lower()

    # Check Nigerian pidgin indicators
    naija_pos = sum(1 for word in NAIJA_POSITIVE if word in text_lower)
    naija_neg = sum(1 for word in NAIJA_NEGATIVE if word in text_lower)

    # Check emojis
    pos_emojis = len(re.findall(r'[🔥💯❤️😍🙌👏✨💪🏆👑🐐💕🎉😊👍]', text))
    neg_emojis = len(re.findall(r'[😡🤮👎💩🖕😤😠🤡💔]', text))

    # TextBlob analysis
    blob_score = 0
    if HAS_TEXTBLOB:
        try:
            blob = TextBlob(text)
            blob_score = blob.sentiment.polarity
        except:
            pass

    # Combine signals
    pos_signals = naija_pos + pos_emojis + (1 if blob_score > 0.2 else 0)
    neg_signals = naija_neg + neg_emojis + (1 if blob_score < -0.2 else 0)

    # Determine sentiment
    if pos_signals > neg_signals + 1:
        return 'positive'
    elif neg_signals > pos_signals + 1:
        return 'negative'
    else:
        return 'neutral'


def compare_quality():
    # Find comments file
    sessions_dir = Path("C:/DEV/naijavibecheck/backend/sessions")

    # Try different paths
    possible_paths = [
        sessions_dir / "analysis_checkpoints" / "analysis_latest.json",
        sessions_dir / "browser_comments.json",
        sessions_dir / "analysis_results.json",
    ]

    comments = None
    for path in possible_paths:
        if path.exists():
            print(f"Loading comments from {path}...")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                comments = data
            elif 'comments' in data:
                comments = data['comments']
            elif 'analyzed_comments' in data:
                comments = data['analyzed_comments']
            elif 'all_comments' in data:
                comments = data['all_comments']

            if comments:
                break

    if not comments:
        print("No comments file found!")
        return

    print(f"Loaded {len(comments):,} comments")

    # Count Claude results
    claude_pos = claude_neg = claude_neu = 0
    for c in comments:
        sent = c.get('sentiment', '').lower()
        if 'positive' in sent:
            claude_pos += 1
        elif 'negative' in sent:
            claude_neg += 1
        else:
            claude_neu += 1

    total = len(comments)

    print(f"\n{'='*60}")
    print("FULL CLAUDE ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Positive: {claude_pos:,} ({claude_pos/total*100:.1f}%)")
    print(f"Negative: {claude_neg:,} ({claude_neg/total*100:.1f}%)")
    print(f"Neutral:  {claude_neu:,} ({claude_neu/total*100:.1f}%)")

    # Run local analysis
    print(f"\n{'='*60}")
    print("RUNNING FREE LOCAL ANALYSIS...")
    print(f"{'='*60}")

    local_pos = local_neg = local_neu = 0
    agreements = 0
    disagreements = []

    for c in comments:
        text = c.get('text', '')
        local_sent = local_sentiment(text)

        if local_sent == 'positive':
            local_pos += 1
        elif local_sent == 'negative':
            local_neg += 1
        else:
            local_neu += 1

        # Compare
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
            if len(disagreements) < 20:
                disagreements.append({
                    'text': text[:80],
                    'claude': claude_sent,
                    'local': local_sent
                })

    print(f"\n{'='*60}")
    print("FREE LOCAL ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Positive: {local_pos:,} ({local_pos/total*100:.1f}%)")
    print(f"Negative: {local_neg:,} ({local_neg/total*100:.1f}%)")
    print(f"Neutral:  {local_neu:,} ({local_neu/total*100:.1f}%)")

    agreement_rate = agreements / total * 100

    print(f"\n{'='*60}")
    print("QUALITY COMPARISON")
    print(f"{'='*60}")
    print(f"\nPer-Comment Agreement: {agreements:,}/{total:,} ({agreement_rate:.1f}%)")

    pos_diff = abs(claude_pos - local_pos) / total * 100
    neg_diff = abs(claude_neg - local_neg) / total * 100

    print(f"\nAggregate Percentage Differences:")
    print(f"  Positive: {abs(claude_pos/total*100 - local_pos/total*100):.1f}%")
    print(f"  Negative: {abs(claude_neg/total*100 - local_neg/total*100):.1f}%")

    print(f"\n{'='*60}")
    print("SAMPLE DISAGREEMENTS")
    print(f"{'='*60}")

    for i, d in enumerate(disagreements[:8]):
        safe_text = d['text'].encode('ascii', 'ignore').decode()
        print(f"\n{i+1}. \"{safe_text}...\"")
        print(f"   Claude: {d['claude']} | Local: {d['local']}")

    print(f"\n{'='*60}")
    print("VERDICT")
    print(f"{'='*60}")

    if agreement_rate >= 80:
        verdict = "EXCELLENT"
        msg = "Local analysis closely matches Claude! Hybrid approach recommended."
    elif agreement_rate >= 70:
        verdict = "GOOD"
        msg = "Aggregate stats accurate, some individual differences."
    elif agreement_rate >= 60:
        verdict = "MODERATE"
        msg = "Noticeable differences. Consider Claude for Nigerian pidgin posts."
    else:
        verdict = "LIMITED"
        msg = "Significant differences. Full Claude analysis recommended for accuracy."

    print(f"\n{verdict}: {msg}")

    # Final comparison
    print(f"\n{'='*60}")
    print("COST-BENEFIT ANALYSIS")
    print(f"{'='*60}")
    print(f"\n                   | Full Claude | Hybrid Approach")
    print(f"                   |-------------|----------------")
    print(f" Cost ({total:,} comments) | ~$3-5       | ~$0.05")
    print(f" Cost (1M comments) | ~$900       | ~$0.10")
    print(f" Aggregate accuracy | 100%        | ~{100-pos_diff:.0f}%")
    print(f" Per-comment match  | 100%        | {agreement_rate:.0f}%")
    print(f" Summary quality    | Claude      | Claude (same)")

    print(f"\n{'='*60}")
    print("RECOMMENDATION")
    print(f"{'='*60}")

    if agreement_rate >= 70:
        print("\nUse HYBRID approach for production:")
        print("  - Local analysis for bulk sentiment (FREE)")
        print("  - Claude only for summary/headline (~$0.05)")
        print("  - Top comments verified by Claude from sample")
        print(f"\n  Savings: ~99% cost reduction with {agreement_rate:.0f}% agreement")
    else:
        print("\nConsider using more Claude analysis for this dataset.")
        print("Nigerian pidgin/slang may need Claude's understanding.")


if __name__ == "__main__":
    compare_quality()
