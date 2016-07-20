"""Add refnos to threads

Revision ID: ffcec420c0bd
Revises: ac1680bc48
Create Date: 2016-07-17 18:40:09.411372

"""

# revision identifiers, used by Alembic.
from sqlalchemy.orm import Session

from uchan.lib.models import Board
from uchan.lib.models import Thread

revision = 'ffcec420c0bd'
down_revision = 'ac1680bc48'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('board', sa.Column('refno_counter', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('thread', sa.Column('refno', sa.Integer(), nullable=False, server_default='1'))
    op.create_index(op.f('ix_thread_refno'), 'thread', ['refno'], unique=False)

    # Adds refnos to each thread, and sets the refno_counter of the board to the last one set
    print('Changing to thread refnos!')
    db = Session(bind=op.get_bind())
    boards = db.query(Board).all()
    for board in boards:
        print('Changing board {}'.format(board.name))
        threads = db.query(Thread).filter(Thread.board_id == board.id).order_by(Thread.id.asc())
        refno = 1
        for thread in threads:
            thread.refno = refno
            refno += 1
            if refno % 30 == 0:
                print('{}/{}'.format(refno, len(threads)))
        board.refno_counter = refno

        db.commit()

    print('Removing defaults...')

    # Remove the default again, it has to be manually set on new models
    op.alter_column('board', 'refno_counter', server_default=None)
    op.alter_column('thread', 'refno', server_default=None)

    print('Done')


def downgrade():
    op.drop_index(op.f('ix_thread_refno'), table_name='thread')
    op.drop_column('thread', 'refno')
    op.drop_column('board', 'refno_counter')
