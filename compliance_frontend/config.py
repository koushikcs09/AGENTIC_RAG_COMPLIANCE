
"""
Configuration settings for the Streamlit frontend application.
"""

import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # API Configuration
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    
    # Application Configuration
    APP_TITLE = os.getenv("APP_TITLE", "Agentic Compliance Mapping System")
    APP_DESCRIPTION = os.getenv("APP_DESCRIPTION", "AI-powered compliance mapping for Australian mining regulations")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    SUPPORTED_FILE_TYPES = ["pdf"]
    
    # UI Configuration
    THEME_CONFIG = {
        "primaryColor": os.getenv("THEME_PRIMARY_COLOR", "#1f77b4"),
        "backgroundColor": os.getenv("THEME_BACKGROUND_COLOR", "#ffffff"),
        "secondaryBackgroundColor": os.getenv("THEME_SECONDARY_BACKGROUND_COLOR", "#f0f2f6"),
        "textColor": os.getenv("THEME_TEXT_COLOR", "#262730")
    }
    
    # Processing Configuration
    POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL", "2"))
    MAX_POLLING_ATTEMPTS = int(os.getenv("MAX_POLLING_ATTEMPTS", "150"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
    
    # API Endpoints
    ENDPOINTS = {
        "upload": "/api/v1/documents/upload",
        "document": "/api/v1/documents",
        "analyze": "/api/v1/analysis/analyze",
        "results": "/api/v1/analysis",
        "reports": "/api/v1/reports"
    }
    
    @classmethod
    def get_endpoint_url(cls, endpoint: str, *args) -> str:
        """Get full URL for an API endpoint."""
        endpoint_path = cls.ENDPOINTS.get(endpoint, "")
        if args:
            endpoint_path = endpoint_path.rstrip('/') + '/' + '/'.join(str(arg) for arg in args)
        return f"{cls.API_BASE_URL}{endpoint_path}"

# Global config instance
config = Config()
