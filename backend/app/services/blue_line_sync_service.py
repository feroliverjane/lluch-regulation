from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.material import Material
from app.models.blue_line import BlueLine, BlueLineSyncStatus
from app.integrations.erp_adapter import ERPAdapter
from app.core.config import settings

logger = logging.getLogger(__name__)


class BlueLineSyncService:
    """Service for bidirectional synchronization between Blue Line and SAP Composite"""
    
    def __init__(self, db: Session):
        self.db = db
        self.erp_adapter = ERPAdapter()
    
    async def sync_to_sap(self, blue_line_id: int) -> Dict[str, Any]:
        """
        Sync Blue Line to SAP Composite system (for Z1 status materials)
        
        Args:
            blue_line_id: Blue Line ID to sync
            
        Returns:
            Dict with sync result details
        """
        logger.info(f"Starting sync to SAP for Blue Line {blue_line_id}")
        
        # Get Blue Line
        blue_line = self.db.query(BlueLine).filter(BlueLine.id == blue_line_id).first()
        if not blue_line:
            return {
                "success": False,
                "message": f"Blue Line {blue_line_id} not found",
                "sync_status": BlueLineSyncStatus.FAILED
            }
        
        # Get Material
        material = self.db.query(Material).filter(Material.id == blue_line.material_id).first()
        if not material:
            return {
                "success": False,
                "message": f"Material {blue_line.material_id} not found",
                "sync_status": BlueLineSyncStatus.FAILED
            }
        
        # Validate eligibility for Z1 sync
        if not self.validate_sync_eligibility(material, direction="to_sap"):
            return {
                "success": False,
                "message": f"Material {material.reference_code} is not eligible for Z1→SAP sync (sap_status: {material.sap_status})",
                "sync_status": BlueLineSyncStatus.NOT_REQUIRED
            }
        
        # Prepare SAP payload
        sap_payload = self.prepare_sap_payload(blue_line, material)
        
        # Send to SAP via ERP adapter
        try:
            sync_success = await self.erp_adapter.sync_blue_line_to_composite(
                reference_code=material.reference_code,
                blue_line_data=sap_payload
            )
            
            if sync_success:
                # Update Blue Line sync status
                blue_line.sync_status = BlueLineSyncStatus.SYNCED
                blue_line.last_synced_at = datetime.now()
                blue_line.sync_error_message = None
                self.db.commit()
                
                logger.info(f"Successfully synced Blue Line {blue_line_id} to SAP")
                return {
                    "success": True,
                    "message": "Blue Line successfully synced to SAP Composite",
                    "sync_status": BlueLineSyncStatus.SYNCED,
                    "synced_at": blue_line.last_synced_at
                }
            else:
                # Update sync status to failed
                blue_line.sync_status = BlueLineSyncStatus.FAILED
                blue_line.sync_error_message = "ERP adapter returned failure"
                self.db.commit()
                
                return {
                    "success": False,
                    "message": "Failed to sync to SAP (ERP adapter error)",
                    "sync_status": BlueLineSyncStatus.FAILED,
                    "error_details": "ERP sync returned false"
                }
                
        except Exception as e:
            logger.error(f"Error syncing Blue Line {blue_line_id} to SAP: {e}")
            blue_line.sync_status = BlueLineSyncStatus.FAILED
            blue_line.sync_error_message = str(e)
            self.db.commit()
            
            return {
                "success": False,
                "message": f"Exception during SAP sync: {str(e)}",
                "sync_status": BlueLineSyncStatus.FAILED,
                "error_details": str(e)
            }
    
    async def import_from_sap(self, material_id: int) -> Dict[str, Any]:
        """
        Import composite data from SAP to Blue Line (for Z2 status materials)
        
        Args:
            material_id: Material ID to import for
            
        Returns:
            Dict with import result details
        """
        logger.info(f"Starting import from SAP for Material {material_id}")
        
        # Get Material
        material = self.db.query(Material).filter(Material.id == material_id).first()
        if not material:
            return {
                "success": False,
                "message": f"Material {material_id} not found",
                "sync_status": BlueLineSyncStatus.FAILED
            }
        
        # Validate eligibility for Z2 import
        if not self.validate_sync_eligibility(material, direction="from_sap"):
            return {
                "success": False,
                "message": f"Material {material.reference_code} is not eligible for Z2←SAP import (sap_status: {material.sap_status})",
                "sync_status": BlueLineSyncStatus.NOT_REQUIRED
            }
        
        # Import from SAP via ERP adapter
        try:
            sap_data = await self.erp_adapter.import_composite_data(material.reference_code)
            
            if not sap_data:
                return {
                    "success": False,
                    "message": f"No composite data found in SAP for {material.reference_code}",
                    "sync_status": BlueLineSyncStatus.FAILED
                }
            
            # Parse SAP response into Blue Line format
            blue_line_data = self.parse_sap_response(sap_data)
            
            # Check if Blue Line already exists
            blue_line = self.db.query(BlueLine).filter(
                BlueLine.material_id == material_id,
                BlueLine.supplier_code == material.supplier_code
            ).first()
            
            if blue_line:
                # Update existing
                blue_line.blue_line_data = blue_line_data
                blue_line.sync_status = BlueLineSyncStatus.SYNCED
                blue_line.last_synced_at = datetime.now()
                blue_line.sync_error_message = None
                blue_line.bl_metadata = blue_line.bl_metadata or {}
                blue_line.bl_metadata["last_sap_import"] = datetime.now().isoformat()
            else:
                # Create new Blue Line from SAP data
                from app.models.blue_line import BlueLineMaterialType
                blue_line = BlueLine(
                    material_id=material_id,
                    supplier_code=material.supplier_code or "UNKNOWN",
                    blue_line_data=blue_line_data,
                    material_type=BlueLineMaterialType.Z001,  # Default for Z2 imports
                    sync_status=BlueLineSyncStatus.SYNCED,
                    last_synced_at=datetime.now(),
                    bl_metadata={"sap_import": datetime.now().isoformat()}
                )
                self.db.add(blue_line)
            
            self.db.commit()
            self.db.refresh(blue_line)
            
            logger.info(f"Successfully imported SAP data to Blue Line for Material {material_id}")
            return {
                "success": True,
                "message": "Successfully imported SAP Composite data to Blue Line",
                "sync_status": BlueLineSyncStatus.SYNCED,
                "synced_at": blue_line.last_synced_at,
                "blue_line_id": blue_line.id
            }
            
        except Exception as e:
            logger.error(f"Error importing from SAP for Material {material_id}: {e}")
            return {
                "success": False,
                "message": f"Exception during SAP import: {str(e)}",
                "sync_status": BlueLineSyncStatus.FAILED,
                "error_details": str(e)
            }
    
    def validate_sync_eligibility(self, material: Material, direction: str) -> bool:
        """
        Check if material is eligible for sync
        
        Args:
            material: Material object
            direction: "to_sap" for Z1→SAP, "from_sap" for Z2←SAP
            
        Returns:
            True if eligible, False otherwise
        """
        if not settings.BLUE_LINE_AUTO_SYNC_ENABLED:
            logger.info("Blue Line auto-sync is disabled in settings")
            return False
        
        if direction == "to_sap":
            # Z1 materials (active/validated) should sync TO SAP
            return material.sap_status == "Z1"
        
        elif direction == "from_sap":
            # Z2 materials (provisional) should import FROM SAP
            return material.sap_status == "Z2"
        
        return False
    
    def prepare_sap_payload(self, blue_line: BlueLine, material: Material) -> Dict[str, Any]:
        """
        Transform Blue Line data to SAP-compatible format
        
        Args:
            blue_line: BlueLine object
            material: Material object
            
        Returns:
            SAP-formatted payload
        """
        # This is a simplified version. In production, you would map
        # the 446 Blue Line fields to SAP's expected format
        
        payload = {
            "material_code": material.reference_code,
            "lluch_reference": material.lluch_reference or material.reference_code,
            "supplier_code": blue_line.supplier_code,
            "material_type": blue_line.material_type.value,
            "sync_timestamp": datetime.now().isoformat(),
            "fields": blue_line.blue_line_data,
            "metadata": {
                "source": "Lluch Blue Line System",
                "calculated_at": blue_line.calculated_at.isoformat() if blue_line.calculated_at else None,
                "version": "1.0"
            }
        }
        
        return payload
    
    def parse_sap_response(self, sap_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform SAP composite data to Blue Line format
        
        Args:
            sap_data: Data received from SAP
            
        Returns:
            Blue Line formatted data (446 fields)
        """
        # This is a simplified version. In production, you would map
        # SAP's format to the 446 Blue Line fields
        
        blue_line_data = {}
        
        # Extract common fields from SAP format
        if "fields" in sap_data:
            blue_line_data = sap_data["fields"]
        
        # Map specific SAP fields to Blue Line fields
        if "composition" in sap_data:
            blue_line_data["sap_composition"] = sap_data["composition"]
        
        if "specifications" in sap_data:
            blue_line_data["sap_specifications"] = sap_data["specifications"]
        
        # Add SAP import metadata
        blue_line_data["_sap_import_timestamp"] = datetime.now().isoformat()
        blue_line_data["_sap_source"] = "SAP Composite System"
        
        return blue_line_data
    
    async def bulk_sync_pending(self) -> Dict[str, Any]:
        """
        Sync all Blue Lines with PENDING status
        
        Returns:
            Summary of sync operations
        """
        logger.info("Starting bulk sync of pending Blue Lines")
        
        # Get all pending Blue Lines for Z1 materials
        pending_blue_lines = self.db.query(BlueLine).join(
            Material, BlueLine.material_id == Material.id
        ).filter(
            BlueLine.sync_status == BlueLineSyncStatus.PENDING,
            Material.sap_status == "Z1"
        ).all()
        
        results = {
            "total": len(pending_blue_lines),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "errors": []
        }
        
        for blue_line in pending_blue_lines:
            try:
                sync_result = await self.sync_to_sap(blue_line.id)
                if sync_result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "blue_line_id": blue_line.id,
                        "error": sync_result.get("message")
                    })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "blue_line_id": blue_line.id,
                    "error": str(e)
                })
        
        logger.info(f"Bulk sync completed: {results['success']} success, {results['failed']} failed")
        return results

