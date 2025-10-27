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

    # Blue Line specific methods
    
    async def get_purchase_history_last_n_years(
        self, 
        reference_code: str,
        years: int = 3
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get purchase history for the last N years from ERP (for Blue Line eligibility)
        
        Args:
            reference_code: Material reference code
            years: Number of years to look back (default 3)
            
        Returns:
            List of purchase records within timeframe if found, None otherwise
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would get {years}-year purchase history for {reference_code}")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/purchases/{reference_code}",
                    params={"years": years},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error getting {years}-year purchase history from ERP: {e}")
            return None
    
    async def get_material_sap_status(self, reference_code: str) -> Optional[str]:
        """
        Get SAP status for a material (Z1, Z2, Z001, Z002)
        
        Args:
            reference_code: Material reference code
            
        Returns:
            SAP status string if found, None otherwise
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would get SAP status for {reference_code}")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/materials/{reference_code}/status",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("sap_status")
                return None
        except Exception as e:
            print(f"Error getting SAP status from ERP: {e}")
            return None
    
    async def sync_blue_line_to_composite(
        self, 
        reference_code: str,
        blue_line_data: Dict[str, Any]
    ) -> bool:
        """
        Sync Blue Line data to SAP Composite system (for Z1 materials)
        
        Args:
            reference_code: Material reference code
            blue_line_data: Blue Line 446 fields data
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would sync Blue Line to SAP Composite for {reference_code}")
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/composite/blue-line-sync",
                    json={
                        "reference_code": reference_code,
                        "blue_line_data": blue_line_data
                    },
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=60.0
                )
                return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error syncing Blue Line to SAP Composite: {e}")
            return False
    
    async def import_composite_data(self, reference_code: str) -> Optional[Dict[str, Any]]:
        """
        Import composite data from SAP (for Z2 materials)
        
        Args:
            reference_code: Material reference code
            
        Returns:
            Composite data dictionary if found, None otherwise
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would import composite data from SAP for {reference_code}")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/composite/{reference_code}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error importing composite data from SAP: {e}")
            return None
    
    async def get_homologation_records(
        self, 
        material_id: int,
        supplier_code: str
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get homologation records for material-supplier pair from ERP
        
        Args:
            material_id: Material ID
            supplier_code: Supplier code
            
        Returns:
            List of homologation records with states
        """
        if not self.enabled:
            print(f"ERP integration not configured. Would get homologation records for material {material_id}, supplier {supplier_code}")
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/homologation",
                    params={"material_id": material_id, "supplier_code": supplier_code},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    return response.json()
                return None
        except Exception as e:
            print(f"Error getting homologation records from ERP: {e}")
            return None






