"""add_template_and_composite_to_blue_line

Revision ID: 616f63814358
Revises: ad69d462af79
Create Date: 2025-10-30 17:55:25.402351

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = '616f63814358'
down_revision: Union[str, None] = 'ad69d462af79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add template_id, responses, and composite_id to blue_lines table
    with op.batch_alter_table('blue_lines', schema=None) as batch_op:
        # Add template_id (nullable, can be set later)
        batch_op.add_column(sa.Column('template_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_blue_lines_template_id', ['template_id'], unique=False)
        batch_op.create_foreign_key('fk_blue_lines_template_id', 'questionnaire_templates', ['template_id'], ['id'])
        
        # Add responses column (JSON format like Questionnaire)
        batch_op.add_column(sa.Column('responses', sa.JSON(), nullable=True))
        
        # Add composite_id (nullable, unique - one composite per blue line)
        batch_op.add_column(sa.Column('composite_id', sa.Integer(), nullable=True))
        batch_op.create_index('ix_blue_lines_composite_id', ['composite_id'], unique=True)
        batch_op.create_foreign_key('fk_blue_lines_composite_id', 'composites', ['composite_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('blue_lines', schema=None) as batch_op:
        batch_op.drop_constraint('fk_blue_lines_composite_id', type_='foreignkey')
        batch_op.drop_index('ix_blue_lines_composite_id')
        batch_op.drop_column('composite_id')
        
        batch_op.drop_column('responses')
        
        batch_op.drop_constraint('fk_blue_lines_template_id', type_='foreignkey')
        batch_op.drop_index('ix_blue_lines_template_id')
        batch_op.drop_column('template_id')






