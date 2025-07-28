
"""
AWS S3 client utilities for document storage and retrieval.
"""

import logging
import boto3
import hashlib
import mimetypes
from typing import Dict, List, Optional, BinaryIO, Tuple
from botocore.exceptions import ClientError, NoCredentialsError
from .config import config

logger = logging.getLogger(__name__)


class S3Client:
    """AWS S3 client for document storage operations."""
    
    def __init__(self):
        try:
            self.s3_client = boto3.client('s3', region_name=config.aws.region)
            self.s3_resource = boto3.resource('s3', region_name=config.aws.region)
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
    
    def upload_file(self, file_obj: BinaryIO, bucket: str, key: str, 
                   metadata: Optional[Dict] = None) -> Dict:
        """Upload file to S3 bucket."""
        try:
            # Calculate file hash
            file_content = file_obj.read()
            file_obj.seek(0)  # Reset file pointer
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Determine content type
            content_type = mimetypes.guess_type(key)[0] or 'application/octet-stream'
            
            # Prepare upload parameters
            upload_params = {
                'Bucket': bucket,
                'Key': key,
                'Body': file_obj,
                'ContentType': content_type,
                'Metadata': metadata or {}
            }
            
            # Add server-side encryption
            upload_params['ServerSideEncryption'] = 'AES256'
            
            # Upload file
            self.s3_client.upload_fileobj(**upload_params)
            
            # Get file size
            file_size = len(file_content)
            
            logger.info(f"File uploaded successfully: s3://{bucket}/{key}")
            
            return {
                'bucket': bucket,
                'key': key,
                'size': file_size,
                'hash': file_hash,
                'content_type': content_type,
                'url': f"s3://{bucket}/{key}"
            }
            
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise
    
    def download_file(self, bucket: str, key: str) -> bytes:
        """Download file from S3 bucket."""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"File not found: s3://{bucket}/{key}")
                raise FileNotFoundError(f"File not found: s3://{bucket}/{key}")
            else:
                logger.error(f"S3 download error: {e}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise
    
    def get_file_metadata(self, bucket: str, key: str) -> Dict:
        """Get file metadata from S3."""
        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response['ContentType'],
                'metadata': response.get('Metadata', {}),
                'etag': response['ETag'].strip('"')
            }
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error(f"File not found: s3://{bucket}/{key}")
                raise FileNotFoundError(f"File not found: s3://{bucket}/{key}")
            else:
                logger.error(f"S3 metadata error: {e}")
                raise
    
    def delete_file(self, bucket: str, key: str) -> bool:
        """Delete file from S3 bucket."""
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"File deleted successfully: s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            return False
    
    def list_files(self, bucket: str, prefix: str = "", 
                  max_keys: int = 1000) -> List[Dict]:
        """List files in S3 bucket with optional prefix."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })
            
            return files
        except ClientError as e:
            logger.error(f"S3 list error: {e}")
            raise
    
    def generate_presigned_url(self, bucket: str, key: str, 
                             expiration: int = 3600, method: str = 'get_object') -> str:
        """Generate presigned URL for S3 object."""
        try:
            url = self.s3_client.generate_presigned_url(
                method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Presigned URL generation error: {e}")
            raise
    
    def copy_file(self, source_bucket: str, source_key: str,
                 dest_bucket: str, dest_key: str) -> bool:
        """Copy file between S3 locations."""
        try:
            copy_source = {'Bucket': source_bucket, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=dest_bucket,
                Key=dest_key,
                ServerSideEncryption='AES256'
            )
            logger.info(f"File copied: s3://{source_bucket}/{source_key} -> s3://{dest_bucket}/{dest_key}")
            return True
        except ClientError as e:
            logger.error(f"S3 copy error: {e}")
            return False
    
    def file_exists(self, bucket: str, key: str) -> bool:
        """Check if file exists in S3 bucket."""
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"S3 existence check error: {e}")
                raise


class DocumentStorage:
    """High-level document storage operations."""
    
    def __init__(self):
        self.s3_client = S3Client()
        self.raw_bucket = config.aws.s3_bucket_raw
        self.processed_bucket = config.aws.s3_bucket_processed
        self.reports_bucket = config.aws.s3_bucket_reports
    
    def store_raw_document(self, file_obj: BinaryIO, document_id: str, 
                          filename: str, metadata: Optional[Dict] = None) -> Dict:
        """Store raw document in S3."""
        key = f"documents/{document_id}/{filename}"
        
        upload_metadata = {
            'document-id': document_id,
            'original-filename': filename,
            'upload-timestamp': str(int(time.time()))
        }
        
        if metadata:
            upload_metadata.update({
                f"custom-{k}": str(v) for k, v in metadata.items()
            })
        
        return self.s3_client.upload_file(
            file_obj, self.raw_bucket, key, upload_metadata
        )
    
    def store_processed_document(self, content: str, document_id: str, 
                               processing_stage: str) -> Dict:
        """Store processed document content."""
        key = f"processed/{document_id}/{processing_stage}.json"
        
        import json
        from io import BytesIO
        
        content_bytes = json.dumps(content, indent=2).encode('utf-8')
        file_obj = BytesIO(content_bytes)
        
        metadata = {
            'document-id': document_id,
            'processing-stage': processing_stage,
            'content-type': 'application/json'
        }
        
        return self.s3_client.upload_file(
            file_obj, self.processed_bucket, key, metadata
        )
    
    def store_report(self, report_content: bytes, report_id: str, 
                    report_type: str, format: str) -> Dict:
        """Store generated report."""
        key = f"reports/{report_id}/{report_type}.{format}"
        
        from io import BytesIO
        file_obj = BytesIO(report_content)
        
        metadata = {
            'report-id': report_id,
            'report-type': report_type,
            'format': format,
            'generation-timestamp': str(int(time.time()))
        }
        
        return self.s3_client.upload_file(
            file_obj, self.reports_bucket, key, metadata
        )
    
    def get_raw_document(self, document_id: str, filename: str) -> bytes:
        """Retrieve raw document from S3."""
        key = f"documents/{document_id}/{filename}"
        return self.s3_client.download_file(self.raw_bucket, key)
    
    def get_processed_document(self, document_id: str, processing_stage: str) -> Dict:
        """Retrieve processed document content."""
        key = f"processed/{document_id}/{processing_stage}.json"
        content = self.s3_client.download_file(self.processed_bucket, key)
        
        import json
        return json.loads(content.decode('utf-8'))
    
    def get_report(self, report_id: str, report_type: str, format: str) -> bytes:
        """Retrieve generated report."""
        key = f"reports/{report_id}/{report_type}.{format}"
        return self.s3_client.download_file(self.reports_bucket, key)
    
    def cleanup_document_files(self, document_id: str) -> bool:
        """Clean up all files associated with a document."""
        try:
            # List and delete raw document files
            raw_files = self.s3_client.list_files(
                self.raw_bucket, f"documents/{document_id}/"
            )
            for file_info in raw_files:
                self.s3_client.delete_file(self.raw_bucket, file_info['key'])
            
            # List and delete processed document files
            processed_files = self.s3_client.list_files(
                self.processed_bucket, f"processed/{document_id}/"
            )
            for file_info in processed_files:
                self.s3_client.delete_file(self.processed_bucket, file_info['key'])
            
            logger.info(f"Cleaned up files for document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up document files: {e}")
            return False


# Global storage instance
import time
document_storage = DocumentStorage()
