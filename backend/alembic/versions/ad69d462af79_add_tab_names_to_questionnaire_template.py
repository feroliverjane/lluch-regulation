"""add_tab_names_to_questionnaire_template

Revision ID: ad69d462af79
Revises: d0ca9142ab5b
Create Date: 2025-10-30 15:33:28.556188

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad69d462af79'
down_revision: Union[str, None] = 'd0ca9142ab5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add tab_names column to questionnaire_templates table
    op.add_column('questionnaire_templates', 
        sa.Column('tab_names', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    # Remove tab_names column
    op.drop_column('questionnaire_templates', 'tab_names')






