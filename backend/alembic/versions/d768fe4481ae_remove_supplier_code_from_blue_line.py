"""remove_supplier_code_from_blue_line

Revision ID: d768fe4481ae
Revises: 616f63814358
Create Date: 2025-10-30 18:23:41.090632

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision: str = 'd768fe4481ae'
down_revision: Union[str, None] = '616f63814358'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Migrate BlueLine to remove supplier_code:
    1. Consolidate multiple BlueLines per material into one (keep first by ID)
    2. Remove supplier_code column
    3. Update unique constraint to material_id only
    """
    
    # Step 1: Consolidate BlueLines per material (keep first one, delete others)
    conn = op.get_bind()
    
    # For each material with multiple BlueLines, keep the first one
    conn.execute(sa.text("""
        DELETE FROM blue_lines
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM blue_lines
            GROUP BY material_id
        )
    """))
    
    # Step 2: Remove old unique constraint and indexes, then remove column
    with op.batch_alter_table('blue_lines', schema=None) as batch_op:
        # Drop old unique constraint
        try:
            batch_op.drop_constraint('uq_material_supplier', type_='unique')
        except:
            pass
        
        # Drop old indexes
        try:
            batch_op.drop_index('ix_blue_lines_supplier_code')
        except:
            pass
        
        # Drop supplier_code column
        batch_op.drop_column('supplier_code')
        
        # Add new unique constraint on material_id only
        batch_op.create_unique_constraint('uq_material_blue_line', ['material_id'])


def downgrade() -> None:
    """
    Revert migration: add supplier_code back
    Note: This will lose data consolidation, and supplier_code will be NULL
    """
    with op.batch_alter_table('blue_lines', schema=None) as batch_op:
        # Drop new constraint
        batch_op.drop_constraint('uq_material_blue_line', type_='unique')
        
        # Add supplier_code column back (nullable)
        batch_op.add_column(sa.Column('supplier_code', sa.String(100), nullable=True))
        
        # Recreate old constraint (but allow NULL supplier_code)
        # Note: SQLite doesn't support partial unique constraints well
        # So we'll just create a regular index
        batch_op.create_index('ix_blue_lines_supplier_code', ['supplier_code'])
        
        # Note: Cannot recreate exact old constraint due to NULL values
        # This is a limitation of the downgrade
