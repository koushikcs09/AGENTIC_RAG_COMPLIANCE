
"""
AWS Lambda function for semantic alignment and mapping pipeline.
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
from common.database import vector_store, db_connection
from common.utils import create_api_response, timing_decorator

logger = logging.getLogger(__name__)
eventbridge = boto3.client('events', region_name=config.aws.region)

class SemanticMappingHandler:
    def __init__(self):
        self.vector_store = vector_store
    
    @timing_decorator
    def process_semantic_mapping(self, event: Dict[str, Any]) -> Dict[str, Any]:
        try:
            document_id = event.get('document_id')
            
            # Get clauses from database
            clauses_query = """
            SELECT clause_id, clause_text, clause_type 
            FROM PROCESSED.CLAUSES 
            WHERE document_id = %s
            """
            clauses = db_connection.execute_query(clauses_query, {'document_id': document_id})
            
            mappings_created = 0
            for clause in clauses:
                # Generate embedding
                embedding = self.vector_store.generate_embedding(clause['CLAUSE_TEXT'])
                
                # Store embedding
                self.vector_store.store_clause_embedding(
                    clause['CLAUSE_ID'], 
                    clause['CLAUSE_TEXT']
                )
                
                # Find similar regulations
                similar_regs = self.vector_store.find_similar_regulations(embedding)
                
                # Store mappings
                for reg in similar_regs:
                    mapping_data = {
                        'mapping_id': f"map_{clause['CLAUSE_ID']}_{reg['regulation_id']}",
                        'clause_id': clause['CLAUSE_ID'],
                        'regulation_id': reg['regulation_id'],
                        'similarity_score': reg['similarity_score'],
                        'mapping_type': 'semantic_similarity',
                        'compliance_category': reg['regulation_category']
                    }
                    
                    db_connection.execute_non_query("""
                        INSERT INTO ANALYTICS.COMPLIANCE_MAPPINGS 
                        (compliance_mapping_id, clause_id, regulation_id, similarity_score, mapping_type, compliance_category)
                        VALUES (%(mapping_id)s, %(clause_id)s, %(regulation_id)s, %(similarity_score)s, %(mapping_type)s, %(compliance_category)s)
                    """, mapping_data)
                    
                    mappings_created += 1
            
            # Publish completion event
            self._publish_mapping_event(document_id, 'semantic_mapping_completed')
            
            return create_api_response(
                success=True,
                data={
                    'document_id': document_id,
                    'mappings_created': mappings_created,
                    'processing_status': 'semantic_mapping_completed'
                }
            )
            
        except Exception as e:
            logger.error(f"Semantic mapping error: {e}")
            return create_api_response(
                success=False,
                error={'code': 'SEMANTIC_MAPPING_ERROR', 'message': str(e)}
            )
    
    def _publish_mapping_event(self, document_id: str, status: str):
        eventbridge.put_events(
            Entries=[{
                'Source': 'compliance.semantic.mapping',
                'DetailType': 'Semantic Mapping Status Change',
                'Detail': json.dumps({
                    'document_id': document_id,
                    'status': status,
                    'pipeline_stage': 'semantic_mapping'
                }),
                'EventBusName': 'compliance-processing-bus'
            }]
        )

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    handler = SemanticMappingHandler()
    return handler.process_semantic_mapping(event)
