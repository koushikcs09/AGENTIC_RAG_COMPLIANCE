
"""
AWS Lambda function for report generation pipeline.
"""

import json
import logging
import boto3
from typing import Dict, Any
import sys
import os

sys.path.append('/opt/python')
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from common.config import config
from common.database import db_connection
from common.s3_client import document_storage
from common.utils import create_api_response, timing_decorator, generate_report_id
from report_generator import ReportGenerator

logger = logging.getLogger(__name__)

class ReportGenerationHandler:
    def __init__(self):
        self.report_generator = ReportGenerator()
    
    @timing_decorator
    def generate_report(self, event: Dict[str, Any]) -> Dict[str, Any]:
        try:
            analysis_id = event.get('analysis_id')
            report_type = event.get('report_type', 'executive_summary')
            format_type = event.get('format', 'pdf')
            
            # Get analysis results
            analysis_query = """
            SELECT * FROM ANALYTICS.ANALYSIS_RESULTS 
            WHERE analysis_id = %s
            """
            analysis_results = db_connection.execute_query(analysis_query, {'analysis_id': analysis_id})
            
            if not analysis_results:
                raise ValueError(f"Analysis not found: {analysis_id}")
            
            analysis_data = analysis_results[0]
            
            # Generate report
            report_content = self.report_generator.generate_report(
                analysis_data, report_type, format_type
            )
            
            # Store report
            report_id = generate_report_id()
            document_storage.store_report(
                report_content, report_id, report_type, format_type
            )
            
            # Store report metadata
            report_metadata = {
                'report_id': report_id,
                'analysis_id': analysis_id,
                'report_type': report_type,
                'report_format': format_type,
                'file_size_bytes': len(report_content)
            }
            
            db_connection.execute_non_query("""
                INSERT INTO ANALYTICS.REPORTS 
                (report_id, analysis_id, report_type, report_format, file_size_bytes)
                VALUES (%(report_id)s, %(analysis_id)s, %(report_type)s, %(report_format)s, %(file_size_bytes)s)
            """, report_metadata)
            
            return create_api_response(
                success=True,
                data={
                    'report_id': report_id,
                    'analysis_id': analysis_id,
                    'report_type': report_type,
                    'format': format_type,
                    'file_size': len(report_content),
                    'status': 'completed'
                }
            )
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return create_api_response(
                success=False,
                error={'code': 'REPORT_GENERATION_ERROR', 'message': str(e)}
            )

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    handler = ReportGenerationHandler()
    return handler.generate_report(event)
