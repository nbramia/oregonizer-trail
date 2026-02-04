"""drop rating table

Revision ID: drop_rating_table
Revises: b2ec67e6fc85
Create Date: 2025-01-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'drop_rating_table'
down_revision = 'b2ec67e6fc85'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the rating table
    op.drop_table('rating')


def downgrade():
    # Recreate the rating table if we need to rollback
    op.create_table('rating',
        sa.Column('id', sa.INTEGER(), nullable=False),
        sa.Column('user_id', sa.INTEGER(), nullable=False),
        sa.Column('scenario_id', sa.INTEGER(), nullable=False),
        sa.Column('is_response', sa.BOOLEAN(), nullable=True),
        sa.Column('rating', sa.INTEGER(), nullable=False),
        sa.Column('submitted_at', sa.DATETIME(), nullable=False),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenario.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
