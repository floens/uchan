"""Add regcode

Revision ID: d5d3bcb14e53
Revises: ffcec420c0bd
Create Date: 2017-08-10 14:45:46.648747

"""

# revision identifiers, used by Alembic.
revision = 'd5d3bcb14e53'
down_revision = 'ffcec420c0bd'
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op


def upgrade():
    op.create_table('regcode',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('password', sa.LargeBinary(), nullable=False),
                    sa.Column('code', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_regcode_password'), 'regcode', ['password'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_regcode_password'), table_name='regcode')
    op.drop_table('regcode')
