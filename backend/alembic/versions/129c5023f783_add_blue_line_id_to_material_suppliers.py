"""add_blue_line_id_to_material_suppliers

Revision ID: 129c5023f783
Revises: 4a4bd2716407
Create Date: 2025-10-30 19:57:16.840455

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '129c5023f783'
down_revision: Union[str, None] = '4a4bd2716407'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add blue_line_id column to material_suppliers table"""
    with op.batch_alter_table('material_suppliers', schema=None) as batch_op:
        # Add blue_line_id column
        batch_op.add_column(sa.Column('blue_line_id', sa.Integer(), nullable=True))
        
        # Add foreign key constraint
        batch_op.create_foreign_key(
            'fk_material_suppliers_blue_line_id',
            'blue_lines',
            ['blue_line_id'],
            ['id']
        )
        
        # Add index
        batch_op.create_index('ix_material_suppliers_blue_line_id', ['blue_line_id'], unique=False)


def downgrade() -> None:
    """Remove blue_line_id column from material_suppliers table"""
    with op.batch_alter_table('material_suppliers', schema=None) as batch_op:
        # Drop index
        batch_op.drop_index('ix_material_suppliers_blue_line_id')
        
        # Drop foreign key constraint
        try:
            batch_op.drop_constraint('fk_material_suppliers_blue_line_id', type_='foreignkey')
        except:
            pass
        
        # Drop column
        batch_op.drop_column('blue_line_id')






