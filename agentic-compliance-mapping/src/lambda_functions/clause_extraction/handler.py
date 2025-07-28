
"""
AWS Lambda function for clause extraction pipeline.
Handles AI-powered clause identification and classification.
"""

import json
import logging
import boto3
from typing import Dict, List, Any, Optional
import sys
import os

# Add src to path for imports
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from common.config import config
from common.database import document_repository, db_connection
from common.s3_client import document_storage
from common.utils import (
    generate_uuid, create_api_response, timing_decorator, 
    retry_with_backoff, chunk_text
)
from clause_classifier import ClauseClassifier
from entity_recognizer import EntityRecognizer
from langchain_processor import LangChainClauseProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
eventbridge = boto3.client('events', region_name=config.aws.region)


class ClauseExtractionHandler:
    """Handler for clause extraction operations."""
    
    def __init__(self):
        self.clause_classifier = ClauseClassifier()
        self.entity_recognizer = EntityRecognizer()
        self.langchain_processor = LangChainClauseProcessor()
    
    @timing_decorator
    @retry_with_backoff(max_retries=2)
    def process_clause_extraction(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process clause extraction from document ingestion completion."""
        try:
            # Extract document information from event
            document_id = event.get('document_id')
            if not document_id:
                raise ValueError("Missing document_id in event")
            
            # Get document from database
            document = document_repository.get_document(document_id)
            if not document:
                raise ValueError(f"Document not found: {document_id}")
            
            # Get processed content from S3
            processed_content = document_storage.get_processed_document(
                document_id, 'ocr_results'
            )
            
            # Extract clauses from document
            extraction_results = self._extract_clauses(document_id, processed_content)
            
            # Store extraction results
            self._store_extraction_results(document_id, extraction_results)
            
            # Update document status
            document_repository.update_document_status(
                document_id, 
                'clause_extraction_completed',
                {
                    'clauses_extracted': len(extraction_results['clauses']),
                    'entities_identified': sum(len(clause.get('entities', [])) for clause in extraction_results['clauses']),
                    'extraction_confidence': extraction_results['overall_confidence']
                }
            )
            
            # Publish event for semantic mapping
            self._publish_extraction_event(document_id, 'clause_extraction_completed')
            
            return create_api_response(
                success=True,
                data={
                    'document_id': document_id,
                    'clauses_extracted': len(extraction_results['clauses']),
                    'entities_identified': sum(len(clause.get('entities', [])) for clause in extraction_results['clauses']),
                    'processing_status': 'clause_extraction_completed',
                    'overall_confidence': extraction_results['overall_confidence']
                },
                message="Clause extraction completed successfully"
            )
            
        except Exception as e:
            logger.error(f"Clause extraction error: {e}")
            # Update document status to failed
            if 'document_id' in locals():
                document_repository.update_document_status(document_id, 'failed')
            
            return create_api_response(
                success=False,
                error={
                    'code': 'CLAUSE_EXTRACTION_ERROR',
                    'message': f"Failed to extract clauses: {str(e)}"
                }
            )
    
    def _extract_clauses(self, document_id: str, processed_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract clauses from processed document content."""
        full_text = processed_content.get('full_text', '')
        pages = processed_content.get('pages', [])
        
        if not full_text:
            raise ValueError("No text content found in processed document")
        
        # Use LangChain for initial clause identification
        langchain_results = self.langchain_processor.extract_clauses(full_text)
        
        # Process each identified clause
        extracted_clauses = []
        total_confidence = 0.0
        
        for i, clause_data in enumerate(langchain_results.get('clauses', [])):
            clause_id = f"{document_id}_clause_{i+1:03d}"
            
            # Classify clause type
            classification = self.clause_classifier.classify_clause(clause_data['text'])
            
            # Extract entities
            entities = self.entity_recognizer.extract_entities(clause_data['text'])
            
            # Determine page numbers
            page_numbers = self._find_clause_pages(clause_data['text'], pages)
            
            # Create clause record
            clause_record = {
                'clause_id': clause_id,
                'document_id': document_id,
                'clause_number': clause_data.get('clause_number', f"C{i+1:03d}"),
                'section_reference': clause_data.get('section_reference', ''),
                'clause_title': clause_data.get('title', ''),
                'clause_text': clause_data['text'],
                'clause_type': classification['primary_type'],
                'clause_subtype': classification.get('subtype', ''),
                'page_numbers': page_numbers,
                'word_count': len(clause_data['text'].split()),
                'sentence_count': len([s for s in clause_data['text'].split('.') if s.strip()]),
                'complexity_score': classification.get('complexity_score', 0.0),
                'mandatory_language': classification.get('has_mandatory_language', False),
                'penalty_clause': classification.get('has_penalties', False),
                'confidence': classification.get('confidence', 0.0),
                'entities': entities,
                'classification_details': classification
            }
            
            extracted_clauses.append(clause_record)
            total_confidence += clause_record['confidence']
        
        # Calculate overall confidence
        overall_confidence = total_confidence / len(extracted_clauses) if extracted_clauses else 0.0
        
        return {
            'document_id': document_id,
            'clauses': extracted_clauses,
            'total_clauses': len(extracted_clauses),
            'overall_confidence': round(overall_confidence, 3),
            'extraction_method': 'langchain_with_classification',
            'processing_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _find_clause_pages(self, clause_text: str, pages: List[Dict]) -> List[int]:
        """Find which pages contain the clause text."""
        page_numbers = []
        
        # Take first 100 characters of clause for matching
        clause_snippet = clause_text[:100].strip()
        
        for page in pages:
            page_text = page.get('text', '')
            if clause_snippet in page_text:
                page_numbers.append(page.get('page_number', 0))
        
        return page_numbers if page_numbers else [1]  # Default to page 1 if not found
    
    def _store_extraction_results(self, document_id: str, extraction_results: Dict[str, Any]) -> None:
        """Store clause extraction results in database and S3."""
        try:
            # Store in S3
            document_storage.store_processed_document(
                extraction_results, document_id, 'clause_extraction'
            )
            
            # Store clauses in database
            clauses_data = []
            entities_data = []
            
            for clause in extraction_results['clauses']:
                # Prepare clause data for database
                clause_db_data = {
                    'clause_id': clause['clause_id'],
                    'document_id': clause['document_id'],
                    'processed_doc_id': f"proc_{document_id}",
                    'clause_number': clause['clause_number'],
                    'section_reference': clause['section_reference'],
                    'clause_title': clause['clause_title'],
                    'clause_text': clause['clause_text'],
                    'clause_type': clause['clause_type'],
                    'clause_subtype': clause['clause_subtype'],
                    'page_numbers': json.dumps(clause['page_numbers']),
                    'word_count': clause['word_count'],
                    'sentence_count': clause['sentence_count'],
                    'complexity_score': clause['complexity_score'],
                    'mandatory_language': clause['mandatory_language'],
                    'penalty_clause': clause['penalty_clause']
                }
                clauses_data.append(clause_db_data)
                
                # Prepare entities data
                for entity in clause.get('entities', []):
                    entity_db_data = {
                        'entity_id': generate_uuid(),
                        'clause_id': clause['clause_id'],
                        'entity_type': entity['entity_type'],
                        'entity_value': entity['entity_value'],
                        'entity_context': entity.get('context', ''),
                        'confidence_score': entity.get('confidence', 0.0),
                        'start_position': entity.get('start_position', 0),
                        'end_position': entity.get('end_position', 0),
                        'normalized_value': entity.get('normalized_value', ''),
                        'entity_metadata': json.dumps(entity.get('metadata', {}))
                    }
                    entities_data.append(entity_db_data)
            
            # Bulk insert clauses
            if clauses_data:
                db_connection.bulk_insert('CLAUSES', clauses_data, 'PROCESSED')
            
            # Bulk insert entities
            if entities_data:
                db_connection.bulk_insert('ENTITIES', entities_data, 'PROCESSED')
            
            logger.info(f"Stored {len(clauses_data)} clauses and {len(entities_data)} entities for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error storing extraction results: {e}")
            raise
    
    def _publish_extraction_event(self, document_id: str, status: str) -> None:
        """Publish clause extraction event to EventBridge."""
        try:
            from datetime import datetime, timezone
            
            event_detail = {
                'document_id': document_id,
                'status': status,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'pipeline_stage': 'clause_extraction'
            }
            
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'compliance.clause.extraction',
                        'DetailType': 'Clause Extraction Status Change',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': 'compliance-processing-bus'
                    }
                ]
            )
            
            logger.info(f"Published extraction event for document {document_id}: {status}")
            
        except Exception as e:
            logger.error(f"Failed to publish extraction event: {e}")


# Lambda handler function
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for clause extraction."""
    handler = ClauseExtractionHandler()
    
    # Process clause extraction
    return handler.process_clause_extraction(event)


# For testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'document_id': 'doc_20250726_test123',
        'source': 'compliance.document.ingestion',
        'detail-type': 'Document Processing Status Change'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
