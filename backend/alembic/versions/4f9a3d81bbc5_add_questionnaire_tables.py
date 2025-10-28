"""add_questionnaire_tables

Revision ID: 4f9a3d81bbc5
Revises: d1ecc018d33f
Create Date: 2025-10-28 15:21:14.779228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f9a3d81bbc5'
down_revision: Union[str, None] = 'd1ecc018d33f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create questionnaires table
    op.create_table(
        'questionnaires',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('material_id', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(length=100), nullable=False),
        sa.Column('questionnaire_type', sa.Enum('INITIAL_HOMOLOGATION', 'REHOMOLOGATION', name='questionnairetype'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('previous_version_id', sa.Integer(), nullable=True),
        sa.Column('responses', sa.JSON(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'SUBMITTED', 'IN_REVIEW', 'APPROVED', 'REJECTED', 'REQUIRES_REVISION', name='questionnairestatus'), nullable=True),
        sa.Column('ai_risk_score', sa.Integer(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_recommendation', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['material_id'], ['materials.id'], ),
        sa.ForeignKeyConstraint(['previous_version_id'], ['questionnaires.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questionnaires_id'), 'questionnaires', ['id'], unique=False)
    op.create_index(op.f('ix_questionnaires_material_id'), 'questionnaires', ['material_id'], unique=False)
    op.create_index(op.f('ix_questionnaires_status'), 'questionnaires', ['status'], unique=False)
    op.create_index(op.f('ix_questionnaires_supplier_code'), 'questionnaires', ['supplier_code'], unique=False)

    # Create questionnaire_validations table
    op.create_table(
        'questionnaire_validations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('questionnaire_id', sa.Integer(), nullable=False),
        sa.Column('validation_type', sa.Enum('BLUE_LINE_COMPARISON', 'VERSION_COMPARISON', 'AI_RISK_ASSESSMENT', name='validationtype'), nullable=False),
        sa.Column('field_name', sa.String(length=200), nullable=False),
        sa.Column('expected_value', sa.String(length=500), nullable=True),
        sa.Column('actual_value', sa.String(length=500), nullable=True),
        sa.Column('deviation_percentage', sa.Float(), nullable=True),
        sa.Column('severity', sa.Enum('INFO', 'WARNING', 'CRITICAL', name='validationseverity'), nullable=False),
        sa.Column('requires_action', sa.Boolean(), nullable=True),
        sa.Column('ai_analysis', sa.JSON(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['questionnaire_id'], ['questionnaires.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questionnaire_validations_id'), 'questionnaire_validations', ['id'], unique=False)
    op.create_index(op.f('ix_questionnaire_validations_questionnaire_id'), 'questionnaire_validations', ['questionnaire_id'], unique=False)

    # Create questionnaire_incidents table
    op.create_table(
        'questionnaire_incidents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('questionnaire_id', sa.Integer(), nullable=False),
        sa.Column('validation_id', sa.Integer(), nullable=True),
        sa.Column('field_name', sa.String(length=200), nullable=False),
        sa.Column('issue_description', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('OPEN', 'ESCALATED_TO_SUPPLIER', 'RESOLVED', 'OVERRIDDEN', name='incidentstatus'), nullable=True),
        sa.Column('resolution_action', sa.Enum('SUPPLIER_CORRECTION', 'USER_OVERRIDE', 'ESCALATED', 'PENDING', name='resolutionaction'), nullable=True),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.Column('override_justification', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('supplier_notified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['questionnaire_id'], ['questionnaires.id'], ),
        sa.ForeignKeyConstraint(['validation_id'], ['questionnaire_validations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questionnaire_incidents_id'), 'questionnaire_incidents', ['id'], unique=False)
    op.create_index(op.f('ix_questionnaire_incidents_questionnaire_id'), 'questionnaire_incidents', ['questionnaire_id'], unique=False)
    op.create_index(op.f('ix_questionnaire_incidents_status'), 'questionnaire_incidents', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_questionnaire_incidents_status'), table_name='questionnaire_incidents')
    op.drop_index(op.f('ix_questionnaire_incidents_questionnaire_id'), table_name='questionnaire_incidents')
    op.drop_index(op.f('ix_questionnaire_incidents_id'), table_name='questionnaire_incidents')
    op.drop_table('questionnaire_incidents')
    
    op.drop_index(op.f('ix_questionnaire_validations_questionnaire_id'), table_name='questionnaire_validations')
    op.drop_index(op.f('ix_questionnaire_validations_id'), table_name='questionnaire_validations')
    op.drop_table('questionnaire_validations')
    
    op.drop_index(op.f('ix_questionnaires_supplier_code'), table_name='questionnaires')
    op.drop_index(op.f('ix_questionnaires_status'), table_name='questionnaires')
    op.drop_index(op.f('ix_questionnaires_material_id'), table_name='questionnaires')
    op.drop_index(op.f('ix_questionnaires_id'), table_name='questionnaires')
    op.drop_table('questionnaires')

