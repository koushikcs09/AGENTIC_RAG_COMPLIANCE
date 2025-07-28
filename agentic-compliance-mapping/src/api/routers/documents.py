
"""
Document management API endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from common.database import document_repository
from common.utils import create_api_response, validate_pdf_file

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "vendor_contract",
    metadata: Optional[str] = None
):
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate PDF
        validation = validate_pdf_file(file_content)
        if not validation['is_valid']:
            raise HTTPException(status_code=400, detail=validation['error_message'])
        
        # Process upload (simplified)
        return create_api_response(
            success=True,
            data={
                "message": "Document upload endpoint - implementation in progress",
                "filename": file.filename,
                "size": len(file_content),
                "document_type": document_type
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}")
async def get_document(document_id: str):
    try:
        document = document_repository.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return create_api_response(success=True, data=document)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_documents(page: int = 1, limit: int = 20):
    try:
        documents, total = document_repository.list_documents(page=page, limit=limit)
        
        return create_api_response(
            success=True,
            data={
                "documents": documents,
                "pagination": {
                    "current_page": page,
                    "total_items": total,
                    "items_per_page": limit
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
