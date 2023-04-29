"""Add board moderator roles

Revision ID: da8b38b5bdd5
Revises: 90ac01a2df
Create Date: 2016-05-03 09:32:06.756899

"""

# revision identifiers, used by Alembic.
revision = "da8b38b5bdd5"
down_revision = "90ac01a2df"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.drop_index(op.f("ix_boardmoderator_board_id"), table_name="boardmoderator")
    op.drop_index(op.f("ix_boardmoderator_moderator_id"), table_name="boardmoderator")
    op.drop_table("boardmoderator")

    op.create_table(
        "boardmoderator",
        sa.Column("board_id", sa.Integer(), nullable=False),
        sa.Column("moderator_id", sa.Integer(), nullable=False),
        sa.Column("roles", postgresql.ARRAY(sa.String()), nullable=False),
        sa.ForeignKeyConstraint(
            ["board_id"],
            ["board.id"],
        ),
        sa.ForeignKeyConstraint(
            ["moderator_id"],
            ["moderator.id"],
        ),
        sa.PrimaryKeyConstraint("board_id", "moderator_id"),
    )
    op.create_index(
        op.f("ix_boardmoderator_roles"), "boardmoderator", ["roles"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_boardmoderator_roles"), table_name="boardmoderator")
    op.drop_table("boardmoderator")

    op.create_table(
        "boardmoderator",
        sa.Column("board_id", sa.Integer(), nullable=True),
        sa.Column("moderator_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["board_id"],
            ["board.id"],
        ),
        sa.ForeignKeyConstraint(
            ["moderator_id"],
            ["moderator.id"],
        ),
    )
    op.create_index(
        op.f("ix_boardmoderator_board_id"), "boardmoderator", ["board_id"], unique=False
    )
    op.create_index(
        op.f("ix_boardmoderator_moderator_id"),
        "boardmoderator",
        ["moderator_id"],
        unique=False,
    )
