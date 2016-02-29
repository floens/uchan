"""Initial tables

Revision ID: df61cfff356e
Revises: 
Create Date: 2016-02-29 15:57:17.971552

"""

# revision identifiers, used by Alembic.
revision = 'df61cfff356e'
down_revision = None
branch_labels = None
depends_on = None

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


def upgrade():
    op.create_table('config',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('type', sa.String(), nullable=True),
                    sa.Column('config', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_config_config'), 'config', ['config'], unique=False)
    op.create_index(op.f('ix_config_type'), 'config', ['type'], unique=False)
    op.create_table('moderator',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('username', sa.String(), nullable=True),
                    sa.Column('password', sa.LargeBinary(), nullable=True),
                    sa.Column('roles', postgresql.ARRAY(sa.String()), nullable=True),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('username')
                    )
    op.create_index(op.f('ix_moderator_roles'), 'moderator', ['roles'], unique=False)
    op.create_table('page',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('title', sa.String(), nullable=False),
                    sa.Column('link_name', sa.String(), nullable=False),
                    sa.Column('type', sa.String(), nullable=False),
                    sa.Column('order', sa.Integer(), nullable=False),
                    sa.Column('content', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('link_name')
                    )
    op.create_index(op.f('ix_page_content'), 'page', ['content'], unique=False)
    op.create_index(op.f('ix_page_order'), 'page', ['order'], unique=False)
    op.create_index(op.f('ix_page_title'), 'page', ['title'], unique=False)
    op.create_index(op.f('ix_page_type'), 'page', ['type'], unique=False)
    op.create_table('session',
                    sa.Column('session_id', sa.String(length=32), nullable=False),
                    sa.Column('data', sa.String(), nullable=False),
                    sa.Column('expires', sa.BigInteger(), nullable=False),
                    sa.PrimaryKeyConstraint('session_id')
                    )
    op.create_index(op.f('ix_session_data'), 'session', ['data'], unique=False)
    op.create_index(op.f('ix_session_expires'), 'session', ['expires'], unique=False)
    op.create_table('board',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=128), nullable=False),
                    sa.Column('config_id', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['config_id'], ['config.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_board_config_id'), 'board', ['config_id'], unique=False)
    op.create_index(op.f('ix_board_name'), 'board', ['name'], unique=True)
    op.create_table('boardmoderator',
                    sa.Column('board_id', sa.Integer(), nullable=True),
                    sa.Column('moderator_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['board_id'], ['board.id'], ),
                    sa.ForeignKeyConstraint(['moderator_id'], ['moderator.id'], )
                    )
    op.create_index(op.f('ix_boardmoderator_board_id'), 'boardmoderator', ['board_id'], unique=False)
    op.create_index(op.f('ix_boardmoderator_moderator_id'), 'boardmoderator', ['moderator_id'], unique=False)
    op.create_table('thread',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('board_id', sa.Integer(), nullable=False),
                    sa.Column('last_modified', sa.BigInteger(), nullable=False),
                    sa.Column('refno_counter', sa.Integer(), nullable=False),
                    sa.Column('sticky', sa.Boolean(), nullable=False),
                    sa.Column('locked', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['board_id'], ['board.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_thread_board_id'), 'thread', ['board_id'], unique=False)
    op.create_index(op.f('ix_thread_last_modified'), 'thread', ['last_modified'], unique=False)
    op.create_table('post',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('thread_id', sa.Integer(), nullable=False),
                    sa.Column('moderator_id', sa.Integer(), nullable=True),
                    sa.Column('date', sa.BigInteger(), nullable=False),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('subject', sa.String(), nullable=True),
                    sa.Column('text', sa.String(), nullable=True),
                    sa.Column('refno', sa.Integer(), nullable=False),
                    sa.Column('password', sa.String(), nullable=True),
                    sa.Column('ip4', sa.BigInteger(), nullable=False),
                    sa.Column('with_mod_name', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['moderator_id'], ['moderator.id'], ),
                    sa.ForeignKeyConstraint(['thread_id'], ['thread.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_post_date'), 'post', ['date'], unique=False)
    op.create_index(op.f('ix_post_ip4'), 'post', ['ip4'], unique=False)
    op.create_index(op.f('ix_post_moderator_id'), 'post', ['moderator_id'], unique=False)
    op.create_index(op.f('ix_post_refno'), 'post', ['refno'], unique=False)
    op.create_index(op.f('ix_post_text'), 'post', ['text'], unique=False)
    op.create_index(op.f('ix_post_thread_id'), 'post', ['thread_id'], unique=False)
    op.create_table('ban',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('ip4', sa.BigInteger(), nullable=False),
                    sa.Column('ip4_end', sa.BigInteger(), nullable=True),
                    sa.Column('reason', sa.String(), nullable=False),
                    sa.Column('date', sa.BigInteger(), nullable=False),
                    sa.Column('length', sa.BigInteger(), nullable=False),
                    sa.Column('board', sa.String(), nullable=True),
                    sa.Column('post', sa.Integer(), nullable=True),
                    sa.Column('moderator_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['moderator_id'], ['moderator.id'], ),
                    sa.ForeignKeyConstraint(['post'], ['post.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_ban_board'), 'ban', ['board'], unique=False)
    op.create_index(op.f('ix_ban_ip4'), 'ban', ['ip4'], unique=False)
    op.create_index(op.f('ix_ban_ip4_end'), 'ban', ['ip4_end'], unique=False)
    op.create_index(op.f('ix_ban_moderator_id'), 'ban', ['moderator_id'], unique=False)
    op.create_table('file',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('location', sa.String(), nullable=False),
                    sa.Column('thumbnail_location', sa.String(), nullable=False),
                    sa.Column('post_id', sa.Integer(), nullable=False),
                    sa.Column('original_name', sa.String(), nullable=False),
                    sa.Column('width', sa.Integer(), nullable=False),
                    sa.Column('height', sa.Integer(), nullable=False),
                    sa.Column('size', sa.Integer(), nullable=False),
                    sa.Column('thumbnail_width', sa.Integer(), nullable=False),
                    sa.Column('thumbnail_height', sa.Integer(), nullable=False),
                    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_file_location'), 'file', ['location'], unique=False)
    op.create_index(op.f('ix_file_post_id'), 'file', ['post_id'], unique=False)
    op.create_index(op.f('ix_file_thumbnail_location'), 'file', ['thumbnail_location'], unique=False)
    op.create_table('report',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('post_id', sa.Integer(), nullable=False),
                    sa.Column('count', sa.Integer(), nullable=False),
                    sa.Column('date', sa.BigInteger(), nullable=False),
                    sa.ForeignKeyConstraint(['post_id'], ['post.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_report_date'), 'report', ['date'], unique=False)
    op.create_index(op.f('ix_report_post_id'), 'report', ['post_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_report_post_id'), table_name='report')
    op.drop_index(op.f('ix_report_date'), table_name='report')
    op.drop_table('report')
    op.drop_index(op.f('ix_file_thumbnail_location'), table_name='file')
    op.drop_index(op.f('ix_file_post_id'), table_name='file')
    op.drop_index(op.f('ix_file_location'), table_name='file')
    op.drop_table('file')
    op.drop_index(op.f('ix_ban_moderator_id'), table_name='ban')
    op.drop_index(op.f('ix_ban_ip4_end'), table_name='ban')
    op.drop_index(op.f('ix_ban_ip4'), table_name='ban')
    op.drop_index(op.f('ix_ban_board'), table_name='ban')
    op.drop_table('ban')
    op.drop_index(op.f('ix_post_thread_id'), table_name='post')
    op.drop_index(op.f('ix_post_text'), table_name='post')
    op.drop_index(op.f('ix_post_refno'), table_name='post')
    op.drop_index(op.f('ix_post_moderator_id'), table_name='post')
    op.drop_index(op.f('ix_post_ip4'), table_name='post')
    op.drop_index(op.f('ix_post_date'), table_name='post')
    op.drop_table('post')
    op.drop_index(op.f('ix_thread_last_modified'), table_name='thread')
    op.drop_index(op.f('ix_thread_board_id'), table_name='thread')
    op.drop_table('thread')
    op.drop_index(op.f('ix_boardmoderator_moderator_id'), table_name='boardmoderator')
    op.drop_index(op.f('ix_boardmoderator_board_id'), table_name='boardmoderator')
    op.drop_table('boardmoderator')
    op.drop_index(op.f('ix_board_name'), table_name='board')
    op.drop_index(op.f('ix_board_config_id'), table_name='board')
    op.drop_table('board')
    op.drop_index(op.f('ix_session_expires'), table_name='session')
    op.drop_index(op.f('ix_session_data'), table_name='session')
    op.drop_table('session')
    op.drop_index(op.f('ix_page_type'), table_name='page')
    op.drop_index(op.f('ix_page_title'), table_name='page')
    op.drop_index(op.f('ix_page_order'), table_name='page')
    op.drop_index(op.f('ix_page_content'), table_name='page')
    op.drop_table('page')
    op.drop_index(op.f('ix_moderator_roles'), table_name='moderator')
    op.drop_table('moderator')
    op.drop_index(op.f('ix_config_type'), table_name='config')
    op.drop_index(op.f('ix_config_config'), table_name='config')
    op.drop_table('config')
