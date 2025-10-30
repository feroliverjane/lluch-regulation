"""
Script to migrate existing BlueLines to include template_id, composite_id, and responses format.
Run this script once to update existing BlueLines with the new structure.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal
from app.models.blue_line import BlueLine
from app.models.composite import Composite, CompositeStatus, CompositeOrigin
from app.models.questionnaire_template import QuestionnaireTemplate, TemplateType
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_blue_lines(db: Session):
    """Migrate existing BlueLines to include template_id, composite_id, and responses"""
    
    # Get default template
    default_template = db.query(QuestionnaireTemplate).filter(
        QuestionnaireTemplate.is_default == True,
        QuestionnaireTemplate.template_type == TemplateType.INITIAL_HOMOLOGATION
    ).first()
    
    if not default_template:
        logger.warning("No default template found. Creating BlueLines without template_id.")
        default_template = None
    
    # Get all BlueLines that need migration
    blue_lines = db.query(BlueLine).filter(
        (BlueLine.template_id == None) | (BlueLine.composite_id == None)
    ).all()
    
    logger.info(f"Found {len(blue_lines)} BlueLines to migrate")
    
    migrated_count = 0
    for bl in blue_lines:
        try:
            # Assign template_id if missing
            if bl.template_id is None and default_template:
                bl.template_id = default_template.id
                logger.info(f"Assigned template_id={default_template.id} to BlueLine {bl.id}")
            
            # Create composite if missing
            if bl.composite_id is None:
                # Check if composite already exists for this material
                existing_composite = db.query(Composite).filter(
                    Composite.material_id == bl.material_id,
                    Composite.status == CompositeStatus.DRAFT
                ).first()
                
                if existing_composite:
                    bl.composite_id = existing_composite.id
                    logger.info(f"Assigned existing composite_id={existing_composite.id} to BlueLine {bl.id}")
                else:
                    # Create new empty composite
                    latest_composite = db.query(Composite).filter(
                        Composite.material_id == bl.material_id
                    ).order_by(Composite.version.desc()).first()
                    
                    next_version = (latest_composite.version + 1) if latest_composite else 1
                    
                    composite = Composite(
                        material_id=bl.material_id,
                        version=next_version,
                        origin=CompositeOrigin.MANUAL,
                        status=CompositeStatus.DRAFT,
                        composite_metadata={},
                        notes="Empty composite created for Blue Line migration - to be filled manually"
                    )
                    
                    db.add(composite)
                    db.flush()  # Flush to get the ID
                    
                    bl.composite_id = composite.id
                    logger.info(f"Created new composite_id={composite.id} for BlueLine {bl.id}")
            
            # Convert blue_line_data to responses format if template exists and responses is empty
            if default_template and not bl.responses and bl.blue_line_data:
                responses = {}
                # Simple conversion: try to map blue_line_data keys to fieldCodes
                for field in default_template.questions_schema:
                    field_code = field.get("fieldCode", "")
                    field_name = field.get("fieldName", "")
                    
                    # Try to find value in blue_line_data by fieldCode or fieldName
                    if field_code and field_code in bl.blue_line_data:
                        responses[field_code] = {
                            "value": bl.blue_line_data[field_code],
                            "name": field_name,
                            "type": field.get("fieldType", "text")
                        }
                    elif field_name and field_name in bl.blue_line_data:
                        responses[field_code] = {
                            "value": bl.blue_line_data[field_name],
                            "name": field_name,
                            "type": field.get("fieldType", "text")
                        }
                
                if responses:
                    bl.responses = responses
                    logger.info(f"Converted {len(responses)} fields to responses format for BlueLine {bl.id}")
            
            migrated_count += 1
            
        except Exception as e:
            logger.error(f"Error migrating BlueLine {bl.id}: {e}")
            db.rollback()
            continue
    
    # Commit all changes
    try:
        db.commit()
        logger.info(f"Successfully migrated {migrated_count} BlueLines")
    except Exception as e:
        logger.error(f"Error committing migration: {e}")
        db.rollback()
        raise


if __name__ == "__main__":
    db = SessionLocal()
    try:
        migrate_blue_lines(db)
        print("\n✅ Migration completed successfully!")
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

