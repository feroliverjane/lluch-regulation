from typing import Dict, Any, Optional
import httpx
from app.core.config import settings


class ChemSDAdapter:
    """Adapter for ChemSD integration"""
    
    def __init__(self):
        self.api_url = settings.CHEMSD_API_URL
        self.api_key = settings.CHEMSD_API_KEY
        self.enabled = bool(self.api_url and self.api_key)
    
    async def export_composite(self, composite_id: int, composite_data: Dict[str, Any]) -> bool:
        """
        Export composite data to ChemSD
        
        Args:
            composite_id: ID of the composite
            composite_data: Composite data to export
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print(f"ChemSD integration not configured. Would export composite {composite_id}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/composites",
                    json=composite_data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error exporting to ChemSD: {e}")
            return False
    
    async def import_component_data(self, cas_number: str) -> Optional[Dict[str, Any]]:
        """
        Import component data from ChemSD by CAS number
        
        Args:
            cas_number: CAS number of the component
            
        Returns:
            Component data if found, None otherwise
        """
        if not self.enabled:
            print(f"ChemSD integration not configured. Would import CAS {cas_number}")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/components/{cas_number}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error importing from ChemSD: {e}")
            return None
    
    async def sync_material(self, material_id: int, material_data: Dict[str, Any]) -> bool:
        """
        Sync material data with ChemSD
        
        Args:
            material_id: ID of the material
            material_data: Material data to sync
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print(f"ChemSD integration not configured. Would sync material {material_id}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.api_url}/materials/{material_id}",
                    json=material_data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error syncing to ChemSD: {e}")
            return False






