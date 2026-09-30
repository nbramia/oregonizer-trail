"""Add game_state table for serverless-safe game persistence

Revision ID: c3f1a2b4d5e6
Revises: merge_heads_rating
Create Date: 2026-09-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f1a2b4d5e6'
down_revision = 'merge_heads_rating'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'game_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_key', sa.String(length=128), nullable=False),
        sa.Column('state', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_key')
    )


def downgrade():
    op.drop_table('game_state')
