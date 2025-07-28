
"""
Safety compliance agent for agentic reasoning.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class SafetyComplianceAgent:
    def __init__(self):
        self.safety_categories = [
            'safety_management_system',
            'hazard_management', 
            'emergency_procedures',
            'safety_training'
        ]
    
    def analyze_compliance(self, mappings: List[Dict]) -> Dict[str, Any]:
        safety_mappings = [m for m in mappings if m.get('compliance_category') == 'safety_compliance']
        
        gaps = []
        for mapping in safety_mappings:
            if mapping.get('similarity_score', 0) < 0.8:
                gaps.append({
                    'clause_id': mapping.get('clause_id'),
                    'gap_type': 'low_similarity',
                    'severity': 'medium',
                    'recommendation': 'Review safety requirements alignment'
                })
        
        risk_score = max(0.3, 1.0 - (len(gaps) / max(1, len(safety_mappings))))
        
        return {
            'compliance_gaps': gaps,
            'risk_score': risk_score,
            'risk_level': 'high' if risk_score < 0.6 else 'medium' if risk_score < 0.8 else 'low',
            'recommendations': [f"Address {len(gaps)} safety compliance gaps"],
            'mappings_analyzed': len(safety_mappings)
        }
