"""product issue cols nullable

Revision ID: a8f0bacbbaef
Revises: e15cc5042999
Create Date: 2022-08-24 13:33:30.104287+00:00

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a8f0bacbbaef"
down_revision = "e15cc5042999"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "products",
        "issues_login_url",
        existing_type=sa.VARCHAR(),
        nullable=True,
        existing_server_default=sa.text(
            "'https://github.com/ITISFoundation/osparc-simcore/issues'::character varying"
        ),
    )
    op.alter_column(
        "products",
        "issues_new_url",
        existing_type=sa.VARCHAR(),
        nullable=True,
        existing_server_default=sa.text(
            "'https://github.com/ITISFoundation/osparc-simcore/issues/new'::character varying"
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "products",
        "issues_new_url",
        existing_type=sa.VARCHAR(),
        nullable=False,
        existing_server_default=sa.text(
            "'https://github.com/ITISFoundation/osparc-simcore/issues/new'::character varying"
        ),
    )
    op.alter_column(
        "products",
        "issues_login_url",
        existing_type=sa.VARCHAR(),
        nullable=False,
        existing_server_default=sa.text(
            "'https://github.com/ITISFoundation/osparc-simcore/issues'::character varying"
        ),
    )
    # ### end Alembic commands ###