
"""
PDF processing utilities for document ingestion.
Handles OCR results processing and text extraction.
"""

import logging
from typing import Dict, List, Any, Optional
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF processing and OCR results handler."""
    
    def __init__(self):
        self.confidence_threshold = 0.8
    
    def process_textract_results(self, textract_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process AWS Textract OCR results into structured format."""
        try:
            blocks = textract_results.get('blocks', [])
            document_metadata = textract_results.get('document_metadata', {})
            
            # Organize blocks by type
            pages = {}
            lines = {}
            words = {}
            
            for block in blocks:
                block_type = block.get('BlockType')
                block_id = block.get('Id')
                
                if block_type == 'PAGE':
                    pages[block_id] = block
                elif block_type == 'LINE':
                    lines[block_id] = block
                elif block_type == 'WORD':
                    words[block_id] = block
            
            # Process pages
            processed_pages = []
            overall_confidence = 0.0
            total_confidence_blocks = 0
            
            for page_id, page_block in pages.items():
                page_info = self._process_page(page_block, lines, words)
                processed_pages.append(page_info)
                
                # Calculate overall confidence
                if page_info['confidence'] > 0:
                    overall_confidence += page_info['confidence']
                    total_confidence_blocks += 1
            
            # Calculate average confidence
            if total_confidence_blocks > 0:
                overall_confidence = overall_confidence / total_confidence_blocks
            
            # Extract full document text
            full_text = self._extract_full_text(processed_pages)
            
            return {
                'document_id': textract_results.get('job_id', ''),
                'pages': processed_pages,
                'full_text': full_text,
                'confidence': round(overall_confidence, 3),
                'total_pages': len(processed_pages),
                'processing_timestamp': datetime.now(timezone.utc).isoformat(),
                'document_metadata': document_metadata,
                'extraction_stats': {
                    'total_blocks': len(blocks),
                    'page_blocks': len(pages),
                    'line_blocks': len(lines),
                    'word_blocks': len(words)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing Textract results: {e}")
            raise
    
    def _process_page(self, page_block: Dict, lines: Dict, words: Dict) -> Dict[str, Any]:
        """Process a single page from Textract results."""
        page_number = page_block.get('Page', 1)
        page_geometry = page_block.get('Geometry', {})
        
        # Get child line IDs
        child_ids = []
        for relationship in page_block.get('Relationships', []):
            if relationship.get('Type') == 'CHILD':
                child_ids.extend(relationship.get('Ids', []))
        
        # Process lines on this page
        page_lines = []
        page_confidence_sum = 0.0
        confidence_count = 0
        
        for line_id in child_ids:
            if line_id in lines:
                line_info = self._process_line(lines[line_id], words)
                page_lines.append(line_info)
                
                if line_info['confidence'] > 0:
                    page_confidence_sum += line_info['confidence']
                    confidence_count += 1
        
        # Calculate page confidence
        page_confidence = page_confidence_sum / confidence_count if confidence_count > 0 else 0.0
        
        # Extract page text
        page_text = '\n'.join([line['text'] for line in page_lines if line['text']])
        
        # Detect tables and images (basic detection)
        tables = self._detect_tables(page_lines)
        images = self._detect_images(page_block)
        
        return {
            'page_number': page_number,
            'text': page_text,
            'lines': page_lines,
            'confidence': round(page_confidence, 3),
            'geometry': page_geometry,
            'tables': tables,
            'images': images,
            'word_count': len(page_text.split()) if page_text else 0,
            'line_count': len(page_lines)
        }
    
    def _process_line(self, line_block: Dict, words: Dict) -> Dict[str, Any]:
        """Process a single line from Textract results."""
        line_text = line_block.get('Text', '')
        line_confidence = line_block.get('Confidence', 0.0)
        line_geometry = line_block.get('Geometry', {})
        
        # Get child word IDs
        word_ids = []
        for relationship in line_block.get('Relationships', []):
            if relationship.get('Type') == 'CHILD':
                word_ids.extend(relationship.get('Ids', []))
        
        # Process words in this line
        line_words = []
        for word_id in word_ids:
            if word_id in words:
                word_block = words[word_id]
                line_words.append({
                    'text': word_block.get('Text', ''),
                    'confidence': word_block.get('Confidence', 0.0),
                    'geometry': word_block.get('Geometry', {})
                })
        
        return {
            'text': line_text,
            'confidence': line_confidence,
            'geometry': line_geometry,
            'words': line_words,
            'word_count': len(line_words)
        }
    
    def _detect_tables(self, page_lines: List[Dict]) -> List[Dict]:
        """Basic table detection from line patterns."""
        tables = []
        
        # Look for patterns that might indicate tables
        # This is a simplified approach - in production, you might use Textract's table detection
        potential_table_lines = []
        
        for line in page_lines:
            text = line['text']
            # Look for lines with multiple columns (tabs, multiple spaces, or pipe separators)
            if re.search(r'\t|\s{3,}|\|', text) and len(text.split()) > 2:
                potential_table_lines.append(line)
        
        if len(potential_table_lines) >= 2:
            # Group consecutive table lines
            current_table = []
            for line in potential_table_lines:
                if not current_table or self._lines_are_consecutive(current_table[-1], line):
                    current_table.append(line)
                else:
                    if len(current_table) >= 2:
                        tables.append({
                            'type': 'detected_table',
                            'lines': current_table,
                            'row_count': len(current_table),
                            'confidence': sum(l['confidence'] for l in current_table) / len(current_table)
                        })
                    current_table = [line]
            
            # Add the last table if it exists
            if len(current_table) >= 2:
                tables.append({
                    'type': 'detected_table',
                    'lines': current_table,
                    'row_count': len(current_table),
                    'confidence': sum(l['confidence'] for l in current_table) / len(current_table)
                })
        
        return tables
    
    def _detect_images(self, page_block: Dict) -> List[Dict]:
        """Basic image detection from page geometry."""
        # This is a placeholder - in production, you might use additional image detection
        images = []
        
        # Look for large empty spaces that might contain images
        geometry = page_block.get('Geometry', {})
        if geometry:
            # This is a simplified approach
            images.append({
                'type': 'potential_image_area',
                'geometry': geometry,
                'confidence': 0.5  # Low confidence for basic detection
            })
        
        return images
    
    def _lines_are_consecutive(self, line1: Dict, line2: Dict) -> bool:
        """Check if two lines are vertically consecutive (basic heuristic)."""
        try:
            geom1 = line1.get('geometry', {}).get('BoundingBox', {})
            geom2 = line2.get('geometry', {}).get('BoundingBox', {})
            
            if not geom1 or not geom2:
                return False
            
            # Check if lines are close vertically
            y1_bottom = geom1.get('Top', 0) + geom1.get('Height', 0)
            y2_top = geom2.get('Top', 0)
            
            # Lines are consecutive if the gap is small
            gap = abs(y2_top - y1_bottom)
            return gap < 0.05  # 5% of page height
            
        except Exception:
            return False
    
    def _extract_full_text(self, processed_pages: List[Dict]) -> str:
        """Extract full document text from processed pages."""
        full_text_parts = []
        
        for page in processed_pages:
            page_text = page.get('text', '')
            if page_text:
                full_text_parts.append(f"--- Page {page['page_number']} ---")
                full_text_parts.append(page_text)
                full_text_parts.append("")  # Empty line between pages
        
        return '\n'.join(full_text_parts)
    
    def extract_text_with_pypdf2(self, pdf_content: bytes) -> Dict[str, Any]:
        """Fallback text extraction using PyPDF2 (for non-OCR cases)."""
        try:
            from PyPDF2 import PdfReader
            from io import BytesIO
            
            pdf_reader = PdfReader(BytesIO(pdf_content))
            pages = []
            full_text_parts = []
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    pages.append({
                        'page_number': page_num,
                        'text': page_text,
                        'confidence': 1.0,  # PyPDF2 doesn't provide confidence
                        'word_count': len(page_text.split()) if page_text else 0,
                        'extraction_method': 'pypdf2'
                    })
                    
                    if page_text:
                        full_text_parts.append(f"--- Page {page_num} ---")
                        full_text_parts.append(page_text)
                        full_text_parts.append("")
                        
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num}: {e}")
                    pages.append({
                        'page_number': page_num,
                        'text': '',
                        'confidence': 0.0,
                        'word_count': 0,
                        'extraction_method': 'pypdf2',
                        'error': str(e)
                    })
            
            return {
                'pages': pages,
                'full_text': '\n'.join(full_text_parts),
                'confidence': 1.0,
                'total_pages': len(pages),
                'extraction_method': 'pypdf2',
                'processing_timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {e}")
            raise
    
    def validate_extraction_quality(self, processed_content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality of text extraction."""
        validation_result = {
            'is_valid': True,
            'quality_score': 0.0,
            'issues': [],
            'recommendations': []
        }
        
        try:
            confidence = processed_content.get('confidence', 0.0)
            full_text = processed_content.get('full_text', '')
            pages = processed_content.get('pages', [])
            
            # Check overall confidence
            if confidence < self.confidence_threshold:
                validation_result['issues'].append(f"Low OCR confidence: {confidence:.2f}")
                validation_result['recommendations'].append("Consider manual review of extracted text")
            
            # Check text length
            if len(full_text) < 100:
                validation_result['issues'].append("Very short extracted text")
                validation_result['recommendations'].append("Verify document contains readable text")
            
            # Check for empty pages
            empty_pages = [p['page_number'] for p in pages if not p.get('text', '').strip()]
            if empty_pages:
                validation_result['issues'].append(f"Empty pages detected: {empty_pages}")
                validation_result['recommendations'].append("Review empty pages for images or complex layouts")
            
            # Calculate quality score
            quality_factors = [
                confidence,  # OCR confidence
                min(1.0, len(full_text) / 1000),  # Text length factor
                1.0 - (len(empty_pages) / len(pages)) if pages else 0.0  # Non-empty page ratio
            ]
            
            validation_result['quality_score'] = sum(quality_factors) / len(quality_factors)
            
            # Overall validation
            if validation_result['quality_score'] < 0.6:
                validation_result['is_valid'] = False
                validation_result['recommendations'].append("Consider re-processing with different OCR settings")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            validation_result['is_valid'] = False
            validation_result['issues'].append(f"Validation failed: {str(e)}")
            return validation_result
