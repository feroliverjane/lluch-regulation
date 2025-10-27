from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings


class ERPAdapter:
    """Adapter for ERP system integration"""
    
    def __init__(self):
        self.api_url = settings.ERP_API_URL
        self.api_key = settings.ERP_API_KEY
        self.enabled = bool(self.api_url and self.api_key)
    
    async def sync_material(self, material_id: int, material_data: Dict[str, Any]) -> bool:
        """
        Sync material data with ERP
        
        Args:
            material_id: ID of the material
            material_data: Material data to sync
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would sync material {material_id}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/materials",
                    json=material_data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error syncing to ERP: {e}")
            return False
    
    async def update_inventory(
        self, 
        material_id: int, 
        reference_code: str, 
        composite_version: int
    ) -> bool:
        """
        Update material inventory information in ERP
        
        Args:
            material_id: ID of the material
            reference_code: Material reference code
            composite_version: Composite version number
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would update inventory for {reference_code}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.api_url}/inventory/{reference_code}",
                    json={"composite_version": composite_version},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Error updating ERP inventory: {e}")
            return False
    
    async def get_purchase_history(self, reference_code: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get purchase history from ERP
        
        Args:
            reference_code: Material reference code
            
        Returns:
            List of purchase records if found, None otherwise
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would get purchase history for {reference_code}")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/purchases/{reference_code}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error getting purchase history from ERP: {e}")
            return None








