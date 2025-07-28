
# Agentic Compliance-Mapping System - Backend Implementation

## Overview

This is the complete backend implementation for the Agentic Compliance-Mapping System, designed to automate compliance verification for Australian mining regulations using AI-powered document processing and analysis.

## Architecture

The system implements a serverless, event-driven architecture with 5 core pipelines:

1. **Document Ingestion Pipeline** - PDF processing with OCR and text extraction
2. **Clause Extraction Pipeline** - AI-powered clause identification and classification  
3. **Semantic Alignment & Mapping Pipeline** - Vector-based similarity matching
4. **Agentic Reasoning Loop** - Multi-agent compliance analysis
5. **Audit & Reporting Pipeline** - Comprehensive report generation

## Technology Stack

- **Backend**: AWS Lambda, API Gateway, S3, EventBridge
- **Database**: Snowflake with Vector Store and Cortex AI
- **AI Framework**: LangChain with custom agents
- **Document Processing**: AWS Textract, PyPDF2
- **API**: FastAPI with async support

## Quick Start

### Prerequisites

- AWS Account with appropriate permissions
- Snowflake account with Cortex capabilities
- Python 3.9+
- Terraform >= 1.0

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd agentic-compliance-mapping

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your AWS and Snowflake credentials

# Deploy infrastructure
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### Environment Variables

Create a `.env` file with:

```bash
# AWS Configuration
AWS_REGION=ap-southeast-2
S3_BUCKET_RAW=compliance-docs-raw
S3_BUCKET_PROCESSED=compliance-docs-processed
S3_BUCKET_REPORTS=compliance-reports

# Snowflake Configuration
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_WAREHOUSE=COMPLIANCE_WH
SNOWFLAKE_DATABASE=COMPLIANCE_DB

# Processing Configuration
MAX_FILE_SIZE_MB=50
MAX_PAGES=100
SIMILARITY_THRESHOLD=0.75
```

## Project Structure

```
agentic-compliance-mapping/
├── src/
│   ├── common/                 # Shared utilities and configuration
│   ├── lambda_functions/       # AWS Lambda function implementations
│   │   ├── document_ingestion/
│   │   ├── clause_extraction/
│   │   ├── semantic_mapping/
│   │   ├── agentic_reasoning/
│   │   └── report_generation/
│   └── api/                   # FastAPI application
├── infrastructure/
│   └── terraform/             # Infrastructure as Code
├── scripts/                   # Deployment and utility scripts
├── tests/                     # Test suites
└── docs/                      # Documentation
```

## API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload document for processing
- `GET /api/v1/documents/{document_id}` - Get document information
- `GET /api/v1/documents` - List documents with pagination

### Analysis
- `POST /api/v1/analysis/analyze/{document_id}` - Trigger compliance analysis
- `GET /api/v1/analysis/{analysis_id}/results` - Get analysis results
- `GET /api/v1/analysis/{analysis_id}/compliance-mappings` - Get detailed mappings

### Reports
- `POST /api/v1/reports/generate` - Generate compliance report
- `GET /api/v1/reports/{report_id}/download` - Download generated report

## Lambda Functions

### 1. Document Ingestion (`document_ingestion/`)
- Handles PDF upload and validation
- Integrates with AWS Textract for OCR
- Extracts metadata and document structure
- Publishes events for next pipeline stage

### 2. Clause Extraction (`clause_extraction/`)
- Uses LangChain agents for intelligent clause identification
- Classifies clauses into compliance categories
- Extracts entities and regulatory references
- Stores structured clause data

### 3. Semantic Mapping (`semantic_mapping/`)
- Generates embeddings using Snowflake Cortex
- Performs vector similarity search against regulations
- Creates compliance mappings with confidence scores
- Optimizes for Australian mining regulations

### 4. Agentic Reasoning (`agentic_reasoning/`)
- Multi-agent analysis system:
  - Safety Compliance Agent
  - Environmental Compliance Agent  
  - Risk Assessment Agent
- Consolidates agent analyses
- Generates actionable recommendations

### 5. Report Generation (`report_generation/`)
- Creates executive summaries and detailed audits
- Supports multiple formats (PDF, HTML, JSON, Excel)
- Generates compliance checklists
- Stores reports in S3 with metadata

## Database Schema

The system uses Snowflake with the following schema structure:

- **RAW Schema**: Raw document storage and metadata
- **PROCESSED Schema**: Extracted clauses and entities
- **VECTORS Schema**: Embeddings and similarity mappings
- **ANALYTICS Schema**: Analysis results and compliance mappings
- **REFERENCE Schema**: Regulation catalog and master data

## Deployment

### Development Environment

```bash
# Start local API server
cd src/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Deploy to AWS
./scripts/deploy.sh
```

### Production Deployment

```bash
# Set production environment
export ENVIRONMENT=prod

# Deploy with production settings
./scripts/deploy.sh

# Monitor deployment
aws logs tail /aws/lambda/compliance-mapping --follow
```

## Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with coverage
pytest --cov=src tests/
```

## Monitoring and Logging

- **CloudWatch Logs**: Centralized logging for all Lambda functions
- **CloudWatch Metrics**: Custom metrics for processing performance
- **EventBridge**: Event-driven monitoring and alerting
- **X-Ray**: Distributed tracing for request flows

## Security

- **IAM Roles**: Principle of least privilege access
- **Encryption**: AES-256 encryption at rest and TLS 1.2+ in transit
- **VPC**: Private subnets for Lambda functions
- **API Authentication**: JWT tokens with Cognito integration

## Performance Optimization

- **Lambda Layers**: Shared dependencies and models
- **Connection Pooling**: Efficient database connections
- **Caching**: Multi-level caching strategy
- **Batch Processing**: Optimized for large document sets

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For technical support and questions:
- Create an issue in the repository
- Contact the development team
- Refer to the comprehensive documentation in `/docs/`

---

**Note**: This is a production-ready backend implementation with comprehensive error handling, logging, and monitoring. The system is designed to scale and handle enterprise-level compliance analysis workloads.
