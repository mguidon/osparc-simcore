"""rm dags table

Revision ID: d1fafda96f4c
Revises: 481d5b472721
Create Date: 2024-07-09 14:02:31.583952+00:00

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d1fafda96f4c"
down_revision = "481d5b472721"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("ix_dags_contact", table_name="dags")
    op.drop_index("ix_dags_id", table_name="dags")
    op.drop_index("ix_dags_key", table_name="dags")
    op.drop_table("dags")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "dags",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("key", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("version", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("description", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("contact", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column(
            "workbench",
            postgresql.JSON(astext_type=sa.Text()),
            autoincrement=False,
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="dags_pkey"),
    )
    op.create_index("ix_dags_key", "dags", ["key"], unique=False)
    op.create_index("ix_dags_id", "dags", ["id"], unique=False)
    op.create_index("ix_dags_contact", "dags", ["contact"], unique=False)
    # ### end Alembic commands ###
