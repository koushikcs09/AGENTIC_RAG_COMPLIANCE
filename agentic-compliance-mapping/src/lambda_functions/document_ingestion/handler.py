
"""
AWS Lambda function for document ingestion pipeline.
Handles PDF upload, OCR processing, and metadata extraction.
"""

import json
import logging
import boto3
from typing import Dict, Any
import sys
import os

# Add src to path for imports
sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from common.config import config
from common.database import document_repository, db_connection
from common.s3_client import document_storage
from common.utils import (
    generate_document_id, validate_pdf_file, create_api_response,
    timing_decorator, retry_with_backoff
)
from pdf_processor import PDFProcessor
from metadata_extractor import MetadataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients
eventbridge = boto3.client('events', region_name=config.aws.region)
textract = boto3.client('textract', region_name=config.aws.region)


class DocumentIngestionHandler:
    """Handler for document ingestion operations."""
    
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.metadata_extractor = MetadataExtractor()
    
    @timing_decorator
    @retry_with_backoff(max_retries=2)
    def process_document_upload(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process document upload from API Gateway."""
        try:
            # Extract file information from event
            file_content = self._extract_file_content(event)
            filename = event.get('filename', 'document.pdf')
            document_type = event.get('document_type', 'vendor_contract')
            metadata = event.get('metadata', {})
            
            # Validate PDF file
            validation_result = validate_pdf_file(file_content)
            if not validation_result['is_valid']:
                return create_api_response(
                    success=False,
                    error={
                        'code': 'INVALID_FILE',
                        'message': validation_result['error_message']
                    }
                )
            
            # Generate document ID
            document_id = generate_document_id()
            
            # Store raw document in S3
            from io import BytesIO
            file_obj = BytesIO(file_content)
            s3_result = document_storage.store_raw_document(
                file_obj, document_id, filename, metadata
            )
            
            # Create database record
            document_data = {
                'document_id': document_id,
                'file_name': filename,
                'file_path': s3_result['url'],
                'file_size_bytes': s3_result['size'],
                'file_hash': s3_result['hash'],
                'content_type': s3_result['content_type'],
                'document_type': document_type,
                'raw_content': '',  # Will be populated after OCR
                'metadata': json.dumps({
                    **metadata,
                    **validation_result['metadata']
                }),
                'created_by': event.get('user_id', 'system')
            }
            
            document_repository.create_document(document_data)
            
            # Trigger OCR processing
            self._trigger_ocr_processing(document_id, s3_result['bucket'], s3_result['key'])
            
            # Publish event for next pipeline stage
            self._publish_ingestion_event(document_id, 'uploaded')
            
            return create_api_response(
                success=True,
                data={
                    'document_id': document_id,
                    'file_name': filename,
                    'file_size': s3_result['size'],
                    'document_type': document_type,
                    'processing_status': 'uploaded',
                    'estimated_processing_time': 300
                },
                message="Document uploaded successfully"
            )
            
        except Exception as e:
            logger.error(f"Document upload processing error: {e}")
            return create_api_response(
                success=False,
                error={
                    'code': 'PROCESSING_ERROR',
                    'message': f"Failed to process document upload: {str(e)}"
                }
            )
    
    @timing_decorator
    def process_ocr_completion(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process OCR completion from AWS Textract."""
        try:
            # Extract job information from event
            job_id = event.get('job_id')
            document_id = event.get('document_id')
            
            if not job_id or not document_id:
                raise ValueError("Missing job_id or document_id in event")
            
            # Get OCR results from Textract
            ocr_results = self._get_textract_results(job_id)
            
            # Process OCR results
            processed_content = self.pdf_processor.process_textract_results(ocr_results)
            
            # Extract metadata
            metadata = self.metadata_extractor.extract_from_content(processed_content)
            
            # Update document in database
            document_repository.update_document_status(
                document_id, 
                'processing',
                {
                    'ocr_confidence': processed_content.get('confidence', 0.0),
                    'total_pages': len(processed_content.get('pages', [])),
                    'extraction_metadata': metadata
                }
            )
            
            # Store processed content in S3
            document_storage.store_processed_document(
                processed_content, document_id, 'ocr_results'
            )
            
            # Publish event for clause extraction
            self._publish_ingestion_event(document_id, 'ocr_completed')
            
            return create_api_response(
                success=True,
                data={
                    'document_id': document_id,
                    'processing_status': 'ocr_completed',
                    'pages_processed': len(processed_content.get('pages', [])),
                    'confidence_score': processed_content.get('confidence', 0.0)
                }
            )
            
        except Exception as e:
            logger.error(f"OCR completion processing error: {e}")
            # Update document status to failed
            if 'document_id' in locals():
                document_repository.update_document_status(document_id, 'failed')
            
            return create_api_response(
                success=False,
                error={
                    'code': 'OCR_PROCESSING_ERROR',
                    'message': f"Failed to process OCR results: {str(e)}"
                }
            )
    
    def _extract_file_content(self, event: Dict[str, Any]) -> bytes:
        """Extract file content from Lambda event."""
        # Handle different event sources (API Gateway, S3, etc.)
        if 'body' in event:
            # API Gateway event with base64 encoded body
            import base64
            body = event['body']
            if event.get('isBase64Encoded', False):
                return base64.b64decode(body)
            else:
                return body.encode('utf-8')
        elif 'Records' in event:
            # S3 event - download file from S3
            record = event['Records'][0]
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            return document_storage.s3_client.download_file(bucket, key)
        else:
            raise ValueError("Unable to extract file content from event")
    
    def _trigger_ocr_processing(self, document_id: str, bucket: str, key: str) -> str:
        """Trigger AWS Textract OCR processing."""
        try:
            response = textract.start_document_text_detection(
                DocumentLocation={
                    'S3Object': {
                        'Bucket': bucket,
                        'Name': key
                    }
                },
                NotificationChannel={
                    'SNSTopicArn': os.getenv('OCR_COMPLETION_TOPIC_ARN'),
                    'RoleArn': config.aws.textract_role_arn
                },
                ClientRequestToken=document_id
            )
            
            job_id = response['JobId']
            logger.info(f"Started Textract job {job_id} for document {document_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to start Textract job: {e}")
            raise
    
    def _get_textract_results(self, job_id: str) -> Dict[str, Any]:
        """Get results from completed Textract job."""
        try:
            response = textract.get_document_text_detection(JobId=job_id)
            
            # Handle paginated results
            blocks = response.get('Blocks', [])
            next_token = response.get('NextToken')
            
            while next_token:
                response = textract.get_document_text_detection(
                    JobId=job_id,
                    NextToken=next_token
                )
                blocks.extend(response.get('Blocks', []))
                next_token = response.get('NextToken')
            
            return {
                'job_id': job_id,
                'job_status': response.get('JobStatus'),
                'blocks': blocks,
                'document_metadata': response.get('DocumentMetadata', {})
            }
            
        except Exception as e:
            logger.error(f"Failed to get Textract results: {e}")
            raise
    
    def _publish_ingestion_event(self, document_id: str, status: str) -> None:
        """Publish document ingestion event to EventBridge."""
        try:
            event_detail = {
                'document_id': document_id,
                'status': status,
                'timestamp': json.dumps(datetime.now(timezone.utc), default=str),
                'pipeline_stage': 'document_ingestion'
            }
            
            eventbridge.put_events(
                Entries=[
                    {
                        'Source': 'compliance.document.ingestion',
                        'DetailType': 'Document Processing Status Change',
                        'Detail': json.dumps(event_detail),
                        'EventBusName': 'compliance-processing-bus'
                    }
                ]
            )
            
            logger.info(f"Published ingestion event for document {document_id}: {status}")
            
        except Exception as e:
            logger.error(f"Failed to publish ingestion event: {e}")
            # Don't raise - this is not critical for the main flow


# Lambda handler functions
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda handler for document ingestion."""
    handler = DocumentIngestionHandler()
    
    # Determine event type and route accordingly
    if 'source' in event and event['source'] == 'aws.textract':
        # OCR completion event from Textract
        return handler.process_ocr_completion(event)
    else:
        # Document upload event
        return handler.process_document_upload(event)


# For testing
if __name__ == "__main__":
    # Test event
    test_event = {
        'filename': 'test_contract.pdf',
        'document_type': 'vendor_contract',
        'metadata': {'jurisdiction': 'wa', 'tags': ['mining', 'safety']},
        'user_id': 'test_user'
    }
    
    result = lambda_handler(test_event, None)
    print(json.dumps(result, indent=2))
