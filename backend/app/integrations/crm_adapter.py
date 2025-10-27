from typing import Dict, Any, List
import httpx
from app.core.config import settings


class CRMAdapter:
    """Adapter for CRM system integration"""
    
    def __init__(self):
        self.api_url = settings.CRM_API_URL
        self.api_key = settings.CRM_API_KEY
        self.enabled = bool(self.api_url and self.api_key)
    
    async def notify_composite_approval(
        self, 
        material_reference: str,
        material_name: str,
        composite_version: int,
        customer_ids: List[int] = None
    ) -> bool:
        """
        Notify CRM about composite approval
        
        Args:
            material_reference: Material reference code
            material_name: Material name
            composite_version: Composite version
            customer_ids: List of customer IDs to notify (None = all customers)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print(f"CRM integration not configured. Would notify about {material_reference} v{composite_version}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                notification_data = {
                    "material_reference": material_reference,
                    "material_name": material_name,
                    "composite_version": composite_version,
                    "notification_type": "composite_approved",
                    "customer_ids": customer_ids
                }
                
                response = await client.post(
                    f"{self.api_url}/notifications",
                    json=notification_data,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error sending CRM notification: {e}")
            return False
    
    async def get_material_customers(self, material_reference: str) -> List[Dict[str, Any]]:
        """
        Get list of customers for a material
        
        Args:
            material_reference: Material reference code
            
        Returns:
            List of customer data
        """
        if not self.enabled:
            print(f"CRM integration not configured. Would get customers for {material_reference}")
            return []
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/materials/{material_reference}/customers",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return []
        except Exception as e:
            print(f"Error getting customers from CRM: {e}")
            return []








