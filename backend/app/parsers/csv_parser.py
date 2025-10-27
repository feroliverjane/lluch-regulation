import pandas as pd
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class ChromatographicCSVParser:
    """Parser for chromatographic analysis CSV files"""
    
    # Common column name variations
    CAS_COLUMNS = ['cas', 'cas_number', 'cas number', 'cas no', 'cas_no', 'casnumber']
    COMPONENT_COLUMNS = ['component', 'compound', 'name', 'component_name', 'substance', 'chemical']
    PERCENTAGE_COLUMNS = ['percentage', '%', 'percent', 'concentration', 'amount', 'area%', 'area_percent']
    
    # Thresholds
    IMPURITY_THRESHOLD = 1.0  # Components < 1% considered impurities by default
    
    def __init__(self):
        self.data = None
        self.parsed_components = []
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a chromatographic CSV file
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dictionary with parsed data and metadata
        """
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin1', 'iso-8859-1']:
                try:
                    self.data = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if self.data is None:
                raise ValueError("Could not read CSV file with any common encoding")
            
            # Normalize column names
            self.data.columns = [col.lower().strip() for col in self.data.columns]
            
            # Identify columns
            cas_col = self._find_column(self.CAS_COLUMNS)
            component_col = self._find_column(self.COMPONENT_COLUMNS)
            percentage_col = self._find_column(self.PERCENTAGE_COLUMNS)
            
            if not component_col or not percentage_col:
                raise ValueError("Could not identify required columns (component and percentage)")
            
            # Parse components
            self.parsed_components = []
            total_percentage = 0.0
            
            for _, row in self.data.iterrows():
                component = self._parse_component(row, cas_col, component_col, percentage_col)
                if component:
                    self.parsed_components.append(component)
                    total_percentage += component['percentage']
            
            # Validate total percentage
            validation_errors = []
            if not (95.0 <= total_percentage <= 105.0):
                validation_errors.append(f"Total percentage {total_percentage:.2f}% is outside valid range (95-105%)")
            
            # Normalize to 100% if close enough
            if 98.0 <= total_percentage <= 102.0:
                normalization_factor = 100.0 / total_percentage
                for component in self.parsed_components:
                    component['percentage'] *= normalization_factor
                total_percentage = 100.0
            
            return {
                'components': self.parsed_components,
                'total_percentage': total_percentage,
                'component_count': len(self.parsed_components),
                'validation_errors': validation_errors,
                'success': len(validation_errors) == 0
            }
            
        except Exception as e:
            return {
                'components': [],
                'total_percentage': 0.0,
                'component_count': 0,
                'validation_errors': [str(e)],
                'success': False
            }
    
    def _find_column(self, possible_names: List[str]) -> Optional[str]:
        """Find a column by trying multiple possible names"""
        for col_name in self.data.columns:
            if col_name in possible_names:
                return col_name
        return None
    
    def _parse_component(
        self, 
        row: pd.Series, 
        cas_col: Optional[str], 
        component_col: str, 
        percentage_col: str
    ) -> Optional[Dict[str, Any]]:
        """Parse a single component from a row"""
        try:
            # Get component name
            component_name = str(row[component_col]).strip()
            if pd.isna(row[component_col]) or component_name in ['', 'nan', 'None']:
                return None
            
            # Get percentage
            percentage_str = str(row[percentage_col]).strip()
            # Remove % sign if present
            percentage_str = percentage_str.replace('%', '').strip()
            percentage = float(percentage_str)
            
            if percentage <= 0:
                return None
            
            # Get CAS number if available
            cas_number = None
            if cas_col and not pd.isna(row[cas_col]):
                cas_number = self._clean_cas_number(str(row[cas_col]))
            
            # Determine component type
            component_type = 'IMPURITY' if percentage < self.IMPURITY_THRESHOLD else 'COMPONENT'
            
            return {
                'cas_number': cas_number,
                'component_name': component_name,
                'percentage': percentage,
                'component_type': component_type
            }
            
        except (ValueError, KeyError) as e:
            return None
    
    def _clean_cas_number(self, cas: str) -> Optional[str]:
        """Clean and validate CAS number"""
        # Remove whitespace
        cas = cas.strip()
        
        # CAS number pattern: XXX-XX-X or XXXX-XX-X, etc.
        pattern = r'^\d{2,7}-\d{2}-\d$'
        if re.match(pattern, cas):
            return cas
        
        # Try to extract CAS pattern from string
        match = re.search(r'(\d{2,7}-\d{2}-\d)', cas)
        if match:
            return match.group(1)
        
        return None
    
    @staticmethod
    def validate_csv_structure(file_path: str) -> Dict[str, Any]:
        """
        Validate CSV structure without full parsing
        
        Returns:
            Dictionary with validation results
        """
        try:
            df = pd.read_csv(file_path, nrows=5)
            columns = [col.lower().strip() for col in df.columns]
            
            has_component = any(
                col in columns 
                for col in ChromatographicCSVParser.COMPONENT_COLUMNS
            )
            has_percentage = any(
                col in columns 
                for col in ChromatographicCSVParser.PERCENTAGE_COLUMNS
            )
            
            return {
                'valid': has_component and has_percentage,
                'columns': list(df.columns),
                'row_count': len(df),
                'has_component_column': has_component,
                'has_percentage_column': has_percentage
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }








