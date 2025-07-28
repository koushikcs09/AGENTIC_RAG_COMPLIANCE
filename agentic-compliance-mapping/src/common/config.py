
"""
Configuration management for the Agentic Compliance-Mapping System.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """Environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class AWSConfig:
    """AWS configuration settings."""
    region: str = "ap-southeast-2"
    s3_bucket_raw: str = "compliance-docs-raw"
    s3_bucket_processed: str = "compliance-docs-processed"
    s3_bucket_reports: str = "compliance-reports"
    textract_role_arn: str = ""
    lambda_timeout: int = 900
    lambda_memory: int = 3008


@dataclass
class SnowflakeConfig:
    """Snowflake configuration settings."""
    account: str = ""
    user: str = ""
    password: str = ""
    warehouse: str = "COMPLIANCE_WH"
    database: str = "COMPLIANCE_DB"
    schema: str = "RAW"
    role: str = "COMPLIANCE_ROLE"
    embedding_model: str = "snowflake-arctic-embed-m"
    llm_model: str = "mixtral-8x7b"


@dataclass
class ProcessingConfig:
    """Document processing configuration."""
    max_file_size_mb: int = 50
    max_pages: int = 100
    ocr_confidence_threshold: float = 0.8
    similarity_threshold: float = 0.75
    batch_size: int = 100
    max_concurrent_jobs: int = 10


@dataclass
class AgentConfig:
    """Agent configuration settings."""
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout_seconds: int = 300
    retry_attempts: int = 3
    agent_types: list = None

    def __post_init__(self):
        if self.agent_types is None:
            self.agent_types = [
                "safety_compliance",
                "environmental_compliance", 
                "operational_compliance",
                "legal_analysis",
                "risk_assessment"
            ]


class Config:
    """Main configuration class."""
    
    def __init__(self, environment: Optional[Environment] = None):
        self.environment = environment or self._detect_environment()
        self.aws = self._load_aws_config()
        self.snowflake = self._load_snowflake_config()
        self.processing = self._load_processing_config()
        self.agents = self._load_agent_config()
        
    def _detect_environment(self) -> Environment:
        """Detect current environment from environment variables."""
        env_name = os.getenv("ENVIRONMENT", "development").lower()
        try:
            return Environment(env_name)
        except ValueError:
            return Environment.DEVELOPMENT
    
    def _load_aws_config(self) -> AWSConfig:
        """Load AWS configuration from environment variables."""
        return AWSConfig(
            region=os.getenv("AWS_REGION", "ap-southeast-2"),
            s3_bucket_raw=os.getenv("S3_BUCKET_RAW", "compliance-docs-raw"),
            s3_bucket_processed=os.getenv("S3_BUCKET_PROCESSED", "compliance-docs-processed"),
            s3_bucket_reports=os.getenv("S3_BUCKET_REPORTS", "compliance-reports"),
            textract_role_arn=os.getenv("TEXTRACT_ROLE_ARN", ""),
            lambda_timeout=int(os.getenv("LAMBDA_TIMEOUT", "900")),
            lambda_memory=int(os.getenv("LAMBDA_MEMORY", "3008"))
        )
    
    def _load_snowflake_config(self) -> SnowflakeConfig:
        """Load Snowflake configuration from environment variables."""
        return SnowflakeConfig(
            account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
            user=os.getenv("SNOWFLAKE_USER", ""),
            password=os.getenv("SNOWFLAKE_PASSWORD", ""),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "COMPLIANCE_WH"),
            database=os.getenv("SNOWFLAKE_DATABASE", "COMPLIANCE_DB"),
            schema=os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
            role=os.getenv("SNOWFLAKE_ROLE", "COMPLIANCE_ROLE"),
            embedding_model=os.getenv("SNOWFLAKE_EMBEDDING_MODEL", "snowflake-arctic-embed-m"),
            llm_model=os.getenv("SNOWFLAKE_LLM_MODEL", "mixtral-8x7b")
        )
    
    def _load_processing_config(self) -> ProcessingConfig:
        """Load processing configuration from environment variables."""
        return ProcessingConfig(
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
            max_pages=int(os.getenv("MAX_PAGES", "100")),
            ocr_confidence_threshold=float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.8")),
            similarity_threshold=float(os.getenv("SIMILARITY_THRESHOLD", "0.75")),
            batch_size=int(os.getenv("BATCH_SIZE", "100")),
            max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", "10"))
        )
    
    def _load_agent_config(self) -> AgentConfig:
        """Load agent configuration from environment variables."""
        return AgentConfig(
            temperature=float(os.getenv("AGENT_TEMPERATURE", "0.1")),
            max_tokens=int(os.getenv("AGENT_MAX_TOKENS", "4000")),
            timeout_seconds=int(os.getenv("AGENT_TIMEOUT", "300")),
            retry_attempts=int(os.getenv("AGENT_RETRY_ATTEMPTS", "3"))
        )
    
    def get_database_url(self) -> str:
        """Get Snowflake database connection URL."""
        return (
            f"snowflake://{self.snowflake.user}:{self.snowflake.password}"
            f"@{self.snowflake.account}/{self.snowflake.database}"
            f"/{self.snowflake.schema}?warehouse={self.snowflake.warehouse}"
            f"&role={self.snowflake.role}"
        )
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT


# Global configuration instance
config = Config()
