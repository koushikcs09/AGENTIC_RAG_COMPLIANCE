
"""
Report generation utilities.
"""

import json
from typing import Dict, Any
from datetime import datetime

class ReportGenerator:
    def generate_report(self, analysis_data: Dict, report_type: str, format_type: str) -> bytes:
        if report_type == 'executive_summary':
            return self._generate_executive_summary(analysis_data, format_type)
        elif report_type == 'detailed_audit':
            return self._generate_detailed_audit(analysis_data, format_type)
        else:
            return self._generate_basic_report(analysis_data, format_type)
    
    def _generate_executive_summary(self, analysis_data: Dict, format_type: str) -> bytes:
        summary = {
            'title': 'Compliance Analysis Executive Summary',
            'analysis_id': analysis_data.get('ANALYSIS_ID'),
            'document_id': analysis_data.get('DOCUMENT_ID'),
            'overall_risk_score': analysis_data.get('OVERALL_RISK_SCORE', 0.5),
            'analysis_timestamp': analysis_data.get('ANALYSIS_TIMESTAMP'),
            'key_findings': [
                'Compliance analysis completed',
                f"Overall risk score: {analysis_data.get('OVERALL_RISK_SCORE', 0.5):.2f}",
                'Detailed recommendations available in full report'
            ],
            'recommendations': [
                'Review identified compliance gaps',
                'Implement recommended improvements',
                'Schedule regular compliance audits'
            ]
        }
        
        if format_type == 'json':
            return json.dumps(summary, indent=2).encode('utf-8')
        else:
            # Simple text format
            text_report = f"""
COMPLIANCE ANALYSIS EXECUTIVE SUMMARY
=====================================

Analysis ID: {summary['analysis_id']}
Document ID: {summary['document_id']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL RISK SCORE: {summary['overall_risk_score']:.2f}

KEY FINDINGS:
{chr(10).join(f"• {finding}" for finding in summary['key_findings'])}

RECOMMENDATIONS:
{chr(10).join(f"• {rec}" for rec in summary['recommendations'])}
            """
            return text_report.encode('utf-8')
    
    def _generate_detailed_audit(self, analysis_data: Dict, format_type: str) -> bytes:
        # Simplified detailed report
        return self._generate_executive_summary(analysis_data, format_type)
    
    def _generate_basic_report(self, analysis_data: Dict, format_type: str) -> bytes:
        return self._generate_executive_summary(analysis_data, format_type)
