#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parser para importar composites desde Excel/CSV en formato SAP
Soporta el formato de archivo Composite.xlsx con columnas:
- Espec./compon. (CAS)
- Nombre del producto
- Cl.Componente (COMPONENT para componentes principales)
- Valor Lím.inf. y Valor Lím.sup. (rangos de porcentaje)
- Unidad (%)
"""

import pandas as pd
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class CompositeExcelParser:
    """Parser para archivos Excel/CSV de composites en formato SAP"""
    
    def __init__(self):
        self.supported_extensions = ['.xlsx', '.xls', '.csv']
    
    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """
        Parsea un archivo Excel/CSV y extrae los componentes del composite
        
        Args:
            file_path: Ruta al archivo Excel/CSV
            
        Returns:
            Dict con:
                - success: bool
                - components: List[Dict] con component_name, cas_number, percentage_min, percentage_max
                - errors: List[str]
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return {
                "success": False,
                "components": [],
                "errors": [f"Archivo no encontrado: {file_path}"]
            }
        
        file_ext = file_path_obj.suffix.lower()
        
        if file_ext not in self.supported_extensions:
            return {
                "success": False,
                "components": [],
                "errors": [f"Formato no soportado: {file_ext}. Soporta: {', '.join(self.supported_extensions)}"]
            }
        
        try:
            # Leer archivo
            if file_ext == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
            
            logger.info(f"Archivo leído: {len(df)} filas, {len(df.columns)} columnas")
            logger.debug(f"Columnas encontradas: {list(df.columns)}")
            
            # Normalizar nombres de columnas (eliminar espacios, convertir a minúsculas)
            df.columns = df.columns.str.strip()
            
            # Buscar componentes principales (Cl.Componente == 'COMPONENT')
            component_col = None
            for col in df.columns:
                if 'componente' in col.lower() or 'component' in col.lower():
                    component_col = col
                    break
            
            if component_col is None:
                return {
                    "success": False,
                    "components": [],
                    "errors": ["No se encontró columna 'Cl.Componente' o similar"]
                }
            
            # Filtrar solo componentes principales
            components_df = df[df[component_col] == 'COMPONENT'].copy()
            
            if components_df.empty:
                return {
                    "success": False,
                    "components": [],
                    "errors": ["No se encontraron componentes con Cl.Componente = 'COMPONENT'"]
                }
            
            logger.info(f"Encontrados {len(components_df)} componentes principales")
            
            # Buscar columnas necesarias
            cas_col = None
            name_col = None
            min_col = None
            max_col = None
            unit_col = None
            
            for col in df.columns:
                col_lower = col.lower()
                if cas_col is None and ('cas' in col_lower or 'espec' in col_lower):
                    cas_col = col
                if name_col is None and ('nombre' in col_lower or 'producto' in col_lower):
                    name_col = col
                if min_col is None and ('lím.inf' in col_lower or 'lim.inf' in col_lower or 'min' in col_lower):
                    min_col = col
                if max_col is None and ('lím.sup' in col_lower or 'lim.sup' in col_lower or 'max' in col_lower):
                    max_col = col
                if unit_col is None and 'unidad' in col_lower:
                    unit_col = col
            
            if not name_col:
                return {
                    "success": False,
                    "components": [],
                    "errors": ["No se encontró columna 'Nombre del producto' o similar"]
                }
            
            components = []
            errors = []
            
            for idx, row in components_df.iterrows():
                try:
                    # Extraer datos
                    component_name = str(row[name_col]).strip() if pd.notna(row[name_col]) else None
                    cas_number = str(row[cas_col]).strip() if cas_col and pd.notna(row[cas_col]) else None
                    
                    # Limpiar CAS (puede tener formato "123-45-6" o "123456")
                    if cas_number:
                        cas_number = cas_number.replace(' ', '').replace('-', '')
                        if len(cas_number) >= 5:
                            # Formatear CAS como "123-45-6"
                            cas_number = f"{cas_number[:3]}-{cas_number[3:5]}-{cas_number[5:]}"
                    
                    # Extraer porcentajes
                    percentage_min = 0.0
                    percentage_max = 0.0
                    
                    if min_col and pd.notna(row[min_col]):
                        try:
                            percentage_min = float(row[min_col])
                        except (ValueError, TypeError):
                            percentage_min = 0.0
                    
                    if max_col and pd.notna(row[max_col]):
                        try:
                            percentage_max = float(row[max_col])
                        except (ValueError, TypeError):
                            percentage_max = 0.0
                    
                    # Si no hay porcentaje máximo pero sí mínimo, usar mínimo como valor único
                    if percentage_max == 0.0 and percentage_min > 0.0:
                        percentage_max = percentage_min
                    
                    # Calcular porcentaje promedio si hay rango
                    percentage = percentage_max if percentage_max > 0 else percentage_min
                    if percentage_min > 0 and percentage_max > percentage_min:
                        percentage = (percentage_min + percentage_max) / 2
                    
                    # Validar que tenga nombre
                    if not component_name or component_name.lower() in ['nan', 'none', '']:
                        errors.append(f"Fila {idx + 1}: Componente sin nombre")
                        continue
                    
                    # Saltar si el nombre parece ser el producto principal (tiene "oil" o similar)
                    if component_name.lower().endswith('oil') and percentage_max >= 90:
                        logger.debug(f"Saltando producto principal: {component_name}")
                        continue
                    
                    components.append({
                        "component_name": component_name,
                        "cas_number": cas_number if cas_number and cas_number != 'nan' else None,
                        "percentage": percentage,
                        "percentage_min": percentage_min,
                        "percentage_max": percentage_max,
                        "component_type": "COMPONENT"
                    })
                    
                except Exception as e:
                    errors.append(f"Fila {idx + 1}: Error procesando componente - {str(e)}")
                    logger.warning(f"Error procesando fila {idx + 1}: {e}")
            
            if not components:
                return {
                    "success": False,
                    "components": [],
                    "errors": errors + ["No se pudieron extraer componentes válidos"]
                }
            
            # Normalizar porcentajes para que sumen aproximadamente 100%
            total_percentage = sum(c['percentage'] for c in components)
            if total_percentage > 0:
                normalization_factor = 100.0 / total_percentage
                for comp in components:
                    comp['percentage'] = round(comp['percentage'] * normalization_factor, 2)
            
            logger.info(f"Extraídos {len(components)} componentes del archivo")
            
            return {
                "success": True,
                "components": components,
                "errors": errors,
                "total_percentage": sum(c['percentage'] for c in components)
            }
            
        except Exception as e:
            logger.error(f"Error parseando archivo {file_path}: {e}", exc_info=True)
            return {
                "success": False,
                "components": [],
                "errors": [f"Error parseando archivo: {str(e)}"]
            }

