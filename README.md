
# Agentic Compliance-Mapping System for Australian Mining Regulations

## Overview

The Agentic Compliance-Mapping System is a sophisticated AI-powered solution designed to automate compliance verification for Australian mining regulations. The system processes vendor contracts and regulatory documents to generate comprehensive audit checklists and compliance reports.

## Key Features

- **Automated Document Processing**: Handles ~50 PDF files with text and images (<100 pages each)
- **Real-time Contract Analysis**: Streamlit frontend for immediate vendor contract upload and analysis
- **Batch Regulatory Processing**: Efficient processing of Australian mining T&C documents
- **AI-Powered Compliance Mapping**: Semantic alignment between contracts and regulations
- **Comprehensive Audit Reports**: Downloadable AI audit checklists with compliance gaps
- **Scalable Architecture**: AWS Lambda backend with Snowflake Vector Store

## System Architecture

The system implements 5 core pipelines:
1. **Document Ingestion Pipeline**: PDF processing with OCR and text extraction
2. **Clause Extraction Pipeline**: AI-powered identification of key contract clauses
3. **Semantic Alignment & Mapping Pipeline**: Vector-based similarity matching
4. **Agentic Reasoning Loop**: Multi-agent compliance analysis and gap identification
5. **Audit & Reporting Pipeline**: Comprehensive report generation

## Technology Stack

- **Backend**: AWS Lambda, API Gateway, S3, EventBridge
- **Frontend**: Streamlit with real-time processing capabilities
- **Data Storage**: Snowflake Vector Store with Cortex AI capabilities
- **AI Framework**: LangChain with custom agents and tools
- **Document Processing**: AWS Textract, PyPDF2, Unstructured
- **Vector Embeddings**: Snowflake Cortex embedding models

## Quick Start

### Prerequisites
- AWS Account with appropriate permissions
- Snowflake account with Cortex capabilities
- Python 3.9+
- Docker (for local development)

### Deployment
```bash
# Clone repository
git clone <repository-url>
cd agentic-compliance-mapping

# Install dependencies
pip install -r requirements.txt

# Deploy infrastructure
cd infrastructure
terraform init
terraform apply

# Deploy application
cd ../deployment
./deploy.sh
```

## Documentation Structure

- [`docs/architecture.md`](docs/architecture.md) - System architecture and AWS services
- [`docs/data_flow.md`](docs/data_flow.md) - Data flow diagrams and pipeline details
- [`docs/db_schema.md`](docs/db_schema.md) - Snowflake database schema and vector store
- [`docs/api_spec.md`](docs/api_spec.md) - API specifications and endpoints
- [`docs/implementation_roadmap.md`](docs/implementation_roadmap.md) - Implementation phases and timeline

## License

MIT License - see LICENSE file for details

## Support

For technical support and questions, please refer to the documentation or create an issue in the repository.
