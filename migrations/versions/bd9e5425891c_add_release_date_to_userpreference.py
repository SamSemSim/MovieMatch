"""Add release_date to UserPreference

Revision ID: bd9e5425891c
Revises: 807f3a057073
Create Date: 2025-01-03 16:16:05.780823

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd9e5425891c'
down_revision = '807f3a057073'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_preference', schema=None) as batch_op:
        batch_op.alter_column('release_date',
               existing_type=sa.VARCHAR(length=10),
               type_=sa.String(length=20),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_preference', schema=None) as batch_op:
        batch_op.alter_column('release_date',
               existing_type=sa.String(length=20),
               type_=sa.VARCHAR(length=10),
               existing_nullable=True)

    # ### end Alembic commands ###