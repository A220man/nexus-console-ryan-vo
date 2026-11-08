"""Add enrichment jobs table

Revision ID: 20261108_add_enrichment
Revises: 
Create Date: 2026-11-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20261108_add_enrichment'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    enrichment_status = sa.Enum('pending', 'running', 'completed', 'failed', name='enrichmentstatus')
    enrichment_target_type = sa.Enum('contact', 'company', name='enrichmenttargettype')
    enrichment_provider = sa.Enum('offline', 'openai_compatible', 'anthropic', 'gemini', name='enrichmentprovider')
    
    enrichment_status.create(op.get_bind(), checkfirst=True)
    enrichment_target_type.create(op.get_bind(), checkfirst=True)
    enrichment_provider.create(op.get_bind(), checkfirst=True)
    
    op.create_table(
        'enrichment_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('target_type', enrichment_target_type, nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('provider', enrichment_provider, nullable=False, server_default='offline'),
        sa.Column('status', enrichment_status, nullable=False, server_default='pending'),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('result_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('config_snapshot', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_enrichment_jobs_target', 'enrichment_jobs', ['target_type', 'target_id'], unique=False)
    op.create_index('ix_enrichment_jobs_status_created', 'enrichment_jobs', ['status', 'created_at'], unique=False)
    op.create_index(op.f('ix_enrichment_jobs_target_type'), 'enrichment_jobs', ['target_type'], unique=False)
    op.create_index(op.f('ix_enrichment_jobs_target_id'), 'enrichment_jobs', ['target_id'], unique=False)
    op.create_index(op.f('ix_enrichment_jobs_status'), 'enrichment_jobs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_enrichment_jobs_status'), table_name='enrichment_jobs')
    op.drop_index(op.f('ix_enrichment_jobs_target_id'), table_name='enrichment_jobs')
    op.drop_index(op.f('ix_enrichment_jobs_target_type'), table_name='enrichment_jobs')
    op.drop_index('ix_enrichment_jobs_status_created', table_name='enrichment_jobs')
    op.drop_index('ix_enrichment_jobs_target', table_name='enrichment_jobs')
    op.drop_table('enrichment_jobs')
    
    sa.Enum(name='enrichmentprovider').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='enrichmenttargettype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='enrichmentstatus').drop(op.get_bind(), checkfirst=True)

