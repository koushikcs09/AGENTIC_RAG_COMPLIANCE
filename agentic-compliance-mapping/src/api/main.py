
"""
FastAPI main application for compliance mapping API.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../'))

from common.config import config
from common.database import document_repository
from common.utils import create_api_response, validate_pdf_file
from api.routers import documents, analysis, reports

app = FastAPI(
    title="Agentic Compliance-Mapping API",
    description="AI-powered compliance mapping system for Australian mining regulations",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])

@app.get("/")
async def root():
    return create_api_response(
        success=True,
        data={"message": "Agentic Compliance-Mapping API", "version": "1.0.0"}
    )

@app.get("/health")
async def health_check():
    return create_api_response(
        success=True,
        data={"status": "healthy", "environment": config.environment.value}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
