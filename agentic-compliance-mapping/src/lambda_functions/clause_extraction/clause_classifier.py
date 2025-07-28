
"""
Clause classification utilities using AI models.
Classifies contract clauses into compliance categories.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ClauseType(Enum):
    """Enumeration of clause types for Australian mining compliance."""
    SAFETY_COMPLIANCE = "safety_compliance"
    ENVIRONMENTAL_COMPLIANCE = "environmental_compliance"
    OPERATIONAL_COMPLIANCE = "operational_compliance"
    COMMERCIAL_TERMS = "commercial_terms"
    LEGAL_PROVISIONS = "legal_provisions"
    ADMINISTRATIVE = "administrative"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of clause classification."""
    primary_type: str
    subtype: str
    confidence: float
    reasoning: str
    keywords_found: List[str]
    has_mandatory_language: bool
    has_penalties: bool
    complexity_score: float
    regulatory_references: List[str]


class ClauseClassifier:
    """AI-powered clause classifier for mining compliance documents."""
    
    def __init__(self):
        self.classification_rules = self._load_classification_rules()
        self.mandatory_indicators = [
            'shall', 'must', 'required', 'mandatory', 'obligated',
            'duty to', 'responsible for', 'ensure that', 'comply with'
        ]
        self.penalty_indicators = [
            'penalty', 'fine', 'breach', 'violation', 'default',
            'termination', 'damages', 'liability', 'forfeit'
        ]
    
    def classify_clause(self, clause_text: str) -> Dict[str, Any]:
        """Classify a clause into compliance categories."""
        try:
            if not clause_text or not clause_text.strip():
                return self._create_unknown_classification("Empty clause text")
            
            # Preprocess text
            processed_text = self._preprocess_text(clause_text)
            
            # Apply classification rules
            classification_scores = self._apply_classification_rules(processed_text)
            
            # Determine primary classification
            primary_type, confidence = self._determine_primary_classification(classification_scores)
            
            # Determine subtype
            subtype = self._determine_subtype(primary_type, processed_text)
            
            # Extract additional features
            features = self._extract_clause_features(processed_text)
            
            # Create classification result
            result = {
                'primary_type': primary_type,
                'subtype': subtype,
                'confidence': round(confidence, 3),
                'reasoning': self._generate_reasoning(primary_type, classification_scores),
                'keywords_found': features['keywords_found'],
                'has_mandatory_language': features['has_mandatory_language'],
                'has_penalties': features['has_penalties'],
                'complexity_score': features['complexity_score'],
                'regulatory_references': features['regulatory_references'],
                'classification_scores': classification_scores,
                'word_count': len(clause_text.split()),
                'sentence_count': len([s for s in clause_text.split('.') if s.strip()])
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self._create_unknown_classification(f"Classification failed: {str(e)}")
    
    def batch_classify_clauses(self, clauses: List[str]) -> List[Dict[str, Any]]:
        """Classify multiple clauses in batch."""
        results = []
        for i, clause_text in enumerate(clauses):
            try:
                result = self.classify_clause(clause_text)
                result['clause_index'] = i
                results.append(result)
            except Exception as e:
                logger.error(f"Error classifying clause {i}: {e}")
                error_result = self._create_unknown_classification(f"Batch classification error: {str(e)}")
                error_result['clause_index'] = i
                results.append(error_result)
        
        return results
    
    def _load_classification_rules(self) -> Dict[str, Dict]:
        """Load classification rules and keyword patterns."""
        return {
            'safety_compliance': {
                'keywords': [
                    'safety', 'health', 'whs', 'work health and safety',
                    'occupational health', 'hazard', 'risk assessment',
                    'safety management system', 'sms', 'safety procedures',
                    'personal protective equipment', 'ppe', 'safety training',
                    'incident', 'accident', 'injury', 'fatality',
                    'emergency', 'evacuation', 'first aid', 'safety officer',
                    'safety inspection', 'safety audit', 'safety compliance',
                    'hazard identification', 'risk control', 'safety plan'
                ],
                'regulatory_patterns': [
                    r'whs\s+act\s+\d{4}',
                    r'work\s+health\s+and\s+safety\s+act',
                    r'occupational\s+health\s+and\s+safety',
                    r'safety\s+management\s+system',
                    r'as\s+\d+\.\d+.*safety'
                ],
                'weight': 1.0,
                'subtypes': {
                    'safety_management_system': ['sms', 'safety management system', 'safety management'],
                    'hazard_management': ['hazard', 'risk assessment', 'hazard identification'],
                    'emergency_procedures': ['emergency', 'evacuation', 'emergency response'],
                    'safety_training': ['safety training', 'competency', 'safety education'],
                    'contractor_safety': ['contractor safety', 'subcontractor safety']
                }
            },
            'environmental_compliance': {
                'keywords': [
                    'environmental', 'environment', 'epbc', 'environmental protection',
                    'biodiversity', 'cultural heritage', 'native title',
                    'rehabilitation', 'restoration', 'remediation',
                    'water', 'air quality', 'noise', 'dust', 'emissions',
                    'waste', 'contamination', 'pollution', 'discharge',
                    'impact assessment', 'environmental impact',
                    'flora', 'fauna', 'ecosystem', 'habitat',
                    'groundwater', 'surface water', 'water management'
                ],
                'regulatory_patterns': [
                    r'epbc\s+act',
                    r'environment\s+protection\s+and\s+biodiversity\s+conservation',
                    r'environmental\s+protection\s+act',
                    r'native\s+title\s+act',
                    r'cultural\s+heritage\s+act'
                ],
                'weight': 1.0,
                'subtypes': {
                    'environmental_impact_assessment': ['eia', 'impact assessment', 'environmental assessment'],
                    'water_management': ['water', 'groundwater', 'surface water', 'water quality'],
                    'rehabilitation_obligations': ['rehabilitation', 'restoration', 'remediation'],
                    'waste_management': ['waste', 'disposal', 'waste management'],
                    'cultural_heritage': ['cultural heritage', 'aboriginal heritage', 'indigenous']
                }
            },
            'operational_compliance': {
                'keywords': [
                    'tenement', 'mining lease', 'exploration licence',
                    'production', 'extraction', 'mining operations',
                    'reporting', 'audit', 'inspection', 'monitoring',
                    'compliance', 'record keeping', 'documentation',
                    'annual report', 'quarterly report', 'notification',
                    'approval', 'permit', 'licence', 'authorization',
                    'variation', 'amendment', 'renewal', 'transfer'
                ],
                'regulatory_patterns': [
                    r'mining\s+act\s+\d{4}',
                    r'petroleum\s+and\s+gas\s+act',
                    r'mineral\s+resources\s+act',
                    r'exploration\s+licence',
                    r'mining\s+lease'
                ],
                'weight': 1.0,
                'subtypes': {
                    'tenement_conditions': ['tenement', 'lease conditions', 'licence conditions'],
                    'reporting_obligations': ['reporting', 'report', 'notification'],
                    'audit_access': ['audit', 'inspection', 'access'],
                    'documentation_requirements': ['documentation', 'record keeping', 'records'],
                    'change_management': ['variation', 'amendment', 'change']
                }
            },
            'commercial_terms': {
                'keywords': [
                    'payment', 'price', 'cost', 'fee', 'charge',
                    'invoice', 'billing', 'remuneration', 'compensation',
                    'delivery', 'supply', 'provision', 'service',
                    'warranty', 'guarantee', 'representation',
                    'indemnity', 'liability', 'insurance',
                    'termination', 'expiry', 'renewal', 'extension'
                ],
                'regulatory_patterns': [
                    r'gst', r'tax', r'duty', r'levy'
                ],
                'weight': 0.8,
                'subtypes': {
                    'payment_terms': ['payment', 'invoice', 'billing', 'remuneration'],
                    'delivery_conditions': ['delivery', 'supply', 'provision'],
                    'warranties': ['warranty', 'guarantee', 'representation'],
                    'indemnities': ['indemnity', 'liability', 'insurance'],
                    'termination_clauses': ['termination', 'expiry', 'breach']
                }
            },
            'legal_provisions': {
                'keywords': [
                    'governing law', 'jurisdiction', 'dispute resolution',
                    'arbitration', 'mediation', 'court', 'tribunal',
                    'breach', 'default', 'remedy', 'damages',
                    'force majeure', 'act of god', 'unforeseen circumstances',
                    'confidentiality', 'non-disclosure', 'proprietary',
                    'intellectual property', 'copyright', 'patent'
                ],
                'regulatory_patterns': [
                    r'corporations\s+act',
                    r'competition\s+and\s+consumer\s+act',
                    r'australian\s+consumer\s+law'
                ],
                'weight': 0.7,
                'subtypes': {
                    'dispute_resolution': ['dispute', 'arbitration', 'mediation'],
                    'governing_law': ['governing law', 'jurisdiction'],
                    'confidentiality': ['confidential', 'non-disclosure', 'proprietary'],
                    'intellectual_property': ['intellectual property', 'copyright', 'patent'],
                    'force_majeure': ['force majeure', 'act of god']
                }
            }
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess clause text for classification."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep important punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\!\?\-\(\)]', ' ', text)
        
        return text.strip()
    
    def _apply_classification_rules(self, text: str) -> Dict[str, float]:
        """Apply classification rules to determine clause type scores."""
        scores = {}
        
        for clause_type, rules in self.classification_rules.items():
            score = 0.0
            keywords_found = 0
            
            # Check keywords
            for keyword in rules['keywords']:
                if keyword in text:
                    score += 1.0
                    keywords_found += 1
            
            # Check regulatory patterns
            for pattern in rules.get('regulatory_patterns', []):
                if re.search(pattern, text, re.IGNORECASE):
                    score += 2.0  # Regulatory references get higher weight
            
            # Apply weight and normalize
            weighted_score = score * rules.get('weight', 1.0)
            
            # Normalize by text length (longer clauses might match more keywords)
            word_count = len(text.split())
            normalized_score = weighted_score / max(1, word_count / 50)  # Normalize per 50 words
            
            scores[clause_type] = {
                'raw_score': score,
                'weighted_score': weighted_score,
                'normalized_score': min(1.0, normalized_score),  # Cap at 1.0
                'keywords_found': keywords_found
            }
        
        return scores
    
    def _determine_primary_classification(self, scores: Dict[str, Dict]) -> Tuple[str, float]:
        """Determine primary classification from scores."""
        if not scores:
            return 'unknown', 0.0
        
        # Find the highest scoring classification
        best_type = 'unknown'
        best_score = 0.0
        
        for clause_type, score_data in scores.items():
            normalized_score = score_data['normalized_score']
            if normalized_score > best_score:
                best_score = normalized_score
                best_type = clause_type
        
        # Require minimum confidence threshold
        if best_score < 0.1:
            return 'unknown', 0.0
        
        return best_type, best_score
    
    def _determine_subtype(self, primary_type: str, text: str) -> str:
        """Determine subtype within the primary classification."""
        if primary_type == 'unknown' or primary_type not in self.classification_rules:
            return ''
        
        subtypes = self.classification_rules[primary_type].get('subtypes', {})
        best_subtype = ''
        best_score = 0
        
        for subtype, keywords in subtypes.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > best_score:
                best_score = score
                best_subtype = subtype
        
        return best_subtype
    
    def _extract_clause_features(self, text: str) -> Dict[str, Any]:
        """Extract additional features from clause text."""
        features = {
            'keywords_found': [],
            'has_mandatory_language': False,
            'has_penalties': False,
            'complexity_score': 0.0,
            'regulatory_references': []
        }
        
        # Check for mandatory language
        for indicator in self.mandatory_indicators:
            if indicator in text:
                features['has_mandatory_language'] = True
                features['keywords_found'].append(indicator)
        
        # Check for penalty language
        for indicator in self.penalty_indicators:
            if indicator in text:
                features['has_penalties'] = True
                features['keywords_found'].append(indicator)
        
        # Extract regulatory references
        reg_patterns = [
            r'([a-z\s]+act\s+\d{4})',
            r'(regulation\s+\d+)',
            r'(section\s+\d+[a-z]?)',
            r'(as\s+\d+(?:\.\d+)?)',
            r'(iso\s+\d+)'
        ]
        
        for pattern in reg_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            features['regulatory_references'].extend(matches)
        
        # Calculate complexity score
        features['complexity_score'] = self._calculate_complexity(text)
        
        # Remove duplicates
        features['keywords_found'] = list(set(features['keywords_found']))
        features['regulatory_references'] = list(set(features['regulatory_references']))
        
        return features
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate text complexity score."""
        words = text.split()
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if not sentences or not words:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Complex word ratio (words > 6 characters)
        complex_words = sum(1 for word in words if len(word) > 6)
        complex_word_ratio = complex_words / len(words)
        
        # Combine metrics (normalize to 0-1)
        complexity = (
            min(1.0, avg_sentence_length / 25) * 0.4 +
            min(1.0, avg_word_length / 8) * 0.3 +
            complex_word_ratio * 0.3
        )
        
        return round(complexity, 3)
    
    def _generate_reasoning(self, primary_type: str, scores: Dict[str, Dict]) -> str:
        """Generate human-readable reasoning for classification."""
        if primary_type == 'unknown':
            return "Could not determine clause type with sufficient confidence"
        
        score_data = scores.get(primary_type, {})
        keywords_found = score_data.get('keywords_found', 0)
        
        reasoning_parts = [
            f"Classified as '{primary_type.replace('_', ' ')}'"
        ]
        
        if keywords_found > 0:
            reasoning_parts.append(f"based on {keywords_found} relevant keywords")
        
        # Add top competing classifications
        sorted_scores = sorted(
            [(k, v['normalized_score']) for k, v in scores.items() if k != primary_type],
            key=lambda x: x[1],
            reverse=True
        )
        
        if sorted_scores and sorted_scores[0][1] > 0.1:
            competing_type = sorted_scores[0][0].replace('_', ' ')
            reasoning_parts.append(f"with some similarity to '{competing_type}'")
        
        return "; ".join(reasoning_parts)
    
    def _create_unknown_classification(self, reason: str) -> Dict[str, Any]:
        """Create classification result for unknown/failed classifications."""
        return {
            'primary_type': 'unknown',
            'subtype': '',
            'confidence': 0.0,
            'reasoning': reason,
            'keywords_found': [],
            'has_mandatory_language': False,
            'has_penalties': False,
            'complexity_score': 0.0,
            'regulatory_references': [],
            'classification_scores': {},
            'word_count': 0,
            'sentence_count': 0
        }
    
    def get_classification_statistics(self, classifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistics from a batch of classifications."""
        if not classifications:
            return {'error': 'No classifications provided'}
        
        # Count by type
        type_counts = {}
        confidence_scores = []
        
        for classification in classifications:
            primary_type = classification.get('primary_type', 'unknown')
            type_counts[primary_type] = type_counts.get(primary_type, 0) + 1
            confidence_scores.append(classification.get('confidence', 0.0))
        
        # Calculate statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        high_confidence_count = sum(1 for score in confidence_scores if score >= 0.7)
        
        return {
            'total_clauses': len(classifications),
            'type_distribution': type_counts,
            'average_confidence': round(avg_confidence, 3),
            'high_confidence_clauses': high_confidence_count,
            'high_confidence_percentage': round(high_confidence_count / len(classifications) * 100, 1)
        }
