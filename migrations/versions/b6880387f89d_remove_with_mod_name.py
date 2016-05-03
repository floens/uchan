"""Remove with mod name

Revision ID: b6880387f89d
Revises: c6dbd16660ea
Create Date: 2016-05-03 13:06:56.020812

"""

# revision identifiers, used by Alembic.
revision = 'b6880387f89d'
down_revision = 'c6dbd16660ea'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.drop_column('post', 'with_mod_name')


def downgrade():
    op.add_column('post', sa.Column('with_mod_name', sa.BOOLEAN(), autoincrement=False, nullable=False))
