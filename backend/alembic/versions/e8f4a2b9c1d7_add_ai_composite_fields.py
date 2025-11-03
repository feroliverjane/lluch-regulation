"""add_ai_composite_fields

Revision ID: e8f4a2b9c1d7
Revises: 129c5023f783
Create Date: 2025-10-31 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f4a2b9c1d7'
down_revision: Union[str, None] = '129c5023f783'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Import for column check
    from alembic import context
    import sqlalchemy as sa_inspect
    from sqlalchemy import inspect
    
    conn = context.get_bind()
    inspector = inspect(conn)
    
    # Add new columns to composites table (check if they exist first)
    # For SQLite, we just add columns. Foreign keys will be enforced by the ORM.
    composites_columns = [col['name'] for col in inspector.get_columns('composites')]
    
    if 'composite_type' not in composites_columns:
        op.add_column('composites', sa.Column('composite_type', sa.String(length=2), nullable=True))
    if 'questionnaire_id' not in composites_columns:
        op.add_column('composites', sa.Column('questionnaire_id', sa.Integer(), nullable=True))
    if 'source_documents' not in composites_columns:
        op.add_column('composites', sa.Column('source_documents', sa.JSON(), nullable=True))
    if 'extraction_confidence' not in composites_columns:
        op.add_column('composites', sa.Column('extraction_confidence', sa.Float(), nullable=True))
    
    # Create indexes if they don't exist
    composites_indexes = [idx['name'] for idx in inspector.get_indexes('composites')]
    if 'ix_composites_questionnaire_id' not in composites_indexes:
        op.create_index('ix_composites_questionnaire_id', 'composites', ['questionnaire_id'], unique=False)
    if 'ix_composites_composite_type' not in composites_indexes:
        op.create_index('ix_composites_composite_type', 'composites', ['composite_type'], unique=False)
    
    # Add new columns to questionnaires table
    questionnaires_columns = [col['name'] for col in inspector.get_columns('questionnaires')]
    
    if 'ai_coherence_score' not in questionnaires_columns:
        op.add_column('questionnaires', sa.Column('ai_coherence_score', sa.Integer(), nullable=True))
    if 'ai_coherence_details' not in questionnaires_columns:
        op.add_column('questionnaires', sa.Column('ai_coherence_details', sa.JSON(), nullable=True))
    if 'attached_documents' not in questionnaires_columns:
        op.add_column('questionnaires', sa.Column('attached_documents', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove columns from questionnaires table
    op.drop_column('questionnaires', 'attached_documents')
    op.drop_column('questionnaires', 'ai_coherence_details')
    op.drop_column('questionnaires', 'ai_coherence_score')
    
    # Remove indexes and columns from composites
    op.drop_index('ix_composites_composite_type', table_name='composites')
    op.drop_index('ix_composites_questionnaire_id', table_name='composites')
    op.drop_column('composites', 'extraction_confidence')
    op.drop_column('composites', 'source_documents')
    op.drop_column('composites', 'questionnaire_id')
    op.drop_column('composites', 'composite_type')

