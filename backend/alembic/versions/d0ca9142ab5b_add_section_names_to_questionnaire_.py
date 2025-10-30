"""add_section_names_to_questionnaire_template

Revision ID: d0ca9142ab5b
Revises: a52fe613a7ad
Create Date: 2025-10-30 15:21:36.330405

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0ca9142ab5b'
down_revision: Union[str, None] = 'a52fe613a7ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add section_names column to questionnaire_templates table
    op.add_column('questionnaire_templates', 
        sa.Column('section_names', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    # Remove section_names column
    op.drop_column('questionnaire_templates', 'section_names')






