
"""
Utility functions and helpers for the Agentic Compliance-Mapping System.
"""

import logging
import uuid
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
from functools import wraps
import time

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_document_id() -> str:
    """Generate a document ID with timestamp prefix."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"doc_{timestamp}_{unique_id}"


def generate_analysis_id() -> str:
    """Generate an analysis ID with timestamp prefix."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"analysis_{timestamp}_{unique_id}"


def generate_report_id() -> str:
    """Generate a report ID with timestamp prefix."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"report_{timestamp}_{unique_id}"


def calculate_file_hash(content: bytes) -> str:
    """Calculate SHA-256 hash of file content."""
    return hashlib.sha256(content).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    return filename


def validate_pdf_file(file_content: bytes) -> Dict[str, Any]:
    """Validate PDF file content and extract basic info."""
    validation_result = {
        'is_valid': False,
        'file_size': len(file_content),
        'error_message': None,
        'metadata': {}
    }
    
    try:
        # Check PDF header
        if not file_content.startswith(b'%PDF-'):
            validation_result['error_message'] = "Invalid PDF format"
            return validation_result
        
        # Check file size
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            validation_result['error_message'] = f"File too large (max {max_size // (1024*1024)}MB)"
            return validation_result
        
        # Basic PDF validation using PyPDF2
        try:
            from PyPDF2 import PdfReader
            from io import BytesIO
            
            pdf_reader = PdfReader(BytesIO(file_content))
            num_pages = len(pdf_reader.pages)
            
            if num_pages > 100:
                validation_result['error_message'] = "Too many pages (max 100)"
                return validation_result
            
            validation_result['metadata'] = {
                'num_pages': num_pages,
                'title': pdf_reader.metadata.get('/Title', '') if pdf_reader.metadata else '',
                'author': pdf_reader.metadata.get('/Author', '') if pdf_reader.metadata else '',
                'creator': pdf_reader.metadata.get('/Creator', '') if pdf_reader.metadata else ''
            }
            
        except Exception as e:
            validation_result['error_message'] = f"PDF parsing error: {str(e)}"
            return validation_result
        
        validation_result['is_valid'] = True
        return validation_result
        
    except Exception as e:
        validation_result['error_message'] = f"Validation error: {str(e)}"
        return validation_result


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 50) -> List[Dict]:
    """Split text into overlapping chunks for processing."""
    if not text or chunk_size <= 0:
        return []
    
    chunks = []
    words = text.split()
    
    if len(words) <= chunk_size:
        return [{
            'chunk_index': 0,
            'text': text,
            'start_word': 0,
            'end_word': len(words),
            'word_count': len(words)
        }]
    
    start = 0
    chunk_index = 0
    
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        
        chunks.append({
            'chunk_index': chunk_index,
            'text': chunk_text,
            'start_word': start,
            'end_word': end,
            'word_count': len(chunk_words)
        })
        
        # Move start position with overlap
        start = end - overlap if end < len(words) else end
        chunk_index += 1
        
        # Prevent infinite loop
        if start >= len(words):
            break
    
    return chunks


def extract_regulation_references(text: str) -> List[Dict]:
    """Extract regulation references from text using regex patterns."""
    patterns = {
        'act_reference': r'([A-Z][a-zA-Z\s]+Act\s+\d{4})',
        'section_reference': r'(Section\s+\d+[A-Za-z]?(?:\(\d+\))?)',
        'regulation_reference': r'(Regulation\s+\d+[A-Za-z]?(?:\(\d+\))?)',
        'code_reference': r'([A-Z][a-zA-Z\s]+Code\s+\d{4})',
        'standard_reference': r'(AS\s+\d+(?:\.\d+)?(?::\d{4})?|ISO\s+\d+(?::\d{4})?)'
    }
    
    references = []
    
    for ref_type, pattern in patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            references.append({
                'type': ref_type,
                'text': match.group(1),
                'start_pos': match.start(),
                'end_pos': match.end(),
                'context': text[max(0, match.start()-50):match.end()+50]
            })
    
    return references


def calculate_text_complexity(text: str) -> Dict[str, float]:
    """Calculate text complexity metrics."""
    if not text:
        return {'complexity_score': 0.0, 'readability_score': 0.0}
    
    # Basic metrics
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    words = text.split()
    
    if not sentences or not words:
        return {'complexity_score': 0.0, 'readability_score': 0.0}
    
    # Calculate metrics
    avg_sentence_length = len(words) / len(sentences)
    avg_word_length = sum(len(word) for word in words) / len(words)
    
    # Simple complexity score (0-1)
    complexity_score = min(1.0, (avg_sentence_length / 20 + avg_word_length / 10) / 2)
    
    # Simple readability score (inverse of complexity)
    readability_score = 1.0 - complexity_score
    
    return {
        'complexity_score': round(complexity_score, 3),
        'readability_score': round(readability_score, 3),
        'avg_sentence_length': round(avg_sentence_length, 1),
        'avg_word_length': round(avg_word_length, 1),
        'sentence_count': len(sentences),
        'word_count': len(words)
    }


def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 1.0):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}")
                        raise
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"Function {func.__name__} failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator


def timing_decorator(func):
    """Decorator to measure function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.2f} seconds: {e}")
            raise
    return wrapper


def format_compliance_score(score: float) -> str:
    """Format compliance score as percentage with color coding."""
    percentage = score * 100
    if percentage >= 90:
        return f"🟢 {percentage:.1f}%"
    elif percentage >= 75:
        return f"🟡 {percentage:.1f}%"
    elif percentage >= 50:
        return f"🟠 {percentage:.1f}%"
    else:
        return f"🔴 {percentage:.1f}%"


def format_risk_level(risk_level: str) -> str:
    """Format risk level with appropriate emoji."""
    risk_emojis = {
        'critical': '🔴',
        'high': '🟠',
        'medium': '🟡',
        'low': '🟢',
        'minimal': '⚪'
    }
    return f"{risk_emojis.get(risk_level.lower(), '⚪')} {risk_level.title()}"


def create_api_response(success: bool = True, data: Any = None, 
                       message: str = "", error: Optional[Dict] = None,
                       request_id: Optional[str] = None) -> Dict:
    """Create standardized API response."""
    response = {
        'success': success,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'request_id': request_id or generate_uuid()
    }
    
    if success:
        response['data'] = data
        response['message'] = message or "Operation completed successfully"
    else:
        response['error'] = error or {'code': 'UNKNOWN_ERROR', 'message': message}
        response['data'] = None
    
    return response


def validate_document_type(document_type: str) -> bool:
    """Validate document type."""
    valid_types = ['vendor_contract', 'regulation', 'terms_conditions']
    return document_type in valid_types


def validate_jurisdiction(jurisdiction: str) -> bool:
    """Validate Australian jurisdiction."""
    valid_jurisdictions = ['federal', 'nsw', 'qld', 'wa', 'sa', 'vic', 'tas', 'nt', 'act']
    return jurisdiction.lower() in valid_jurisdictions


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep punctuation
    text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\"\'\/]', '', text)
    
    # Normalize quotes
    text = re.sub(r'["""]', '"', text)
    text = re.sub(r'[''']', "'", text)
    
    return text.strip()


def extract_key_phrases(text: str, max_phrases: int = 10) -> List[str]:
    """Extract key phrases from text using simple heuristics."""
    if not text:
        return []
    
    # Common compliance-related keywords
    compliance_keywords = [
        'safety', 'environmental', 'regulation', 'compliance', 'requirement',
        'obligation', 'standard', 'procedure', 'management', 'system',
        'audit', 'inspection', 'monitoring', 'reporting', 'documentation',
        'training', 'competency', 'risk', 'hazard', 'incident', 'emergency'
    ]
    
    # Find sentences containing compliance keywords
    sentences = re.split(r'[.!?]+', text)
    key_phrases = []
    
    for sentence in sentences:
        sentence = sentence.strip().lower()
        if any(keyword in sentence for keyword in compliance_keywords):
            # Extract noun phrases (simplified)
            words = sentence.split()
            if 5 <= len(words) <= 15:  # Reasonable phrase length
                key_phrases.append(sentence.capitalize())
    
    # Remove duplicates and limit results
    unique_phrases = list(dict.fromkeys(key_phrases))
    return unique_phrases[:max_phrases]


class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self, total_steps: int, operation_name: str = "Operation"):
        self.total_steps = total_steps
        self.current_step = 0
        self.operation_name = operation_name
        self.start_time = time.time()
        self.step_times = []
    
    def update(self, step_name: str = "", increment: int = 1):
        """Update progress."""
        self.current_step += increment
        current_time = time.time()
        self.step_times.append(current_time)
        
        progress_percentage = (self.current_step / self.total_steps) * 100
        elapsed_time = current_time - self.start_time
        
        if self.current_step > 0:
            avg_time_per_step = elapsed_time / self.current_step
            estimated_total_time = avg_time_per_step * self.total_steps
            remaining_time = estimated_total_time - elapsed_time
        else:
            remaining_time = 0
        
        logger.info(
            f"{self.operation_name}: {progress_percentage:.1f}% "
            f"({self.current_step}/{self.total_steps}) - "
            f"{step_name} - ETA: {remaining_time:.0f}s"
        )
    
    def complete(self):
        """Mark operation as complete."""
        total_time = time.time() - self.start_time
        logger.info(f"{self.operation_name} completed in {total_time:.2f} seconds")
