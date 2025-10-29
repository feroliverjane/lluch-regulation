"""add_questionnaire_template_table

Revision ID: a52fe613a7ad
Revises: 4f9a3d81bbc5
Create Date: 2025-10-29 17:21:05.981056

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a52fe613a7ad'
down_revision: Union[str, None] = '4f9a3d81bbc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create questionnaire_templates table
    op.create_table(
        'questionnaire_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.Enum('INITIAL_HOMOLOGATION', 'REHOMOLOGATION', name='templatetype'), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('questions_schema', sa.JSON(), nullable=False),
        sa.Column('scoring_rules', sa.JSON(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=True),
        sa.Column('total_sections', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questionnaire_templates_id'), 'questionnaire_templates', ['id'], unique=False)
    op.create_index(op.f('ix_questionnaire_templates_template_type'), 'questionnaire_templates', ['template_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_questionnaire_templates_template_type'), table_name='questionnaire_templates')
    op.drop_index(op.f('ix_questionnaire_templates_id'), table_name='questionnaire_templates')
    op.drop_table('questionnaire_templates')

