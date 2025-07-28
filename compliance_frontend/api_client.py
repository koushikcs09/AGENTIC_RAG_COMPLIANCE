
"""
API client for communicating with the backend compliance mapping service.
"""

import requests
import time
import json
from typing import Dict, Any, Optional, List, Tuple
import logging
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIClient:
    """Client for backend API communication."""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.timeout = config.API_TIMEOUT
        self.session = requests.Session()
        
        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {method} {url}")
            return {"success": False, "error": {"message": "Request timeout"}}
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error for {method} {url}")
            return {"success": False, "error": {"message": "Connection error - backend service unavailable"}}
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {method} {url}: {e}")
            try:
                error_data = response.json()
                return {"success": False, "error": error_data.get("error", {"message": str(e)})}
            except:
                return {"success": False, "error": {"message": f"HTTP {response.status_code}: {str(e)}"}}
        except Exception as e:
            logger.error(f"Unexpected error for {method} {url}: {e}")
            return {"success": False, "error": {"message": f"Unexpected error: {str(e)}"}}
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        return self._make_request("GET", "/health")
    
    def upload_document(self, file_content: bytes, filename: str, 
                       document_type: str = "vendor_contract") -> Dict[str, Any]:
        """Upload a document for analysis."""
        # Remove Content-Type header for file upload
        headers = dict(self.session.headers)
        if 'Content-Type' in headers:
            del headers['Content-Type']
        
        files = {
            'file': (filename, file_content, 'application/pdf')
        }
        
        data = {
            'document_type': document_type
        }
        
        try:
            url = f"{self.base_url}{config.ENDPOINTS['upload']}"
            response = requests.post(
                url=url,
                files=files,
                data=data,
                headers={k: v for k, v in headers.items() if k != 'Content-Type'},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return {"success": False, "error": {"message": f"Upload failed: {str(e)}"}}
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document information."""
        endpoint = f"{config.ENDPOINTS['document']}/{document_id}"
        return self._make_request("GET", endpoint)
    
    def list_documents(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """List uploaded documents."""
        endpoint = f"{config.ENDPOINTS['document']}?page={page}&limit={limit}"
        return self._make_request("GET", endpoint)
    
    def trigger_analysis(self, document_id: str, 
                        analysis_type: str = "full_compliance") -> Dict[str, Any]:
        """Trigger compliance analysis for a document."""
        endpoint = f"{config.ENDPOINTS['analyze']}/{document_id}"
        data = {"analysis_type": analysis_type}
        return self._make_request("POST", endpoint, json=data)
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis results."""
        endpoint = f"{config.ENDPOINTS['results']}/{analysis_id}/results"
        return self._make_request("GET", endpoint)
    
    def generate_report(self, analysis_id: str, report_type: str = "executive_summary",
                       format: str = "pdf") -> Dict[str, Any]:
        """Generate compliance report."""
        data = {
            "analysis_id": analysis_id,
            "report_type": report_type,
            "format": format
        }
        return self._make_request("POST", config.ENDPOINTS['reports'] + "/generate", json=data)
    
    def download_report(self, report_id: str) -> Dict[str, Any]:
        """Download generated report."""
        endpoint = f"{config.ENDPOINTS['reports']}/{report_id}/download"
        return self._make_request("GET", endpoint)
    
    def poll_analysis_status(self, analysis_id: str, 
                           callback: Optional[callable] = None) -> Dict[str, Any]:
        """Poll analysis status until completion."""
        attempts = 0
        max_attempts = config.MAX_POLLING_ATTEMPTS
        
        while attempts < max_attempts:
            result = self.get_analysis_results(analysis_id)
            
            if result.get("success"):
                data = result.get("data", {})
                status = data.get("status", "unknown")
                
                if callback:
                    callback(status, data)
                
                if status in ["completed", "failed", "error"]:
                    return result
            
            time.sleep(config.POLLING_INTERVAL)
            attempts += 1
        
        return {
            "success": False,
            "error": {"message": "Analysis polling timeout"}
        }

# Global API client instance
api_client = APIClient()

# Mock data for demonstration (since backend is still in development)
class MockAPIClient:
    """Mock API client for demonstration purposes."""
    
    def __init__(self):
        self.documents = {}
        self.analyses = {}
        self.reports = {}
    
    def health_check(self) -> Dict[str, Any]:
        return {
            "success": True,
            "data": {"status": "healthy", "environment": "development"}
        }
    
    def upload_document(self, file_content: bytes, filename: str, 
                       document_type: str = "vendor_contract") -> Dict[str, Any]:
        import uuid
        from datetime import datetime
        
        document_id = f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        self.documents[document_id] = {
            "document_id": document_id,
            "filename": filename,
            "size": len(file_content),
            "document_type": document_type,
            "status": "uploaded",
            "upload_timestamp": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": {
                "document_id": document_id,
                "message": "Document uploaded successfully",
                "filename": filename,
                "size": len(file_content)
            }
        }
    
    def trigger_analysis(self, document_id: str, 
                        analysis_type: str = "full_compliance") -> Dict[str, Any]:
        import uuid
        from datetime import datetime
        
        analysis_id = f"analysis_{datetime.now().strftime('%Y%m%d%H%M%S')}_{str(uuid.uuid4())[:8]}"
        
        self.analyses[analysis_id] = {
            "analysis_id": analysis_id,
            "document_id": document_id,
            "analysis_type": analysis_type,
            "status": "processing",
            "progress": 0,
            "created_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": {
                "analysis_id": analysis_id,
                "status": "started",
                "message": "Analysis started successfully"
            }
        }
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        import random
        from datetime import datetime
        
        if analysis_id not in self.analyses:
            return {"success": False, "error": {"message": "Analysis not found"}}
        
        analysis = self.analyses[analysis_id]
        
        # Simulate progress
        if analysis["status"] == "processing":
            analysis["progress"] = min(100, analysis["progress"] + random.randint(5, 20))
            
            if analysis["progress"] >= 100:
                analysis["status"] = "completed"
                # Generate mock results
                analysis["results"] = self._generate_mock_results()
        
        return {
            "success": True,
            "data": analysis
        }
    
    def _generate_mock_results(self) -> Dict[str, Any]:
        """Generate mock compliance mapping results."""
        mock_mappings = [
            {
                "tc_reference": "Section 5.2 - Safety Management",
                "vendor_clause": "Contractor shall implement comprehensive safety management systems in accordance with industry best practices.",
                "compliance_flag": "🟢 Compliant",
                "compliance_score": 0.95,
                "suggested_action": "Ensure alignment with specific mining safety regulations (WHS Mines Regulations 2022)",
                "risk_level": "low",
                "regulation_references": ["Work Health and Safety (Mines) Regulations 2022 (WA)", "Mining Act 1978 (WA)"]
            },
            {
                "tc_reference": "Section 8.1 - Environmental Obligations",
                "vendor_clause": "Services will be performed in accordance with environmental standards.",
                "compliance_flag": "🟡 Partial Compliance",
                "compliance_score": 0.65,
                "suggested_action": "Specify compliance with EPBC Act and state environmental protection requirements",
                "risk_level": "medium",
                "regulation_references": ["Environment Protection and Biodiversity Conservation Act 1999", "Environmental Protection Act 1994 (Qld)"]
            },
            {
                "tc_reference": "Section 12.3 - Insurance Requirements",
                "vendor_clause": "Contractor maintains public liability insurance of $10 million.",
                "compliance_flag": "🔴 Non-Compliant",
                "compliance_score": 0.30,
                "suggested_action": "Increase coverage to minimum $20-30 million as per mining industry standards",
                "risk_level": "high",
                "regulation_references": ["Mining Act 1978 (WA)", "Work Health and Safety Act 2011"]
            },
            {
                "tc_reference": "Section 15.1 - Emergency Response",
                "vendor_clause": "Contractor will follow site emergency procedures.",
                "compliance_flag": "🟡 Partial Compliance",
                "compliance_score": 0.70,
                "suggested_action": "Specify detailed emergency response plan requirements and incident reporting procedures",
                "risk_level": "medium",
                "regulation_references": ["Work Health and Safety (Mines) Regulations 2022", "Mining Management Act 2001 (NT)"]
            },
            {
                "tc_reference": "Section 6.4 - Personnel Competency",
                "vendor_clause": "All personnel will be appropriately qualified and experienced.",
                "compliance_flag": "🟠 Requires Attention",
                "compliance_score": 0.55,
                "suggested_action": "Specify required licenses, certifications, and competency standards for mining operations",
                "risk_level": "medium",
                "regulation_references": ["Work Health and Safety (Mines) Regulations 2022", "Mining Act 1992 (NSW)"]
            }
        ]
        
        audit_checklist = [
            {
                "category": "Safety Management",
                "items": [
                    "Verify contractor safety management system documentation",
                    "Confirm personnel competency certificates and licenses",
                    "Review emergency response procedures alignment",
                    "Check incident reporting protocols"
                ]
            },
            {
                "category": "Environmental Compliance",
                "items": [
                    "Validate environmental duty of care provisions",
                    "Review waste management procedures",
                    "Confirm cultural heritage protection measures",
                    "Check rehabilitation contribution agreements"
                ]
            },
            {
                "category": "Insurance and Risk",
                "items": [
                    "Verify insurance coverage amounts and scope",
                    "Review indemnity and liability provisions",
                    "Confirm workers' compensation coverage",
                    "Check professional indemnity requirements"
                ]
            }
        ]
        
        return {
            "compliance_mappings": mock_mappings,
            "audit_checklist": audit_checklist,
            "overall_compliance_score": 0.63,
            "risk_summary": {
                "high_risk_items": 1,
                "medium_risk_items": 3,
                "low_risk_items": 1
            },
            "recommendations": [
                "Increase insurance coverage to industry standards",
                "Specify detailed environmental compliance requirements",
                "Add specific personnel competency requirements",
                "Include comprehensive emergency response provisions"
            ]
        }

# Use mock client for demonstration
mock_api_client = MockAPIClient()
