"""Add parent_id to comment table for replies

Revision ID: a1b2c3d4e5f6
Revises: 4f6a09bb4bfb
Create Date: 2025-01-23 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '4f6a09bb4bfb'
branch_labels = None
depends_on = None


def upgrade():
    # Add parent_id column to comment table
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_comment_parent', 'comment', ['parent_id'], ['id'])


def downgrade():
    # Remove parent_id column from comment table
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.drop_constraint('fk_comment_parent', type_='foreignkey')
        batch_op.drop_column('parent_id')

