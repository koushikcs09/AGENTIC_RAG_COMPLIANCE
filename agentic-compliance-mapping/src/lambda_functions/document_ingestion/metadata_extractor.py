
"""
Metadata extraction utilities for document ingestion.
Extracts document properties, structure, and key information.
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from collections import Counter

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata and document properties from processed content."""
    
    def __init__(self):
        self.date_patterns = [
            r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b',  # DD/MM/YYYY or MM/DD/YYYY
            r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b',  # DD Month YYYY
            r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b',  # Month DD, YYYY
            r'\b(\d{2,4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b'   # YYYY/MM/DD
        ]
        
        self.contract_indicators = [
            'agreement', 'contract', 'terms and conditions', 'service agreement',
            'supply agreement', 'contractor', 'vendor', 'supplier', 'client'
        ]
        
        self.regulation_indicators = [
            'act', 'regulation', 'code', 'standard', 'law', 'statute',
            'ordinance', 'rule', 'directive', 'policy'
        ]
        
        self.mining_keywords = [
            'mining', 'mine', 'mineral', 'extraction', 'excavation', 'quarry',
            'ore', 'coal', 'gold', 'iron', 'copper', 'bauxite', 'exploration',
            'drilling', 'blasting', 'processing', 'refining', 'smelting'
        ]
        
        self.safety_keywords = [
            'safety', 'health', 'hazard', 'risk', 'accident', 'incident',
            'injury', 'fatality', 'emergency', 'evacuation', 'ppe',
            'personal protective equipment', 'safety management system'
        ]
        
        self.environmental_keywords = [
            'environmental', 'environment', 'pollution', 'contamination',
            'rehabilitation', 'restoration', 'water', 'air', 'soil',
            'waste', 'emissions', 'discharge', 'impact assessment'
        ]
    
    def extract_from_content(self, processed_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract comprehensive metadata from processed document content."""
        try:
            full_text = processed_content.get('full_text', '')
            pages = processed_content.get('pages', [])
            
            metadata = {
                'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
                'document_structure': self._analyze_document_structure(pages),
                'content_analysis': self._analyze_content(full_text),
                'key_entities': self._extract_key_entities(full_text),
                'dates': self._extract_dates(full_text),
                'document_classification': self._classify_document(full_text),
                'compliance_indicators': self._identify_compliance_areas(full_text),
                'quality_metrics': self._calculate_quality_metrics(processed_content),
                'language_analysis': self._analyze_language(full_text)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}")
            return {
                'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e),
                'extraction_status': 'failed'
            }
    
    def _analyze_document_structure(self, pages: List[Dict]) -> Dict[str, Any]:
        """Analyze document structure and layout."""
        structure = {
            'total_pages': len(pages),
            'page_analysis': [],
            'has_tables': False,
            'has_images': False,
            'section_count': 0,
            'average_words_per_page': 0
        }
        
        total_words = 0
        section_patterns = [
            r'^\s*\d+\.\s+',  # 1. Section
            r'^\s*\d+\.\d+\s+',  # 1.1 Subsection
            r'^\s*[A-Z][A-Z\s]+$',  # ALL CAPS HEADERS
            r'^\s*SECTION\s+\d+',  # SECTION 1
            r'^\s*PART\s+[IVX]+',  # PART I, II, III
        ]
        
        for page in pages:
            page_info = {
                'page_number': page.get('page_number', 0),
                'word_count': page.get('word_count', 0),
                'line_count': page.get('line_count', 0),
                'has_tables': len(page.get('tables', [])) > 0,
                'has_images': len(page.get('images', [])) > 0,
                'confidence': page.get('confidence', 0.0)
            }
            
            structure['page_analysis'].append(page_info)
            total_words += page_info['word_count']
            
            if page_info['has_tables']:
                structure['has_tables'] = True
            if page_info['has_images']:
                structure['has_images'] = True
            
            # Count sections in page text
            page_text = page.get('text', '')
            for pattern in section_patterns:
                structure['section_count'] += len(re.findall(pattern, page_text, re.MULTILINE))
        
        if len(pages) > 0:
            structure['average_words_per_page'] = total_words / len(pages)
        
        return structure
    
    def _analyze_content(self, text: str) -> Dict[str, Any]:
        """Analyze document content characteristics."""
        if not text:
            return {'error': 'No text content to analyze'}
        
        # Basic text statistics
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        # Calculate readability metrics
        avg_words_per_sentence = len(words) / len(sentences) if sentences else 0
        avg_chars_per_word = sum(len(word) for word in words) / len(words) if words else 0
        
        # Identify document sections
        sections = self._identify_sections(text)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(text)
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'character_count': len(text),
            'avg_words_per_sentence': round(avg_words_per_sentence, 2),
            'avg_chars_per_word': round(avg_chars_per_word, 2),
            'sections': sections,
            'key_phrases': key_phrases,
            'complexity_score': self._calculate_complexity_score(text)
        }
    
    def _extract_key_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract key entities from document text."""
        entities = {
            'organizations': [],
            'locations': [],
            'regulations': [],
            'standards': [],
            'dates': [],
            'monetary_amounts': [],
            'percentages': []
        }
        
        # Organization patterns
        org_patterns = [
            r'\b([A-Z][a-zA-Z\s&]+(?:Pty|Ltd|Inc|Corp|Company|Corporation|Group|Holdings)\.?)\b',
            r'\b([A-Z][a-zA-Z\s]+(?:Department|Ministry|Authority|Commission|Board))\b'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['organizations'].extend([match.strip() for match in matches])
        
        # Location patterns (Australian focus)
        location_patterns = [
            r'\b(New South Wales|NSW|Queensland|QLD|Western Australia|WA|South Australia|SA|Victoria|VIC|Tasmania|TAS|Northern Territory|NT|Australian Capital Territory|ACT)\b',
            r'\b([A-Z][a-zA-Z\s]+(?:City|Town|Shire|Council))\b'
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['locations'].extend([match.strip() for match in matches])
        
        # Regulation references
        reg_patterns = [
            r'\b([A-Z][a-zA-Z\s]+Act\s+\d{4})\b',
            r'\b(Regulation\s+\d+[A-Za-z]?(?:\(\d+\))?)\b',
            r'\b(Section\s+\d+[A-Za-z]?(?:\(\d+\))?)\b'
        ]
        
        for pattern in reg_patterns:
            matches = re.findall(pattern, text)
            entities['regulations'].extend([match.strip() for match in matches])
        
        # Standards
        std_patterns = [
            r'\b(AS\s+\d+(?:\.\d+)?(?::\d{4})?)\b',
            r'\b(ISO\s+\d+(?::\d{4})?)\b',
            r'\b(ANSI\s+[A-Z]+\d+)\b'
        ]
        
        for pattern in std_patterns:
            matches = re.findall(pattern, text)
            entities['standards'].extend([match.strip() for match in matches])
        
        # Monetary amounts
        money_patterns = [
            r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',
            r'\b\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*dollars?\b'
        ]
        
        for pattern in money_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities['monetary_amounts'].extend(matches)
        
        # Percentages
        percentage_pattern = r'\b\d+(?:\.\d+)?%\b'
        entities['percentages'] = re.findall(percentage_pattern, text)
        
        # Remove duplicates and limit results
        for key in entities:
            entities[key] = list(set(entities[key]))[:10]  # Limit to top 10
        
        return entities
    
    def _extract_dates(self, text: str) -> List[Dict[str, str]]:
        """Extract dates from document text."""
        dates = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_str = match.group(1)
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context = text[context_start:context_end].strip()
                
                dates.append({
                    'date_string': date_str,
                    'context': context,
                    'position': match.start()
                })
        
        # Remove duplicates and sort by position
        unique_dates = []
        seen_dates = set()
        
        for date_info in sorted(dates, key=lambda x: x['position']):
            if date_info['date_string'] not in seen_dates:
                unique_dates.append(date_info)
                seen_dates.add(date_info['date_string'])
        
        return unique_dates[:20]  # Limit to 20 dates
    
    def _classify_document(self, text: str) -> Dict[str, Any]:
        """Classify document type based on content."""
        text_lower = text.lower()
        
        # Count indicators
        contract_score = sum(1 for indicator in self.contract_indicators if indicator in text_lower)
        regulation_score = sum(1 for indicator in self.regulation_indicators if indicator in text_lower)
        
        # Determine primary classification
        if contract_score > regulation_score:
            primary_type = 'contract'
            confidence = min(1.0, contract_score / 5.0)
        elif regulation_score > contract_score:
            primary_type = 'regulation'
            confidence = min(1.0, regulation_score / 5.0)
        else:
            primary_type = 'unknown'
            confidence = 0.0
        
        # Determine secondary classifications
        secondary_types = []
        
        if any(keyword in text_lower for keyword in self.mining_keywords):
            secondary_types.append('mining_related')
        
        if any(keyword in text_lower for keyword in self.safety_keywords):
            secondary_types.append('safety_related')
        
        if any(keyword in text_lower for keyword in self.environmental_keywords):
            secondary_types.append('environmental_related')
        
        return {
            'primary_type': primary_type,
            'confidence': round(confidence, 3),
            'secondary_types': secondary_types,
            'contract_indicators': contract_score,
            'regulation_indicators': regulation_score
        }
    
    def _identify_compliance_areas(self, text: str) -> Dict[str, Any]:
        """Identify compliance areas mentioned in the document."""
        text_lower = text.lower()
        
        compliance_areas = {
            'safety_compliance': {
                'score': 0,
                'keywords_found': [],
                'sections': []
            },
            'environmental_compliance': {
                'score': 0,
                'keywords_found': [],
                'sections': []
            },
            'operational_compliance': {
                'score': 0,
                'keywords_found': [],
                'sections': []
            },
            'legal_compliance': {
                'score': 0,
                'keywords_found': [],
                'sections': []
            }
        }
        
        # Safety compliance
        safety_keywords = self.safety_keywords + [
            'whs', 'work health and safety', 'occupational health',
            'safety management system', 'hazard identification',
            'risk assessment', 'safety training', 'safety procedures'
        ]
        
        for keyword in safety_keywords:
            if keyword in text_lower:
                compliance_areas['safety_compliance']['score'] += 1
                compliance_areas['safety_compliance']['keywords_found'].append(keyword)
        
        # Environmental compliance
        env_keywords = self.environmental_keywords + [
            'epbc', 'environmental protection', 'biodiversity',
            'cultural heritage', 'native title', 'land use',
            'water management', 'air quality', 'noise management'
        ]
        
        for keyword in env_keywords:
            if keyword in text_lower:
                compliance_areas['environmental_compliance']['score'] += 1
                compliance_areas['environmental_compliance']['keywords_found'].append(keyword)
        
        # Operational compliance
        operational_keywords = [
            'tenement', 'mining lease', 'exploration licence',
            'production', 'reporting', 'audit', 'inspection',
            'compliance monitoring', 'record keeping', 'documentation'
        ]
        
        for keyword in operational_keywords:
            if keyword in text_lower:
                compliance_areas['operational_compliance']['score'] += 1
                compliance_areas['operational_compliance']['keywords_found'].append(keyword)
        
        # Legal compliance
        legal_keywords = [
            'contract', 'agreement', 'terms', 'conditions',
            'liability', 'indemnity', 'warranty', 'breach',
            'termination', 'dispute resolution', 'governing law'
        ]
        
        for keyword in legal_keywords:
            if keyword in text_lower:
                compliance_areas['legal_compliance']['score'] += 1
                compliance_areas['legal_compliance']['keywords_found'].append(keyword)
        
        # Normalize scores and limit keywords
        for area in compliance_areas:
            compliance_areas[area]['keywords_found'] = list(set(compliance_areas[area]['keywords_found']))[:10]
            compliance_areas[area]['normalized_score'] = min(1.0, compliance_areas[area]['score'] / 10.0)
        
        return compliance_areas
    
    def _calculate_quality_metrics(self, processed_content: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate document quality metrics."""
        confidence = processed_content.get('confidence', 0.0)
        full_text = processed_content.get('full_text', '')
        pages = processed_content.get('pages', [])
        
        # Text quality metrics
        text_length_score = min(1.0, len(full_text) / 5000)  # Normalize to 5000 chars
        
        # Page consistency
        if pages:
            page_confidences = [p.get('confidence', 0.0) for p in pages]
            confidence_variance = sum((c - confidence) ** 2 for c in page_confidences) / len(page_confidences)
            consistency_score = max(0.0, 1.0 - confidence_variance)
        else:
            consistency_score = 0.0
        
        # Content completeness
        has_meaningful_content = len(full_text.split()) > 50
        completeness_score = 1.0 if has_meaningful_content else 0.0
        
        # Overall quality score
        overall_quality = (confidence + text_length_score + consistency_score + completeness_score) / 4
        
        return {
            'overall_quality': round(overall_quality, 3),
            'ocr_confidence': round(confidence, 3),
            'text_length_score': round(text_length_score, 3),
            'consistency_score': round(consistency_score, 3),
            'completeness_score': round(completeness_score, 3),
            'has_meaningful_content': has_meaningful_content
        }
    
    def _analyze_language(self, text: str) -> Dict[str, Any]:
        """Analyze language characteristics of the document."""
        if not text:
            return {'language': 'unknown', 'confidence': 0.0}
        
        # Simple language detection (English focus)
        english_indicators = [
            'the', 'and', 'or', 'of', 'to', 'in', 'for', 'with', 'by', 'from',
            'shall', 'will', 'must', 'may', 'should', 'would', 'could'
        ]
        
        words = text.lower().split()
        english_word_count = sum(1 for word in words if word in english_indicators)
        english_confidence = min(1.0, english_word_count / len(words)) if words else 0.0
        
        # Detect formal/legal language
        formal_indicators = [
            'whereas', 'therefore', 'hereby', 'herein', 'thereof', 'pursuant',
            'notwithstanding', 'aforementioned', 'heretofore', 'hereafter'
        ]
        
        formal_word_count = sum(1 for indicator in formal_indicators if indicator in text.lower())
        formality_score = min(1.0, formal_word_count / 10.0)
        
        return {
            'language': 'english' if english_confidence > 0.5 else 'unknown',
            'confidence': round(english_confidence, 3),
            'formality_score': round(formality_score, 3),
            'is_legal_document': formality_score > 0.3,
            'word_count': len(words)
        }
    
    def _identify_sections(self, text: str) -> List[Dict[str, Any]]:
        """Identify document sections and headers."""
        sections = []
        lines = text.split('\n')
        
        section_patterns = [
            (r'^\s*\d+\.\s+(.+)$', 'numbered_section'),
            (r'^\s*\d+\.\d+\s+(.+)$', 'numbered_subsection'),
            (r'^\s*[A-Z][A-Z\s]{5,}$', 'caps_header'),
            (r'^\s*SECTION\s+\d+[:\-\s]+(.+)$', 'formal_section'),
            (r'^\s*PART\s+[IVX]+[:\-\s]+(.+)$', 'part_header')
        ]
        
        for line_num, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            for pattern, section_type in section_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    title = match.group(1) if match.groups() else line
                    sections.append({
                        'line_number': line_num + 1,
                        'type': section_type,
                        'title': title.strip(),
                        'full_text': line
                    })
                    break
        
        return sections[:50]  # Limit to 50 sections
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from document text."""
        # This is a simplified approach - in production, you might use more sophisticated NLP
        sentences = re.split(r'[.!?]+', text)
        key_phrases = []
        
        # Look for sentences with compliance-related keywords
        compliance_keywords = (
            self.safety_keywords + self.environmental_keywords + 
            ['compliance', 'requirement', 'obligation', 'standard', 'procedure']
        )
        
        for sentence in sentences:
            sentence = sentence.strip()
            if 10 <= len(sentence.split()) <= 20:  # Reasonable phrase length
                if any(keyword in sentence.lower() for keyword in compliance_keywords):
                    key_phrases.append(sentence)
        
        return key_phrases[:20]  # Limit to 20 phrases
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity score."""
        if not text:
            return 0.0
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences or not words:
            return 0.0
        
        # Calculate metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Normalize to 0-1 scale
        sentence_complexity = min(1.0, avg_sentence_length / 25.0)
        word_complexity = min(1.0, avg_word_length / 8.0)
        
        return round((sentence_complexity + word_complexity) / 2, 3)
