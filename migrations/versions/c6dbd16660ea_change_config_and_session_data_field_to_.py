"""Change config and session data field to JSOn type

Revision ID: c6dbd16660ea
Revises: da8b38b5bdd5
Create Date: 2016-05-03 10:05:53.137091

"""

# revision identifiers, used by Alembic.
revision = "c6dbd16660ea"
down_revision = "da8b38b5bdd5"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.drop_index(op.f("ix_session_data"), table_name="session")
    op.execute("ALTER TABLE session ALTER COLUMN data TYPE JSON USING data::JSON;")

    op.drop_index(op.f("ix_config_config"), table_name="config")
    op.execute("ALTER TABLE config ALTER COLUMN config TYPE JSON USING config::JSON;")


def downgrade():
    op.execute(
        "ALTER TABLE session ALTER COLUMN data TYPE VARCHAR USING data::VARCHAR;"
    )
    op.create_index(op.f("ix_session_data"), "session", ["data"], unique=False)

    op.execute(
        "ALTER TABLE config ALTER COLUMN config TYPE VARCHAR USING config::VARCHAR;"
    )
    op.create_index(op.f("ix_config_config"), "config", ["config"], unique=False)
