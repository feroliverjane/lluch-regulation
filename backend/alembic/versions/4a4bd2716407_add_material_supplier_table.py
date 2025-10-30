"""add_material_supplier_table

Revision ID: 4a4bd2716407
Revises: d768fe4481ae
Create Date: 2025-10-30 19:26:11.816838

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = '4a4bd2716407'
down_revision: Union[str, None] = 'd768fe4481ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create material_suppliers table"""
    op.create_table(
        'material_suppliers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('questionnaire_id', sa.Integer(), nullable=False),
        sa.Column('blue_line_id', sa.Integer(), nullable=True),
        sa.Column('supplier_code', sa.String(length=100), nullable=False),
        sa.Column('supplier_name', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='ACTIVE'),
        sa.Column('validation_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mismatch_fields', sa.JSON(), nullable=True),
        sa.Column('accepted_mismatches', sa.JSON(), nullable=True),
        sa.Column('validated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.ForeignKeyConstraint(['questionnaire_id'], ['questionnaires.id'], ),
        sa.ForeignKeyConstraint(['blue_line_id'], ['blue_lines.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('questionnaire_id', name='uq_material_supplier_questionnaire')
    )
    
    # Create indexes
    op.create_index(op.f('ix_material_suppliers_material_id'), 'material_suppliers', ['material_id'], unique=False)
    op.create_index(op.f('ix_material_suppliers_questionnaire_id'), 'material_suppliers', ['questionnaire_id'], unique=True)
    op.create_index(op.f('ix_material_suppliers_supplier_code'), 'material_suppliers', ['supplier_code'], unique=False)
    op.create_index(op.f('ix_material_suppliers_status'), 'material_suppliers', ['status'], unique=False)
    op.create_index(op.f('ix_material_suppliers_blue_line_id'), 'material_suppliers', ['blue_line_id'], unique=False)


def downgrade() -> None:
    """Drop material_suppliers table"""
    op.drop_index(op.f('ix_material_suppliers_blue_line_id'), table_name='material_suppliers')
    op.drop_index(op.f('ix_material_suppliers_status'), table_name='material_suppliers')
    op.drop_index(op.f('ix_material_suppliers_supplier_code'), table_name='material_suppliers')
    op.drop_index(op.f('ix_material_suppliers_questionnaire_id'), table_name='material_suppliers')
    op.drop_index(op.f('ix_material_suppliers_material_id'), table_name='material_suppliers')
    op.drop_table('material_suppliers')






