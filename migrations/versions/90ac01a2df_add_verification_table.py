"""Add verification table

Revision ID: 90ac01a2df
Revises: df61cfff356e
Create Date: 2016-04-16 17:28:20.778467

"""

# revision identifiers, used by Alembic.
revision = "90ac01a2df"
down_revision = "df61cfff356e"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table(
        "verification",
        sa.Column("verification_id", sa.String(length=32), nullable=False),
        sa.Column("ip4", sa.BigInteger(), nullable=False),
        sa.Column("expires", sa.BigInteger(), nullable=False),
        sa.Column("data", postgresql.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("verification_id"),
    )
    op.create_index(
        op.f("ix_verification_expires"), "verification", ["expires"], unique=False
    )
    op.create_index(op.f("ix_verification_ip4"), "verification", ["ip4"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_verification_ip4"), table_name="verification")
    op.drop_index(op.f("ix_verification_expires"), table_name="verification")
    op.drop_table("verification")
