"""remove submit timestamp

Revision ID: 52a0e8148dd5
Revises: 77ac824a77ff
Create Date: 2024-12-16 14:55:15.114923+00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '52a0e8148dd5'
down_revision = '77ac824a77ff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('comp_tasks', 'submit')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comp_tasks', sa.Column('submit', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
