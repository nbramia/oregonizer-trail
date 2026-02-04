"""Merge rating table heads

Revision ID: merge_heads_rating
Revises: a5307423edb5, drop_rating_table
Create Date: 2025-01-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'merge_heads_rating'
down_revision = ('a5307423edb5', 'drop_rating_table')
branch_labels = None
depends_on = None


def upgrade():
    # No changes needed - both paths lead to same state (no rating table)
    pass


def downgrade():
    # No changes needed
    pass
