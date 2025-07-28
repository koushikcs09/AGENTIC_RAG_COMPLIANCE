
"""
AWS Lambda function for agentic reasoning pipeline.
"""

import json
import logging
import boto3
from typing import Dict, List, Any
import sys
import os

sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from common.config import config
from common.database import db_connection
from common.utils import create_api_response, timing_decorator
from agents.safety_agent import SafetyComplianceAgent
from agents.environmental_agent import EnvironmentalAgent
from agents.risk_agent import RiskAssessmentAgent

logger = logging.getLogger(__name__)
eventbridge = boto3.client('events', region_name=config.aws.region)

class AgenticReasoningHandler:
    def __init__(self):
        self.agents = {
            'safety': SafetyComplianceAgent(),
            'environmental': EnvironmentalAgent(),
            'risk': RiskAssessmentAgent()
        }
    
    @timing_decorator
    def process_agentic_reasoning(self, event: Dict[str, Any]) -> Dict[str, Any]:
        try:
            document_id = event.get('document_id')
            
            # Get compliance mappings
            mappings_query = """
            SELECT * FROM ANALYTICS.COMPLIANCE_MAPPINGS 
            WHERE clause_id IN (
                SELECT clause_id FROM PROCESSED.CLAUSES WHERE document_id = %s
            )
            """
            mappings = db_connection.execute_query(mappings_query, {'document_id': document_id})
            
            # Run agent analyses
            agent_results = {}
            for agent_name, agent in self.agents.items():
                result = agent.analyze_compliance(mappings)
                agent_results[agent_name] = result
            
            # Consolidate results
            overall_analysis = self._consolidate_analyses(agent_results)
            
            # Store analysis results
            analysis_data = {
                'analysis_id': f"analysis_{document_id}",
                'document_id': document_id,
                'agent_analyses': json.dumps(agent_results),
                'overall_risk_score': overall_analysis['overall_risk_score'],
                'analysis_type': 'full_compliance'
            }
            
            db_connection.execute_non_query("""
                INSERT INTO ANALYTICS.ANALYSIS_RESULTS 
                (analysis_id, document_id, agent_analyses, overall_risk_score, analysis_type)
                VALUES (%(analysis_id)s, %(document_id)s, PARSE_JSON(%(agent_analyses)s), %(overall_risk_score)s, %(analysis_type)s)
            """, analysis_data)
            
            # Publish completion event
            self._publish_reasoning_event(document_id, 'agentic_reasoning_completed')
            
            return create_api_response(
                success=True,
                data={
                    'document_id': document_id,
                    'analysis_id': analysis_data['analysis_id'],
                    'overall_risk_score': overall_analysis['overall_risk_score'],
                    'processing_status': 'agentic_reasoning_completed'
                }
            )
            
        except Exception as e:
            logger.error(f"Agentic reasoning error: {e}")
            return create_api_response(
                success=False,
                error={'code': 'AGENTIC_REASONING_ERROR', 'message': str(e)}
            )
    
    def _consolidate_analyses(self, agent_results: Dict) -> Dict:
        risk_scores = [result.get('risk_score', 0.5) for result in agent_results.values()]
        overall_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.5
        
        return {
            'overall_risk_score': round(overall_risk, 3),
            'agent_count': len(agent_results),
            'consolidated_recommendations': []
        }
    
    def _publish_reasoning_event(self, document_id: str, status: str):
        eventbridge.put_events(
            Entries=[{
                'Source': 'compliance.agentic.reasoning',
                'DetailType': 'Agentic Reasoning Status Change',
                'Detail': json.dumps({
                    'document_id': document_id,
                    'status': status,
                    'pipeline_stage': 'agentic_reasoning'
                }),
                'EventBusName': 'compliance-processing-bus'
            }]
        )

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    handler = AgenticReasoningHandler()
    return handler.process_agentic_reasoning(event)
