from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.core.config import settings
from app.models.composite import Composite, CompositeStatus
from app.models.material import Material
from app.services.composite_calculator import CompositeCalculator
from app.services.composite_comparator import CompositeComparator


@celery_app.task(name="app.tasks.review_composites")
def review_composites():
    """
    Periodic task to review composites
    Recalculates composites that haven't been updated in REVIEW_PERIOD_DAYS
    """
    db: Session = SessionLocal()
    
    try:
        # Get materials with approved composites older than review period
        review_date = datetime.now() - timedelta(days=settings.REVIEW_PERIOD_DAYS)
        
        # Find materials needing review
        materials_needing_review = db.query(Material).join(Composite).filter(
            Composite.status == CompositeStatus.APPROVED,
            Composite.approved_at < review_date
        ).distinct().all()
        
        reviewed_count = 0
        significant_changes_count = 0
        
        for material in materials_needing_review:
            # Get latest approved composite
            latest_composite = db.query(Composite).filter(
                Composite.material_id == material.id,
                Composite.status == CompositeStatus.APPROVED
            ).order_by(Composite.version.desc()).first()
            
            if not latest_composite:
                continue
            
            # Recalculate composite
            calculator = CompositeCalculator(db)
            try:
                new_composite = calculator.calculate_from_lab_analyses(
                    material_id=material.id,
                    notes=f"Automatic review - comparing to v{latest_composite.version}"
                )
                
                # Don't save yet, just compare
                # Temporarily add to session to get components loaded
                db.add(new_composite)
                db.flush()
                
                # Compare with latest
                comparator = CompositeComparator(db)
                # Need to compare components directly since new_composite not committed
                comparison_result = _compare_composite_components(
                    latest_composite, 
                    new_composite, 
                    settings.COMPOSITE_THRESHOLD_PERCENT
                )
                
                if comparison_result['significant_changes']:
                    # Save the new composite for review
                    db.commit()
                    db.refresh(new_composite)
                    
                    significant_changes_count += 1
                    
                    # TODO: Send notification to technical team
                    print(f"Significant changes detected in {material.reference_code} v{new_composite.version}")
                    print(f"Total change score: {comparison_result['total_change']:.2f}%")
                else:
                    # No significant changes, rollback
                    db.rollback()
                
                reviewed_count += 1
                
            except ValueError as e:
                print(f"Error reviewing material {material.reference_code}: {e}")
                db.rollback()
                continue
        
        print(f"Composite review completed: {reviewed_count} materials reviewed, {significant_changes_count} with significant changes")
        return {
            "reviewed_count": reviewed_count,
            "significant_changes_count": significant_changes_count
        }
        
    except Exception as e:
        print(f"Error in review_composites task: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.cleanup_old_drafts")
def cleanup_old_drafts():
    """
    Clean up old draft composites (older than 30 days)
    """
    db: Session = SessionLocal()
    
    try:
        cleanup_date = datetime.now() - timedelta(days=30)
        
        # Find old drafts
        old_drafts = db.query(Composite).filter(
            Composite.status == CompositeStatus.DRAFT,
            Composite.created_at < cleanup_date
        ).all()
        
        deleted_count = 0
        for draft in old_drafts:
            db.delete(draft)
            deleted_count += 1
        
        db.commit()
        
        print(f"Cleaned up {deleted_count} old draft composites")
        return {"deleted_count": deleted_count}
        
    except Exception as e:
        print(f"Error in cleanup_old_drafts task: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def _compare_composite_components(old_composite, new_composite, threshold):
    """Helper function to compare composite components"""
    
    # Create component maps
    old_components = {
        (c.cas_number or c.component_name.lower()): c.percentage
        for c in old_composite.components
    }
    new_components = {
        (c.cas_number or c.component_name.lower()): c.percentage
        for c in new_composite.components
    }
    
    total_change = 0.0
    
    # Calculate changes
    all_keys = set(old_components.keys()) | set(new_components.keys())
    for key in all_keys:
        old_pct = old_components.get(key, 0.0)
        new_pct = new_components.get(key, 0.0)
        total_change += abs(new_pct - old_pct)
    
    return {
        "total_change": total_change,
        "significant_changes": total_change >= threshold
    }








