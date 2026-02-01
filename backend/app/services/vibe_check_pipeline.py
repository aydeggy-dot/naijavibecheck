"""
NaijaVibeCheck - Complete Production Pipeline

This is the main orchestrator that:
- Scrapes ALL comments (millions if needed)
- Analyzes sentiment with patience
- Generates publishable insights
- Works overnight if needed
- Resumes from interruptions
- Protects accounts from bans
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Callable

from app.services.scraper.robust_scraper import RobustInstagramScraper
from app.services.analyzer.robust_analyzer import RobustSentimentAnalyzer
from app.services.analyzer.cost_effective_analyzer import CostEffectiveAnalyzer
from app.services.database_storage import DatabaseStorage, save_vibe_check_result
from app.config import settings

logger = logging.getLogger(__name__)


class VibeCheckPipeline:
    """
    Complete end-to-end pipeline for NaijaVibeCheck.

    Usage:
        pipeline = VibeCheckPipeline()
        result = await pipeline.run_full_analysis(
            shortcode="DULsWrPjwef",
            celebrity_name="Davido"
        )
    """

    def __init__(
        self,
        results_dir: Optional[Path] = None,
        scraper_config: Optional[Dict] = None,
        analyzer_config: Optional[Dict] = None,
    ):
        self.results_dir = results_dir or Path(settings.sessions_dir) / "vibe_check_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.scraper_config = scraper_config
        self.analyzer_config = analyzer_config

    async def run_full_analysis(
        self,
        shortcode: str,
        celebrity_name: str,
        post_context: str = "",
        max_comments: int = 0,  # 0 = unlimited
        resume: bool = True,
        cost_effective: bool = True,  # Use hybrid approach (99% cheaper)
        save_to_database: bool = True,  # Save to PostgreSQL (production)
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run complete vibe check analysis on a post.

        Args:
            shortcode: Instagram post shortcode
            celebrity_name: Celebrity name for context
            post_context: Post caption (optional)
            max_comments: Maximum comments to scrape (0 = all)
            resume: Resume from previous progress
            progress_callback: Callback(stage, current, total)

        Returns:
            Complete analysis results ready for publishing
        """
        analysis_id = f"{shortcode}_{datetime.now().strftime('%Y%m%d')}"
        result_path = self.results_dir / f"{analysis_id}.json"

        logger.info(f"=" * 60)
        logger.info(f"NAIJA VIBE CHECK PIPELINE")
        logger.info(f"Post: {shortcode}")
        logger.info(f"Celebrity: {celebrity_name}")
        logger.info(f"=" * 60)

        # Check for existing complete result
        if resume and result_path.exists():
            try:
                with open(result_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                if existing.get('status') == 'complete':
                    logger.info("Found complete previous analysis, returning cached result")
                    return existing
            except:
                pass

        # ============================================
        # STAGE 1: SCRAPE COMMENTS
        # ============================================
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 1: SCRAPING COMMENTS")
        logger.info("=" * 60)

        scraper = RobustInstagramScraper(config=self.scraper_config)

        def scrape_progress(current, total):
            if progress_callback:
                progress_callback("scraping", current, total)
            if current % 500 == 0:
                logger.info(f"Scrape progress: {current:,}/{total:,}")

        try:
            scrape_result = await scraper.scrape_all_comments(
                shortcode=shortcode,
                max_comments=max_comments,
                resume=resume,
                progress_callback=scrape_progress
            )
        finally:
            await scraper.close()

        if 'error' in scrape_result and not scrape_result.get('comments'):
            logger.error(f"Scraping failed: {scrape_result['error']}")
            return {
                'status': 'failed',
                'stage': 'scraping',
                'error': scrape_result['error']
            }

        comments = scrape_result.get('comments', [])
        total_expected = scrape_result.get('total_expected', len(comments))

        logger.info(f"Scraped {len(comments):,} comments (expected: {total_expected:,})")
        logger.info(f"Coverage: {scrape_result.get('coverage_pct', 0):.1f}%")

        # Save intermediate result
        intermediate = {
            'status': 'scraping_complete',
            'shortcode': shortcode,
            'celebrity': celebrity_name,
            'scrape_stats': {
                'total_scraped': len(comments),
                'total_expected': total_expected,
                'coverage_pct': scrape_result.get('coverage_pct', 0),
                'scrape_time_minutes': scrape_result.get('scrape_time_minutes', 0)
            },
            'comments': comments
        }
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(intermediate, f, ensure_ascii=False, default=str)

        # ============================================
        # STAGE 2: SENTIMENT ANALYSIS
        # ============================================
        logger.info("\n" + "=" * 60)
        logger.info("STAGE 2: SENTIMENT ANALYSIS")
        if cost_effective:
            logger.info("Mode: COST-EFFECTIVE (local + Claude summary)")
        else:
            logger.info("Mode: FULL CLAUDE (higher accuracy, higher cost)")
        logger.info("=" * 60)

        def analysis_progress(current, total):
            if progress_callback:
                progress_callback("analyzing", current, total)
            if current % 200 == 0:
                logger.info(f"Analysis progress: {current:,}/{total:,}")

        if cost_effective:
            # Use cost-effective hybrid approach
            analyzer = CostEffectiveAnalyzer()
            analysis_result = await analyzer.full_analysis(
                comments=comments,
                celebrity_name=celebrity_name,
                post_context=post_context,
                progress_callback=analysis_progress
            )
            stats = analysis_result.get('stats', {})
            analyzed_comments = analysis_result.get('comments', [])
            # Get summary directly from cost-effective result
            summary = analysis_result.get('summary', {})
            top_comments = {
                'top_positive': analysis_result.get('top_positive', []),
                'top_negative': analysis_result.get('top_negative', []),
                'notable': analysis_result.get('notable', [])
            }
        else:
            # Use full Claude analysis (more expensive)
            analyzer = RobustSentimentAnalyzer(config=self.analyzer_config)
            analysis_result = await analyzer.analyze_all_comments(
                comments=comments,
                celebrity_name=celebrity_name,
                post_context=post_context,
                analysis_id=analysis_id,
                resume=resume,
                progress_callback=analysis_progress
            )
            stats = analysis_result.get('stats', {})
            analyzed_comments = analysis_result.get('comments', [])
            summary = None  # Will be generated in stage 4
            top_comments = None  # Will be extracted in stage 3

        logger.info(f"Analyzed {stats.get('successfully_analyzed', 0):,} comments")
        logger.info(f"Positive: {stats.get('positive_pct', 0):.1f}%")
        logger.info(f"Negative: {stats.get('negative_pct', 0):.1f}%")

        # ============================================
        # STAGE 3: GET TOP COMMENTS
        # ============================================
        if top_comments is None:
            # Only needed for full Claude mode
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 3: EXTRACTING INSIGHTS")
            logger.info("=" * 60)

            top_comments = await analyzer.get_top_comments(analyzed_comments, top_n=10)

            logger.info(f"Found {len(top_comments.get('top_positive', []))} top positive")
            logger.info(f"Found {len(top_comments.get('top_negative', []))} top negative")
            logger.info(f"Found {len(top_comments.get('notable', []))} notable comments")
        else:
            logger.info("\n[STAGE 3: SKIPPED - Using cost-effective results]")

        # ============================================
        # STAGE 4: GENERATE SUMMARY
        # ============================================
        if summary is None:
            # Only needed for full Claude mode
            logger.info("\n" + "=" * 60)
            logger.info("STAGE 4: GENERATING AI SUMMARY")
            logger.info("=" * 60)

            summary = await analyzer.generate_summary(
                celebrity_name=celebrity_name,
                post_caption=post_context,
                stats=stats,
                top_comments=top_comments
            )

            logger.info(f"Headline: {summary.get('headline', 'N/A')}")
            logger.info(f"Controversy level: {summary.get('controversy_level', 'N/A')}")
        else:
            logger.info("\n[STAGE 4: SKIPPED - Using cost-effective summary]")
            logger.info(f"Headline: {summary.get('headline', 'N/A')}")
            logger.info(f"Controversy level: {summary.get('controversy_level', 'N/A')}")

        # ============================================
        # FINAL RESULT
        # ============================================
        final_result = {
            'status': 'complete',
            'analysis_id': analysis_id,
            'timestamp': datetime.now().isoformat(),
            'post': {
                'shortcode': shortcode,
                'url': f'https://www.instagram.com/p/{shortcode}/',
                'celebrity': celebrity_name,
                'caption': post_context[:500] if post_context else None,
            },
            'scrape_stats': {
                'total_scraped': len(comments),
                'total_expected': total_expected,
                'coverage_pct': scrape_result.get('coverage_pct', 0),
                'scrape_time_minutes': scrape_result.get('scrape_time_minutes', 0)
            },
            'analysis_stats': stats,
            'analysis_mode': 'cost_effective' if cost_effective else 'full_claude',
            'cost_estimate': '$0.05-0.10' if cost_effective else f'~${len(comments) * 0.001:.2f}',
            'summary': summary,
            'top_comments': {
                'positive': [
                    {
                        'username': c.get('username_anonymized', c.get('username', '')),
                        'text': c.get('text', '')[:200],
                        'sentiment_score': c.get('sentiment_score', 0),
                        'ai_summary': c.get('ai_summary', '')
                    }
                    for c in top_comments.get('top_positive', [])[:5]
                ],
                'negative': [
                    {
                        'username': c.get('username_anonymized', c.get('username', '')),
                        'text': c.get('text', '')[:200],
                        'toxicity_score': c.get('toxicity_score', 0),
                        'ai_summary': c.get('ai_summary', '')
                    }
                    for c in top_comments.get('top_negative', [])[:5]
                ],
                'notable': [
                    {
                        'username': c.get('username_anonymized', c.get('username', '')),
                        'text': c.get('text', '')[:200],
                        'ai_summary': c.get('ai_summary', '')
                    }
                    for c in top_comments.get('notable', [])[:5]
                ]
            },
            # Full data for reference (can be large)
            'all_comments': analyzed_comments
        }

        # Save final result to JSON file (backup)
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2, default=str)

        # Save to PostgreSQL database (production)
        if save_to_database:
            try:
                logger.info("\n" + "=" * 60)
                logger.info("STAGE 5: SAVING TO DATABASE")
                logger.info("=" * 60)

                db_result = await save_vibe_check_result(
                    shortcode=shortcode,
                    celebrity_name=celebrity_name,
                    comments=comments,
                    stats=stats,
                    summary=summary,
                    top_comments=final_result['top_comments']
                )
                final_result['database'] = {
                    'saved': True,
                    'post_id': db_result['post_id'],
                    'analysis_id': db_result['analysis_id']
                }
                logger.info(f"Saved to database: post_id={db_result['post_id']}")
            except Exception as e:
                logger.error(f"Database save failed: {e}")
                final_result['database'] = {'saved': False, 'error': str(e)}

        logger.info(f"\n" + "=" * 60)
        logger.info(f"VIBE CHECK COMPLETE!")
        logger.info(f"Results saved to: {result_path}")
        if save_to_database and final_result.get('database', {}).get('saved'):
            logger.info(f"Results saved to: PostgreSQL database")
        logger.info(f"=" * 60)

        return final_result

    def get_publishable_report(self, result: Dict) -> str:
        """Generate a publishable report from analysis results."""
        if result.get('status') != 'complete':
            return f"Analysis incomplete: {result.get('status')}"

        summary = result.get('summary', {})
        stats = result.get('analysis_stats', {})
        scrape_stats = result.get('scrape_stats', {})

        report = f"""
{'='*60}
NAIJA VIBE CHECK REPORT
{'='*60}

📊 POST: {result['post']['celebrity']}
🔗 {result['post']['url']}

{'='*60}
📈 ANALYSIS STATS
{'='*60}
Comments Analyzed: {stats.get('successfully_analyzed', 0):,} / {scrape_stats.get('total_expected', 0):,}
Coverage: {scrape_stats.get('coverage_pct', 0):.1f}%

SENTIMENT BREAKDOWN:
✅ Positive: {stats.get('positive', 0):,} ({stats.get('positive_pct', 0):.1f}%)
❌ Negative: {stats.get('negative', 0):,} ({stats.get('negative_pct', 0):.1f}%)
➖ Neutral: {stats.get('neutral', 0):,} ({stats.get('neutral_pct', 0):.1f}%)

{'='*60}
📰 AI-GENERATED SUMMARY
{'='*60}

HEADLINE: {summary.get('headline', 'N/A')}

VIBE SUMMARY:
{summary.get('vibe_summary', 'N/A')}

SPICY TAKE:
{summary.get('spicy_take', 'N/A')}

CONTROVERSY LEVEL: {summary.get('controversy_level', 'N/A').upper()}

KEY INSIGHTS:
"""
        for insight in summary.get('key_insights', []):
            report += f"• {insight}\n"

        report += f"""
RECOMMENDED HASHTAGS:
#{' #'.join(summary.get('recommended_hashtags', ['NaijaVibeCheck']))}

{'='*60}
Generated by NaijaVibeCheck
Analysis Time: {stats.get('analysis_time_minutes', 0):.1f} minutes
{'='*60}
"""
        return report


async def run_overnight_analysis(
    shortcode: str,
    celebrity_name: str,
    post_context: str = "",
    cost_effective: bool = True  # Default to cost-effective mode
):
    """
    Run a full overnight analysis job.

    This function is designed to be called as a background task
    that can run for hours if needed.

    Args:
        shortcode: Instagram post shortcode
        celebrity_name: Celebrity name
        post_context: Post caption
        cost_effective: Use hybrid approach (99% cheaper, recommended)
    """
    pipeline = VibeCheckPipeline()

    def progress(stage, current, total):
        pct = (current / total * 100) if total > 0 else 0
        print(f"[{stage.upper()}] {current:,}/{total:,} ({pct:.1f}%)")

    result = await pipeline.run_full_analysis(
        shortcode=shortcode,
        celebrity_name=celebrity_name,
        post_context=post_context,
        max_comments=0,  # Get ALL comments
        resume=True,
        cost_effective=cost_effective,
        progress_callback=progress
    )

    # Print report
    report = pipeline.get_publishable_report(result)
    print(report)

    return result


if __name__ == "__main__":
    # Example usage
    asyncio.run(run_overnight_analysis(
        shortcode="DULsWrPjwef",
        celebrity_name="Davido",
        post_context="I be Africa man original I no be gentleman at all o"
    ))
