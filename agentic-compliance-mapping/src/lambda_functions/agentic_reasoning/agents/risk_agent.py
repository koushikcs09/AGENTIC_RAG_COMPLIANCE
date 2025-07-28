
"""
Risk assessment agent for agentic reasoning.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class RiskAssessmentAgent:
    def __init__(self):
        self.risk_factors = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.5,
            'low': 0.2
        }
    
    def analyze_compliance(self, mappings: List[Dict]) -> Dict[str, Any]:
        total_mappings = len(mappings)
        if total_mappings == 0:
            return {
                'overall_risk_score': 1.0,
                'risk_level': 'critical',
                'risk_factors': ['No compliance mappings found'],
                'recommendations': ['Immediate compliance review required']
            }
        
        # Calculate risk based on similarity scores
        low_similarity_count = sum(1 for m in mappings if m.get('similarity_score', 0) < 0.7)
        risk_ratio = low_similarity_count / total_mappings
        
        overall_risk = min(1.0, risk_ratio + 0.2)  # Base risk + similarity risk
        
        risk_level = 'critical' if overall_risk > 0.8 else 'high' if overall_risk > 0.6 else 'medium' if overall_risk > 0.4 else 'low'
        
        return {
            'overall_risk_score': round(overall_risk, 3),
            'risk_level': risk_level,
            'risk_factors': [f'{low_similarity_count} mappings with low similarity'],
            'recommendations': ['Comprehensive compliance review recommended'] if overall_risk > 0.6 else ['Monitor compliance status'],
            'mappings_analyzed': total_mappings
        }
