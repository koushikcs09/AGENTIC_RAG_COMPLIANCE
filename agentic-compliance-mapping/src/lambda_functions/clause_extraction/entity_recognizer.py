
"""
Entity recognition utilities for clause extraction.
Identifies and extracts key entities from contract clauses.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import spacy

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an extracted entity."""
    entity_type: str
    entity_value: str
    confidence: float
    start_position: int
    end_position: int
    context: str
    normalized_value: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EntityRecognizer:
    """Entity recognition for mining compliance documents."""
    
    def __init__(self):
        self.nlp = None  # Will be loaded lazily
        self.entity_patterns = self._load_entity_patterns()
        self.australian_jurisdictions = [
            'new south wales', 'nsw', 'queensland', 'qld', 
            'western australia', 'wa', 'south australia', 'sa',
            'victoria', 'vic', 'tasmania', 'tas', 
            'northern territory', 'nt', 'australian capital territory', 'act',
            'commonwealth', 'federal', 'australia'
        ]
    
    def _load_spacy_model(self):
        """Lazy load spaCy model."""
        if self.nlp is None:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning("spaCy model not found, using pattern-based recognition only")
                self.nlp = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from clause text."""
        try:
            if not text or not text.strip():
                return []
            
            entities = []
            
            # Pattern-based extraction (always available)
            pattern_entities = self._extract_pattern_entities(text)
            entities.extend(pattern_entities)
            
            # spaCy-based extraction (if available)
            if self.nlp is None:
                self._load_spacy_model()
            
            if self.nlp is not None:
                spacy_entities = self._extract_spacy_entities(text)
                entities.extend(spacy_entities)
            
            # Deduplicate and merge entities
            merged_entities = self._merge_entities(entities)
            
            # Validate and normalize entities
            validated_entities = self._validate_entities(merged_entities, text)
            
            return validated_entities
            
        except Exception as e:
            logger.error(f"Entity extraction error: {e}")
            return []
    
    def _load_entity_patterns(self) -> Dict[str, List[str]]:
        """Load regex patterns for entity recognition."""
        return {
            'regulation_reference': [
                r'\b([A-Z][a-zA-Z\s]+Act\s+\d{4})\b',
                r'\b(Regulation\s+\d+[A-Za-z]?(?:\(\d+\))?)\b',
                r'\b(Section\s+\d+[A-Za-z]?(?:\(\d+\))?)\b',
                r'\b(Part\s+[IVX]+[A-Za-z]?)\b',
                r'\b(Schedule\s+\d+[A-Za-z]?)\b',
                r'\b(Clause\s+\d+[A-Za-z]?(?:\(\d+\))?)\b'
            ],
            'standard_reference': [
                r'\b(AS\s+\d+(?:\.\d+)?(?::\d{4})?)\b',
                r'\b(ISO\s+\d+(?::\d{4})?)\b',
                r'\b(ANSI\s+[A-Z]+\d+)\b',
                r'\b(BS\s+\d+(?::\d{4})?)\b',
                r'\b(EN\s+\d+(?::\d{4})?)\b'
            ],
            'organization': [
                r'\b([A-Z][a-zA-Z\s&]+(?:Pty|Ltd|Inc|Corp|Company|Corporation|Group|Holdings)\.?)\b',
                r'\b([A-Z][a-zA-Z\s]+(?:Department|Ministry|Authority|Commission|Board|Agency))\b',
                r'\b([A-Z][a-zA-Z\s]+(?:Council|Government|Administration))\b'
            ],
            'location': [
                r'\b(New South Wales|NSW|Queensland|QLD|Western Australia|WA|South Australia|SA|Victoria|VIC|Tasmania|TAS|Northern Territory|NT|Australian Capital Territory|ACT)\b',
                r'\b([A-Z][a-zA-Z\s]+(?:City|Town|Shire|Municipality|Region))\b',
                r'\b([A-Z][a-zA-Z\s]+(?:Mine|Quarry|Site|Facility|Plant))\b'
            ],
            'date': [
                r'\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b',
                r'\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b',
                r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{2,4})\b',
                r'\b(\d{2,4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})\b'
            ],
            'monetary': [
                r'(\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*dollars?)\b',
                r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*AUD)\b'
            ],
            'percentage': [
                r'\b(\d+(?:\.\d+)?%)\b',
                r'\b(\d+(?:\.\d+)?\s*per\s*cent)\b'
            ],
            'time_period': [
                r'\b(\d+\s*(?:day|week|month|year|hour)s?)\b',
                r'\b(within\s+\d+\s*(?:day|week|month|year|hour)s?)\b',
                r'\b(not\s+less\s+than\s+\d+\s*(?:day|week|month|year)s?)\b'
            ],
            'mining_equipment': [
                r'\b(excavator|bulldozer|dump\s+truck|loader|drill|crusher|conveyor|processing\s+plant)\b',
                r'\b(haul\s+truck|grader|compactor|dragline|shovel|scraper)\b'
            ],
            'safety_equipment': [
                r'\b(hard\s+hat|safety\s+helmet|high\s+vis|safety\s+vest|safety\s+boots)\b',
                r'\b(respirator|breathing\s+apparatus|gas\s+detector|safety\s+harness)\b',
                r'\b(first\s+aid\s+kit|emergency\s+equipment|fire\s+extinguisher)\b'
            ],
            'environmental_term': [
                r'\b(groundwater|surface\s+water|water\s+table|aquifer|watershed)\b',
                r'\b(flora|fauna|ecosystem|habitat|biodiversity|endangered\s+species)\b',
                r'\b(air\s+quality|noise\s+level|dust\s+emission|water\s+quality)\b'
            ]
        }
    
    def _extract_pattern_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using regex patterns."""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    entity_value = match.group(1) if match.groups() else match.group(0)
                    
                    # Get context around the entity
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(text), match.end() + 50)
                    context = text[context_start:context_end].strip()
                    
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_pattern_confidence(entity_type, entity_value)
                    
                    # Normalize entity value
                    normalized_value = self._normalize_entity_value(entity_type, entity_value)
                    
                    entity = {
                        'entity_type': entity_type,
                        'entity_value': entity_value.strip(),
                        'confidence': confidence,
                        'start_position': match.start(),
                        'end_position': match.end(),
                        'context': context,
                        'normalized_value': normalized_value,
                        'extraction_method': 'pattern',
                        'metadata': {
                            'pattern_used': pattern,
                            'match_groups': match.groups()
                        }
                    }
                    
                    entities.append(entity)
        
        return entities
    
    def _extract_spacy_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using spaCy NER."""
        entities = []
        
        try:
            doc = self.nlp(text)
            
            for ent in doc.ents:
                # Map spaCy entity types to our types
                entity_type = self._map_spacy_entity_type(ent.label_)
                
                if entity_type:  # Only include mapped entity types
                    # Get context
                    context_start = max(0, ent.start_char - 50)
                    context_end = min(len(text), ent.end_char + 50)
                    context = text[context_start:context_end].strip()
                    
                    # Calculate confidence (spaCy doesn't provide confidence scores)
                    confidence = self._calculate_spacy_confidence(ent)
                    
                    # Normalize entity value
                    normalized_value = self._normalize_entity_value(entity_type, ent.text)
                    
                    entity = {
                        'entity_type': entity_type,
                        'entity_value': ent.text.strip(),
                        'confidence': confidence,
                        'start_position': ent.start_char,
                        'end_position': ent.end_char,
                        'context': context,
                        'normalized_value': normalized_value,
                        'extraction_method': 'spacy',
                        'metadata': {
                            'spacy_label': ent.label_,
                            'spacy_explanation': spacy.explain(ent.label_)
                        }
                    }
                    
                    entities.append(entity)
        
        except Exception as e:
            logger.error(f"spaCy entity extraction error: {e}")
        
        return entities
    
    def _map_spacy_entity_type(self, spacy_label: str) -> Optional[str]:
        """Map spaCy entity labels to our entity types."""
        mapping = {
            'ORG': 'organization',
            'GPE': 'location',  # Geopolitical entity
            'LOC': 'location',
            'DATE': 'date',
            'TIME': 'time_period',
            'MONEY': 'monetary',
            'PERCENT': 'percentage',
            'LAW': 'regulation_reference',
            'PERSON': 'person',
            'PRODUCT': 'mining_equipment'
        }
        
        return mapping.get(spacy_label)
    
    def _calculate_pattern_confidence(self, entity_type: str, entity_value: str) -> float:
        """Calculate confidence score for pattern-based entities."""
        base_confidence = 0.8  # Base confidence for pattern matches
        
        # Adjust based on entity type specificity
        type_adjustments = {
            'regulation_reference': 0.1,  # High confidence for regulation patterns
            'standard_reference': 0.1,
            'monetary': 0.05,
            'percentage': 0.05,
            'date': 0.0,
            'organization': -0.1,  # Lower confidence, might be false positives
            'location': -0.1
        }
        
        adjustment = type_adjustments.get(entity_type, 0.0)
        confidence = base_confidence + adjustment
        
        # Adjust based on entity value characteristics
        if len(entity_value) < 3:
            confidence -= 0.2  # Very short entities are less reliable
        elif len(entity_value) > 100:
            confidence -= 0.1  # Very long entities might be extraction errors
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_spacy_confidence(self, ent) -> float:
        """Calculate confidence score for spaCy entities."""
        # spaCy doesn't provide confidence scores, so we estimate based on entity characteristics
        base_confidence = 0.7
        
        # Adjust based on entity length and type
        if len(ent.text) < 2:
            return 0.3  # Very short entities are unreliable
        elif len(ent.text) > 50:
            return 0.5  # Very long entities might be errors
        
        # Adjust based on entity label confidence
        label_confidence = {
            'ORG': 0.8,
            'GPE': 0.9,
            'DATE': 0.9,
            'MONEY': 0.9,
            'PERCENT': 0.9,
            'LAW': 0.7,
            'PERSON': 0.6
        }
        
        return label_confidence.get(ent.label_, base_confidence)
    
    def _normalize_entity_value(self, entity_type: str, entity_value: str) -> str:
        """Normalize entity values for consistency."""
        normalized = entity_value.strip()
        
        if entity_type == 'location':
            # Normalize Australian jurisdictions
            normalized_lower = normalized.lower()
            for jurisdiction in self.australian_jurisdictions:
                if jurisdiction.lower() == normalized_lower:
                    # Return standardized form
                    jurisdiction_map = {
                        'new south wales': 'NSW',
                        'queensland': 'QLD',
                        'western australia': 'WA',
                        'south australia': 'SA',
                        'victoria': 'VIC',
                        'tasmania': 'TAS',
                        'northern territory': 'NT',
                        'australian capital territory': 'ACT'
                    }
                    return jurisdiction_map.get(jurisdiction.lower(), jurisdiction.upper())
        
        elif entity_type == 'regulation_reference':
            # Normalize regulation references
            normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
            normalized = normalized.title()  # Title case
        
        elif entity_type == 'standard_reference':
            # Normalize standards (uppercase)
            normalized = normalized.upper()
        
        elif entity_type == 'monetary':
            # Normalize monetary amounts
            normalized = re.sub(r'[^\d\.\$,]', '', normalized)
        
        elif entity_type == 'percentage':
            # Normalize percentages
            normalized = re.sub(r'\s+', '', normalized)
        
        elif entity_type == 'date':
            # Basic date normalization (could be enhanced with proper date parsing)
            normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _merge_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge overlapping entities and remove duplicates."""
        if not entities:
            return []
        
        # Sort entities by start position
        sorted_entities = sorted(entities, key=lambda x: x['start_position'])
        
        merged = []
        current_entity = sorted_entities[0]
        
        for next_entity in sorted_entities[1:]:
            # Check for overlap
            if (next_entity['start_position'] <= current_entity['end_position'] and
                next_entity['end_position'] >= current_entity['start_position']):
                
                # Entities overlap - merge them
                if next_entity['confidence'] > current_entity['confidence']:
                    # Keep the higher confidence entity
                    current_entity = next_entity
                # Otherwise keep current_entity
                
            else:
                # No overlap - add current entity and move to next
                merged.append(current_entity)
                current_entity = next_entity
        
        # Add the last entity
        merged.append(current_entity)
        
        return merged
    
    def _validate_entities(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Validate and filter entities."""
        validated = []
        
        for entity in entities:
            # Basic validation checks
            if not entity['entity_value'] or len(entity['entity_value'].strip()) < 2:
                continue  # Skip very short entities
            
            if entity['confidence'] < 0.3:
                continue  # Skip low confidence entities
            
            # Check if entity value actually exists in text at specified position
            start_pos = entity['start_position']
            end_pos = entity['end_position']
            
            if (start_pos >= 0 and end_pos <= len(text) and
                entity['entity_value'].lower() in text[start_pos:end_pos].lower()):
                
                # Entity is valid
                validated.append(entity)
        
        return validated
    
    def extract_regulation_entities(self, text: str) -> List[Dict[str, Any]]:
        """Specialized extraction for regulation-related entities."""
        regulation_entities = []
        
        # Australian mining-specific regulations
        mining_regulations = [
            r'\b(Mining\s+Act\s+\d{4})\b',
            r'\b(Petroleum\s+and\s+Gas\s+\(Production\s+and\s+Safety\)\s+Act\s+\d{4})\b',
            r'\b(Environmental\s+Protection\s+Act\s+\d{4})\b',
            r'\b(Work\s+Health\s+and\s+Safety\s+Act\s+\d{4})\b',
            r'\b(Native\s+Title\s+Act\s+\d{4})\b',
            r'\b(Aboriginal\s+Cultural\s+Heritage\s+Act\s+\d{4})\b',
            r'\b(Environment\s+Protection\s+and\s+Biodiversity\s+Conservation\s+Act\s+\d{4})\b'
        ]
        
        for pattern in mining_regulations:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                entity_value = match.group(1)
                
                # Get context
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end].strip()
                
                regulation_entities.append({
                    'entity_type': 'regulation_reference',
                    'entity_value': entity_value,
                    'confidence': 0.9,  # High confidence for specific mining regulations
                    'start_position': match.start(),
                    'end_position': match.end(),
                    'context': context,
                    'normalized_value': entity_value.title(),
                    'extraction_method': 'specialized_pattern',
                    'metadata': {
                        'regulation_category': 'mining_specific',
                        'jurisdiction': self._infer_jurisdiction(entity_value)
                    }
                })
        
        return regulation_entities
    
    def _infer_jurisdiction(self, regulation_name: str) -> str:
        """Infer jurisdiction from regulation name."""
        # This is a simplified approach - in practice, you'd have a comprehensive mapping
        if 'commonwealth' in regulation_name.lower() or 'epbc' in regulation_name.lower():
            return 'federal'
        else:
            return 'state'  # Default to state level
    
    def get_entity_statistics(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics from extracted entities."""
        if not entities:
            return {'total_entities': 0}
        
        # Count by type
        type_counts = {}
        confidence_scores = []
        extraction_methods = {}
        
        for entity in entities:
            entity_type = entity.get('entity_type', 'unknown')
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1
            
            confidence_scores.append(entity.get('confidence', 0.0))
            
            method = entity.get('extraction_method', 'unknown')
            extraction_methods[method] = extraction_methods.get(method, 0) + 1
        
        # Calculate statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        high_confidence_count = sum(1 for score in confidence_scores if score >= 0.8)
        
        return {
            'total_entities': len(entities),
            'entity_type_distribution': type_counts,
            'extraction_method_distribution': extraction_methods,
            'average_confidence': round(avg_confidence, 3),
            'high_confidence_entities': high_confidence_count,
            'high_confidence_percentage': round(high_confidence_count / len(entities) * 100, 1)
        }
