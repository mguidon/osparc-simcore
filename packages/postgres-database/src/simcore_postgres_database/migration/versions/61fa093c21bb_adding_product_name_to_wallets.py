"""adding product_name to wallets

Revision ID: 61fa093c21bb
Revises: ae72826e75fc
Create Date: 2023-09-20 14:42:10.661569+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "61fa093c21bb"
down_revision = "ae72826e75fc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("wallets", sa.Column("product_name", sa.String(), nullable=True))
    op.execute(
        sa.DDL("UPDATE wallets SET product_name = 'osparc' WHERE product_name IS NULL")
    )
    op.alter_column(
        "wallets",
        "product_name",
        existing_type=sa.String(),
        nullable=False,
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("wallets", "product_name")
    # ### end Alembic commands ###