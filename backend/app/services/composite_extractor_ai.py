"""
Composite Extractor AI

AI-based service for extracting chemical composition data from PDF documents.
Uses OCR, pattern recognition, and text analysis to identify components, CAS numbers, and percentages.
"""

import logging
import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class CompositeExtractorAI:
    """
    Extracts chemical composition data from PDF documents.
    Handles both text-based PDFs and scanned/image PDFs.
    """
    
    # Regex patterns for detection
    CAS_PATTERN = r'\b\d{1,7}-\d{2}-\d\b'  # CAS number format: XXXXXXX-XX-X
    PERCENTAGE_PATTERN = r'(\d+\.?\d*)\s*%'  # Percentage: XX.X%
    PERCENTAGE_RANGE_PATTERN = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*%'  # Range: XX-YY%
    
    # Common composition table keywords
    TABLE_KEYWORDS = [
        'composition',
        'component',
        'ingredient',
        'constituents',
        'cas',
        'cas number',
        'cas no',
        'percentage',
        '%',
        'concentration'
    ]
    
    def __init__(self):
        self.confidence_threshold = 50  # Minimum confidence for OCR results
    
    def extract_from_pdfs(self, pdf_paths: List[str]) -> Tuple[List[Dict[str, Any]], float]:
        """
        Extract composition data from multiple PDF files.
        
        Args:
            pdf_paths: List of paths to PDF files
            
        Returns:
            Tuple of (components list, overall confidence score 0-100)
        """
        all_components = []
        confidence_scores = []
        
        for pdf_path in pdf_paths:
            try:
                components, confidence = self._extract_from_single_pdf(pdf_path)
                all_components.extend(components)
                confidence_scores.append(confidence)
                
                logger.info(
                    f"Extracted {len(components)} components from {Path(pdf_path).name} "
                    f"with confidence {confidence:.1f}%"
                )
            except Exception as e:
                logger.error(f"Error extracting from {pdf_path}: {e}")
                confidence_scores.append(0)
        
        # Deduplicate and merge components
        merged_components = self._merge_components(all_components)
        
        # Calculate overall confidence
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Validate that percentages sum to approximately 100
        total_percentage = sum(c['percentage'] for c in merged_components)
        if not (95 <= total_percentage <= 105):
            logger.warning(
                f"Total percentage is {total_percentage}%, expected ~100%. "
                f"Adjusting confidence score."
            )
            overall_confidence *= 0.7
        
        return merged_components, overall_confidence
    
    def _extract_from_single_pdf(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], float]:
        """Extract composition from a single PDF file"""
        # Try text-based extraction first (faster)
        text = self._extract_text_from_pdf(pdf_path)
        
        if text and len(text.strip()) > 100:
            # Text-based PDF
            components, confidence = self._parse_text_for_composition(text)
            if components:
                return components, confidence
        
        # Fall back to OCR for scanned PDFs
        logger.info(f"Text extraction insufficient, using OCR for {pdf_path}")
        text = self._extract_text_with_ocr(pdf_path)
        components, confidence = self._parse_text_for_composition(text)
        
        # Lower confidence for OCR results
        return components, confidence * 0.85
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""
    
    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            text = ""
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)
                
                # Run OCR
                page_text = pytesseract.image_to_string(
                    processed_image,
                    config='--psm 6'  # Assume uniform block of text
                )
                text += page_text + "\n\n"
                
                logger.debug(f"OCR extracted {len(page_text)} chars from page {i+1}")
            
            return text
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return ""
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert PIL Image to OpenCV format
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)
        
        # Convert back to PIL Image
        return Image.fromarray(denoised)
    
    def _parse_text_for_composition(self, text: str) -> Tuple[List[Dict[str, Any]], float]:
        """
        Parse extracted text to find composition data.
        
        Returns:
            Tuple of (components list, confidence score 0-100)
        """
        components = []
        
        # Look for table-like structures
        lines = text.split('\n')
        
        # Find potential composition table
        table_start_idx = None
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in self.TABLE_KEYWORDS):
                table_start_idx = i
                break
        
        if table_start_idx is None:
            logger.warning("No composition table found in document")
            return [], 0
        
        # Extract components from lines after table start
        confidence_scores = []
        for i in range(table_start_idx, min(table_start_idx + 50, len(lines))):
            line = lines[i]
            
            # Try to extract component from line
            component = self._extract_component_from_line(line)
            if component:
                components.append(component)
                confidence_scores.append(component.get('confidence', 70))
        
        # Calculate confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Validate components
        valid_components = self._validate_components(components)
        
        return valid_components, avg_confidence
    
    def _extract_component_from_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Extract a component (name, CAS, percentage) from a text line.
        
        Expected formats:
        - "Linalool 78-70-6 35.5%"
        - "Linalool | 78-70-6 | 35.5"
        - "35.5% Linalool (CAS: 78-70-6)"
        """
        # Find CAS number
        cas_match = re.search(self.CAS_PATTERN, line)
        if not cas_match:
            return None
        
        cas_number = cas_match.group(0)
        
        # Find percentage
        percentage = None
        perc_match = re.search(self.PERCENTAGE_PATTERN, line)
        if perc_match:
            percentage = float(perc_match.group(1))
        else:
            # Try range pattern and take midpoint
            range_match = re.search(self.PERCENTAGE_RANGE_PATTERN, line)
            if range_match:
                min_perc = float(range_match.group(1))
                max_perc = float(range_match.group(2))
                percentage = (min_perc + max_perc) / 2
        
        if percentage is None:
            # Try to find standalone number near CAS
            numbers = re.findall(r'\b(\d+\.?\d*)\b', line)
            for num in numbers:
                try:
                    val = float(num)
                    if 0 < val <= 100:
                        percentage = val
                        break
                except ValueError:
                    continue
        
        if percentage is None:
            logger.debug(f"No percentage found in line: {line}")
            return None
        
        # Extract component name (text before or after CAS, excluding percentage)
        # Remove CAS and percentage from line
        name_text = line
        name_text = re.sub(self.CAS_PATTERN, '', name_text)
        name_text = re.sub(self.PERCENTAGE_PATTERN, '', name_text)
        name_text = re.sub(self.PERCENTAGE_RANGE_PATTERN, '', name_text)
        
        # Clean up name
        name = name_text.strip()
        name = re.sub(r'[|:\-_\t]+', ' ', name)  # Replace separators with space
        name = re.sub(r'\s+', ' ', name)  # Normalize whitespace
        name = name.strip()
        
        if not name or len(name) < 3:
            logger.debug(f"Invalid component name extracted: '{name}'")
            return None
        
        # Confidence based on how complete the data is
        confidence = 80
        if percentage < 0.1 or percentage > 100:
            confidence = 40
        if not self._validate_cas_format(cas_number):
            confidence = 50
        
        return {
            'component_name': name,
            'cas_number': cas_number,
            'percentage': percentage,
            'confidence': confidence,
            'source_line': line.strip()
        }
    
    def _validate_cas_format(self, cas: str) -> bool:
        """Validate CAS number format"""
        return bool(re.match(r'^\d{1,7}-\d{2}-\d$', cas))
    
    def _validate_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and clean extracted components.
        Remove duplicates, validate ranges, etc.
        """
        # Remove duplicates based on CAS number
        seen_cas = set()
        unique_components = []
        
        for comp in components:
            cas = comp['cas_number']
            if cas not in seen_cas:
                seen_cas.add(cas)
                unique_components.append(comp)
            else:
                # Duplicate found, keep the one with higher confidence
                existing = next(c for c in unique_components if c['cas_number'] == cas)
                if comp['confidence'] > existing['confidence']:
                    unique_components.remove(existing)
                    unique_components.append(comp)
        
        # Sort by percentage descending
        unique_components.sort(key=lambda x: x['percentage'], reverse=True)
        
        return unique_components
    
    def _merge_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge components from multiple sources.
        Average percentages for duplicates.
        """
        merged = {}
        
        for comp in components:
            cas = comp['cas_number']
            
            if cas not in merged:
                merged[cas] = comp.copy()
                merged[cas]['count'] = 1
            else:
                # Average the percentage
                existing = merged[cas]
                existing['percentage'] = (
                    existing['percentage'] * existing['count'] + comp['percentage']
                ) / (existing['count'] + 1)
                existing['count'] += 1
                
                # Update confidence (higher is better)
                existing['confidence'] = max(existing['confidence'], comp['confidence'])
        
        # Remove count field
        result = []
        for comp in merged.values():
            comp.pop('count', None)
            result.append(comp)
        
        return result



