"""Add moderator log table

Revision ID: ac1680bc48
Revises: b6880387f89d
Create Date: 2016-05-08 19:50:03.469322

"""

# revision identifiers, used by Alembic.
revision = 'ac1680bc48'
down_revision = 'b6880387f89d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('moderatorlog',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('date', sa.BigInteger(), nullable=False),
                    sa.Column('moderator_id', sa.Integer(), nullable=True),
                    sa.Column('board_id', sa.Integer(), nullable=True),
                    sa.Column('type', sa.Integer(), nullable=False),
                    sa.Column('text', sa.String(), nullable=False),
                    sa.ForeignKeyConstraint(['board_id'], ['board.id'], ),
                    sa.ForeignKeyConstraint(['moderator_id'], ['moderator.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_moderatorlog_board_id'), 'moderatorlog', ['board_id'], unique=False)
    op.create_index(op.f('ix_moderatorlog_date'), 'moderatorlog', ['date'], unique=False)
    op.create_index(op.f('ix_moderatorlog_moderator_id'), 'moderatorlog', ['moderator_id'], unique=False)
    op.create_index(op.f('ix_moderatorlog_type'), 'moderatorlog', ['type'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_moderatorlog_type'), table_name='moderatorlog')
    op.drop_index(op.f('ix_moderatorlog_moderator_id'), table_name='moderatorlog')
    op.drop_index(op.f('ix_moderatorlog_date'), table_name='moderatorlog')
    op.drop_index(op.f('ix_moderatorlog_board_id'), table_name='moderatorlog')
    op.drop_table('moderatorlog')
