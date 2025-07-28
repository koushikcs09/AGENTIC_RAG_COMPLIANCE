
"""
Analysis API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from common.database import db_connection
from common.utils import create_api_response

router = APIRouter()

@router.post("/analyze/{document_id}")
async def trigger_analysis(
    document_id: str,
    analysis_type: str = "full_compliance"
):
    try:
        # Trigger analysis (simplified)
        return create_api_response(
            success=True,
            data={
                "message": "Analysis trigger endpoint - implementation in progress",
                "document_id": document_id,
                "analysis_type": analysis_type,
                "status": "queued"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    try:
        query = "SELECT * FROM ANALYTICS.ANALYSIS_RESULTS WHERE analysis_id = %s"
        results = db_connection.execute_query(query, {'analysis_id': analysis_id})
        
        if not results:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return create_api_response(success=True, data=results[0])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
