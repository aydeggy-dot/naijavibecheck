"""Initial database schema.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Proxies table
    op.create_table(
        'proxies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('host', sa.String(255), nullable=False),
        sa.Column('port', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('password_encrypted', sa.Text(), nullable=True),
        sa.Column('protocol', sa.String(20), nullable=False, server_default='http'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('country_code', sa.String(5), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Celebrities table
    op.create_table(
        'celebrities',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instagram_username', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('follower_count', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('discovered_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
        sa.Column('scrape_priority', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instagram_username')
    )
    op.create_index('ix_celebrities_instagram_username', 'celebrities', ['instagram_username'])

    # Posts table
    op.create_table(
        'posts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('celebrity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instagram_post_id', sa.String(255), nullable=False),
        sa.Column('shortcode', sa.String(50), nullable=False),
        sa.Column('post_url', sa.String(500), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('comment_count', sa.Integer(), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_viral', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('viral_score', sa.Float(), nullable=True),
        sa.Column('is_analyzed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['celebrity_id'], ['celebrities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instagram_post_id')
    )
    op.create_index('ix_posts_celebrity_id', 'posts', ['celebrity_id'])
    op.create_index('ix_posts_shortcode', 'posts', ['shortcode'])

    # Comments table
    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instagram_comment_id', sa.String(255), nullable=True),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('username_anonymized', sa.String(255), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('commented_at', sa.DateTime(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_reply', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['comments.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'instagram_comment_id', name='uq_post_comment')
    )
    op.create_index('ix_comments_post_id', 'comments', ['post_id'])

    # Comment analysis table
    op.create_table(
        'comment_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('comment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sentiment', sa.String(20), nullable=True),
        sa.Column('sentiment_score', sa.Float(), nullable=True),
        sa.Column('toxicity_score', sa.Float(), nullable=True),
        sa.Column('emotion_tags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('is_top_positive', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_top_negative', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('analysis_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['comment_id'], ['comments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('comment_id')
    )

    # Post analysis table
    op.create_table(
        'post_analysis',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_comments_analyzed', sa.Integer(), nullable=True),
        sa.Column('positive_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('negative_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('neutral_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('positive_percentage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('negative_percentage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('neutral_percentage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('average_sentiment_score', sa.Float(), nullable=False, server_default='0'),
        sa.Column('top_positive_comment_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('top_negative_comment_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column('controversy_score', sa.Float(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_insights', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id')
    )

    # Generated content table
    op.create_table(
        'generated_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('post_analysis_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('hashtags', postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column('media_urls', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('thumbnail_url', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('scheduled_for', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('instagram_post_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_metadata', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.ForeignKeyConstraint(['post_analysis_id'], ['post_analysis.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Our engagement table
    op.create_table(
        'our_engagement',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('checked_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('comment_count', sa.Integer(), nullable=True),
        sa.Column('share_count', sa.Integer(), nullable=True),
        sa.Column('save_count', sa.Integer(), nullable=True),
        sa.Column('reach', sa.Integer(), nullable=True),
        sa.Column('impressions', sa.Integer(), nullable=True),
        sa.Column('engagement_rate', sa.Float(), nullable=True),
        sa.Column('follower_change', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['generated_content_id'], ['generated_content.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Content performance table
    op.create_table(
        'content_performance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('celebrity_category', sa.String(50), nullable=True),
        sa.Column('content_type', sa.String(50), nullable=True),
        sa.Column('post_hour', sa.Integer(), nullable=True),
        sa.Column('post_day_of_week', sa.Integer(), nullable=True),
        sa.Column('controversy_level', sa.String(20), nullable=True),
        sa.Column('engagement_score', sa.Float(), nullable=True),
        sa.Column('virality_score', sa.Float(), nullable=True),
        sa.Column('features', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['generated_content_id'], ['generated_content.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('generated_content_id')
    )

    # Settings table
    op.create_table(
        'settings',
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', postgresql.JSONB(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('key')
    )

    # Scraper accounts table
    op.create_table(
        'scraper_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('password_encrypted', sa.Text(), nullable=False),
        sa.Column('session_data', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('requests_today', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_banned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('banned_at', sa.DateTime(), nullable=True),
        sa.Column('proxy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['proxy_id'], ['proxies.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('scraper_accounts')
    op.drop_table('settings')
    op.drop_table('content_performance')
    op.drop_table('our_engagement')
    op.drop_table('generated_content')
    op.drop_table('post_analysis')
    op.drop_table('comment_analysis')
    op.drop_table('comments')
    op.drop_table('posts')
    op.drop_table('celebrities')
    op.drop_table('proxies')
