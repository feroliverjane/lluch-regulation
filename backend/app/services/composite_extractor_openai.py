"""
Composite Extractor using OpenAI Vision API

Uses GPT-4 Vision to extract chemical composition data from PDF documents.
Much more accurate than OCR-based extraction, especially for complex layouts.
"""

import logging
import base64
import json
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF
from pdf2image import convert_from_path

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI library not installed. Install with: pip install openai")

logger = logging.getLogger(__name__)


class CompositeExtractorOpenAI:
    """
    Extracts chemical composition data from PDF documents using OpenAI Vision API.
    Converts PDFs to images and uses GPT-4 Vision to understand structure and extract data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI extractor.
        
        Args:
            api_key: OpenAI API key. If None, will try to get from environment.
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install openai"
            )
        
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.model = "gpt-4o"  # GPT-4 Vision model (gpt-4o has vision capabilities)
        
    def extract_from_pdfs(
        self, 
        pdf_paths: List[str],
        use_vision: bool = True
    ) -> Tuple[List[Dict[str, Any]], float]:
        """
        Extract composition data from multiple PDF files using OpenAI.
        
        Args:
            pdf_paths: List of paths to PDF files
            use_vision: If True, use Vision API. If False, extract text first and use GPT-4.
            
        Returns:
            Tuple of (components list, overall confidence score 0-100)
        """
        all_components = []
        confidence_scores = []
        
        for pdf_path in pdf_paths:
            try:
                if use_vision:
                    components, confidence = self._extract_with_vision(pdf_path)
                else:
                    components, confidence = self._extract_with_text(pdf_path)
                
                all_components.extend(components)
                confidence_scores.append(confidence)
                
                logger.info(
                    f"Extracted {len(components)} components from {Path(pdf_path).name} "
                    f"with confidence {confidence:.1f}%"
                )
            except Exception as e:
                logger.error(f"Error extracting from {pdf_path}: {e}", exc_info=True)
                confidence_scores.append(0)
        
        # Deduplicate and merge components
        merged_components = self._merge_components(all_components)
        
        # Calculate overall confidence
        overall_confidence = (
            sum(confidence_scores) / len(confidence_scores) 
            if confidence_scores else 0
        )
        
        # Validate that percentages sum to approximately 100
        total_percentage = sum(c['percentage'] for c in merged_components)
        if not (95 <= total_percentage <= 105):
            logger.warning(
                f"Total percentage is {total_percentage}%, expected ~100%. "
                f"Adjusting confidence score."
            )
            overall_confidence *= 0.85
        
        return merged_components, overall_confidence
    
    def _extract_with_vision(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], float]:
        """
        Extract using OpenAI Vision API (GPT-4 Vision).
        First tries to extract text directly, then converts to images if needed.
        """
        # First try: Extract text directly (faster, no poppler needed)
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            
            # If we got good text, use text-based extraction
            if text and len(text.strip()) > 200:
                logger.info("Using text-based extraction (faster)")
                return self._extract_with_text(pdf_path)
        except Exception as e:
            logger.warning(f"Could not extract text directly: {e}")
        
        # Second try: Convert PDF to images (requires poppler)
        try:
            images = convert_from_path(pdf_path, dpi=300, fmt='PNG')
        except Exception as e:
            logger.error(f"Error converting PDF to images: {e}")
            logger.info("Falling back to text extraction")
            # Fallback: try to extract text first
            return self._extract_with_text(pdf_path)
        
        if not images:
            raise ValueError(f"No pages found in PDF: {pdf_path}")
        
        # Process first few pages (usually composition is at the beginning)
        pages_to_process = min(3, len(images))
        all_components = []
        
        for i, image in enumerate(images[:pages_to_process]):
            try:
                # Convert PIL Image to base64
                import io
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Call OpenAI Vision API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an expert chemist specializing in extracting chemical composition data from technical documents.

Your task is to extract chemical components with their CAS numbers and percentages from ANY format:
- Composition tables
- IFRA certificates
- Safety data sheets
- Technical specifications
- Any document mentioning chemical components

Return ONLY a valid JSON array with this exact structure:
[
    {
        "component_name": "Full chemical name",
        "cas_number": "CAS number in format XXXXXXX-XX-X or N/A",
        "percentage": decimal_number
    }
]

Rules:
- Extract ALL components you find, even if percentages are small or in ranges
- CAS numbers must be in format: XXXXXXX-XX-X (digits separated by hyphens)
- Percentages should be decimal numbers (e.g., 35.5, not "35.5%")
- If percentage is a range (e.g., "10-20%"), use the midpoint (15.0)
- If percentage is "max X%", use that value
- If no percentage is given but component is listed, use 0.1% as default
- If a component appears multiple times, include it only once with the most reliable percentage
- For IFRA certificates: extract components mentioned in "MATIÈRES PREMIÈRES" or raw materials sections
- Be very precise with percentages - these are critical for regulatory compliance
- If document doesn't contain composition data, return empty array []"""
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Analyze this document and extract ALL chemical composition data.

Look for:
1. Component names (chemical names, raw materials, ingredients)
2. CAS numbers (format: XXXXXXX-XX-X)
3. Percentages, concentrations, or maximum levels

Document types might include:
- Composition tables
- IFRA certificates (look for "MATIÈRES PREMIÈRES" or raw materials)
- Safety data sheets
- Technical specifications

If you find any chemical components mentioned, extract them even if percentages are ranges or maximum values.
If no composition data is found, return empty array [].

Return ONLY the JSON array, no other text."""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000,
                    temperature=0.1  # Low temperature for precision
                )
                
                # Parse response
                content = response.choices[0].message.content.strip()
                
                # Extract JSON from response (might have markdown code blocks)
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Parse JSON
                try:
                    page_components = json.loads(content)
                    if isinstance(page_components, list):
                        all_components.extend(page_components)
                    else:
                        logger.warning(f"Expected list, got {type(page_components)}")
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON from OpenAI response: {e}")
                    logger.debug(f"Response content: {content}")
                    # Try to extract with text fallback
                    return self._extract_with_text(pdf_path)
                
            except Exception as e:
                logger.error(f"Error processing page {i+1}: {e}")
                continue
        
        # Calculate confidence (higher for more components found)
        confidence = min(95, 70 + len(all_components) * 2)
        
        return all_components, confidence
    
    def _extract_with_text(self, pdf_path: str) -> Tuple[List[Dict[str, Any]], float]:
        """
        Extract using text extraction + GPT-4 (fallback method).
        First extracts text from PDF, then uses GPT-4 to parse it.
        """
        # Extract text from PDF
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return [], 0
        
        if not text or len(text.strip()) < 50:
            logger.warning("Insufficient text extracted from PDF")
            return [], 0
        
        # Use GPT-4 to extract composition from text
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Can also use gpt-4-turbo
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert chemist. Extract chemical composition data from ANY document format.

Look for chemical components in:
- Composition tables
- IFRA certificates (especially "MATIÈRES PREMIÈRES" section)
- Safety data sheets
- Technical specifications
- Any section mentioning raw materials or ingredients

Return ONLY a valid JSON object with this structure:
{
    "components": [
    {
        "component_name": "Full chemical name",
        "cas_number": "CAS number in format XXXXXXX-XX-X or N/A",
        "percentage": decimal_number
    }
]
}

Rules:
- Extract ALL components found, even if percentages are ranges or maximum values
- If percentage is a range, use midpoint
- If no percentage given, use 0.1% as default
- For IFRA certs: focus on raw materials sections
- If no composition data found, return {"components": []}"""
                    },
                    {
                        "role": "user",
                        "content": f"""Extract chemical composition data from this text:

{text[:4000]}  # Limit to first 4000 chars to avoid token limits

Return ONLY the JSON array."""
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"Raw OpenAI response: {content[:200]}...")
            
            # Extract JSON from response (might have markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            result = json.loads(content)
            logger.debug(f"Parsed result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
            
            # Handle different response formats
            if isinstance(result, dict):
                # If response_format was json_object, look for components key
                if "components" in result:
                components = result["components"]
                    logger.info(f"Found {len(components)} components in 'components' key")
                elif "data" in result:
                    components = result["data"]
                    logger.info(f"Found {len(components)} components in 'data' key")
                else:
                    # Try to extract any list values
                    list_values = [v for v in result.values() if isinstance(v, list)]
                    components = list_values[0] if list_values else []
                    if components:
                        logger.info(f"Found {len(components)} components in dict values")
                    else:
                        logger.warning(f"No components found in response. Keys: {list(result.keys())}")
                        logger.debug(f"Full response: {result}")
            elif isinstance(result, list):
                components = result
                logger.info(f"Response is a list with {len(components)} components")
            else:
                logger.warning(f"Unexpected response format: {type(result)}")
                logger.debug(f"Response content: {content[:500]}")
                components = []
            
            confidence = min(90, 60 + len(components) * 3)
            
            return components, confidence
            
        except Exception as e:
            logger.error(f"Error in GPT-4 text extraction: {e}")
            return [], 0
    
    def _merge_components(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Merge components from multiple sources, averaging percentages for duplicates.
        """
        merged = {}
        
        for comp in components:
            # Use CAS number as key if available, otherwise component name
            key = comp.get('cas_number') or comp.get('component_name', '').lower()
            
            if not key or key == 'N/A':
                # Skip components without identifiers
                continue
            
            if key not in merged:
                merged[key] = comp.copy()
                merged[key]['count'] = 1
            else:
                # Average the percentage
                existing = merged[key]
                existing['percentage'] = (
                    existing['percentage'] * existing['count'] + comp.get('percentage', 0)
                ) / (existing['count'] + 1)
                existing['count'] += 1
                
                # Use the most complete component name
                if len(comp.get('component_name', '')) > len(existing.get('component_name', '')):
                    existing['component_name'] = comp.get('component_name', '')
        
        # Remove count field and return list
        result = []
        for comp in merged.values():
            comp.pop('count', None)
            result.append(comp)
        
        # Sort by percentage descending
        result.sort(key=lambda x: x.get('percentage', 0), reverse=True)
        
        return result

