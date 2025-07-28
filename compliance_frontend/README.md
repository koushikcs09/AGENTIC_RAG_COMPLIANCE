
# Agentic Compliance-Mapping System Frontend

AI-powered compliance mapping for Australian mining regulations - Streamlit Frontend Application

## Overview

This Streamlit application provides a user-friendly interface for compliance officers and legal teams to analyze vendor contract PDF files against Australian mining regulations. The system uses AI-powered mapping to identify compliance gaps, assess risks, and generate actionable recommendations.

## Features

### 🔍 Core Functionality
- **PDF Document Upload** with comprehensive validation
- **Real-time Processing Status** with progress tracking
- **Compliance Mapping** against Australian mining regulations
- **AI-Generated Audit Checklist** for systematic review
- **Multi-format Downloads** (Excel, CSV, JSON)
- **Risk Assessment** with color-coded visualization

### 📊 Analysis Capabilities
- Automatic clause extraction and classification
- Regulatory reference mapping
- Compliance scoring and risk level assessment
- Gap analysis with suggested actions
- Interactive data visualization

### 📋 Compliance Areas Covered
- **Work Health and Safety (WHS)** requirements
- **Environmental Protection** obligations  
- **Insurance and Risk Management** standards
- **Personnel Competency** requirements
- **Emergency Response** procedures
- **Regulatory Reporting** obligations

## System Architecture

```
┌─────────────────┬─────────────────┬─────────────────┐
│   Frontend      │   Backend API   │   AI Processing │
│   (Streamlit)   │   (FastAPI)     │   (AWS Lambda)  │
├─────────────────┼─────────────────┼─────────────────┤
│ • File Upload   │ • Document Mgmt │ • PDF Analysis  │
│ • Status Display│ • Analysis APIs │ • Clause Extract│
│ • Results View  │ • Report APIs   │ • Semantic Map  │
│ • Downloads     │ • Data Storage  │ • Risk Assess  │
└─────────────────┴─────────────────┴─────────────────┘
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Access to backend API endpoints

### Setup Instructions

1. **Clone/Download the Application**
   ```bash
   cd /home/ubuntu/compliance_frontend
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   - Edit `.env` file to configure API endpoints and settings
   - Ensure backend API is running and accessible

4. **Run the Application**
   ```bash
   streamlit run app.py
   ```

5. **Access the Interface**
   - Open browser to `http://localhost:8501`
   - Upload PDF documents for analysis

## Usage Guide

### Step 1: Document Upload
1. Navigate to the upload section
2. Select a PDF contract file (max 50MB)
3. Wait for validation confirmation
4. Click "Upload & Start Analysis"

### Step 2: Processing & Analysis
1. Monitor real-time progress updates
2. View processing status and completion percentage
3. System automatically advances to results when complete

### Step 3: Review Results
1. **Metrics Dashboard**: Overall compliance score and risk summary
2. **Visual Charts**: Compliance distribution and risk level charts
3. **Detailed Mappings**: Table view with T&C references, clauses, and flags
4. **Audit Checklist**: AI-generated systematic review items
5. **Recommendations**: Prioritized action items

### Step 4: Download Reports
1. **Excel Report**: Complete analysis with all data and charts
2. **CSV Data**: Compliance mappings for further analysis
3. **JSON Report**: Machine-readable format for integration

## Configuration

### Environment Variables (.env)
```bash
# Backend API Configuration
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30

# Application Configuration
APP_TITLE=Agentic Compliance Mapping System
MAX_FILE_SIZE_MB=50

# Processing Configuration
POLLING_INTERVAL=2
MAX_POLLING_ATTEMPTS=150
```

### API Endpoints
- **Document Upload**: `/api/v1/documents/upload`
- **Analysis Trigger**: `/api/v1/analysis/analyze/{document_id}`
- **Results Retrieval**: `/api/v1/analysis/{analysis_id}/results`
- **Report Generation**: `/api/v1/reports/generate`

## Compliance Framework

### Australian Mining Regulations Covered

#### Federal Legislation
- Environment Protection and Biodiversity Conservation Act 1999 (EPBC Act)
- Native Title Act 1993
- Work Health and Safety Act 2011

#### State Mining Acts
- Mining Act 1978 (WA)
- Mining Act 1992 (NSW)  
- Mineral Resources Act 1989 (Qld)
- Mining Act 1971 (SA)
- And others across all Australian jurisdictions

#### Key Compliance Areas
1. **Safety Management Systems**
   - Principal Mining Hazard Management Plans
   - Contractor Safety Management Plans
   - Emergency Response Procedures

2. **Environmental Obligations**
   - Environmental Impact Assessments
   - Rehabilitation and Closure Plans
   - Cultural Heritage Protection

3. **Operational Requirements**
   - Personnel Competency and Licensing
   - Insurance and Financial Assurance
   - Reporting and Documentation

## Output Format

### Compliance Mapping Table Structure
| Column | Description |
|--------|-------------|
| T&C Reference | Specific contract section/clause reference |
| Mapped Vendor Clause | Relevant contract language identified |
| Compliance Flag | 🟢 Compliant / 🟡 Partial / 🔴 Non-Compliant |
| Score | Numerical compliance percentage |
| Risk Level | Low / Medium / High / Critical |
| Suggested Action | Specific recommendations for improvement |

### Risk Assessment Levels
- **🟢 Low Risk (90-100%)**: Fully compliant, minimal action required
- **🟡 Medium Risk (70-89%)**: Partially compliant, improvements recommended  
- **🟠 High Risk (50-69%)**: Significant gaps, immediate attention required
- **🔴 Critical Risk (0-49%)**: Major non-compliance, urgent action needed

## Technical Details

### File Processing
- **Supported Formats**: PDF only
- **Maximum File Size**: 50MB
- **Validation**: Format, size, and content checks
- **Security**: File type validation and safe processing

### AI Processing Pipeline
1. **Document Ingestion**: PDF parsing and text extraction
2. **Clause Classification**: AI-powered content categorization
3. **Semantic Mapping**: Vector similarity matching against regulations
4. **Risk Assessment**: Multi-agent analysis system
5. **Report Generation**: Structured output with recommendations

### Performance Characteristics
- **Upload Processing**: < 30 seconds for typical contracts
- **Analysis Duration**: 2-5 minutes depending on document complexity
- **Concurrent Users**: Designed for multiple simultaneous analyses
- **Real-time Updates**: 2-second polling interval for status updates

## Troubleshooting

### Common Issues

#### File Upload Problems
- **"Invalid PDF format"**: Ensure file is a valid PDF document
- **"File too large"**: Reduce file size to under 50MB
- **"Upload failed"**: Check network connection and backend availability

#### Processing Issues
- **"Analysis timeout"**: Large documents may require more time
- **"Backend unavailable"**: Verify API service is running
- **"Connection error"**: Check network connectivity and firewall settings

#### Display Problems
- **Missing charts**: Ensure plotly is installed correctly
- **Table formatting**: Check pandas version compatibility
- **Download failures**: Verify browser download permissions

### Support Contacts
- **Technical Support**: support@compliance-mapping.com
- **Documentation**: [System Documentation](https://docs.compliance-mapping.com)
- **GitHub Issues**: [Report Issues](https://github.com/your-org/compliance-mapping/issues)

## Development

### Project Structure
```
compliance_frontend/
├── app.py                 # Main Streamlit application
├── config.py             # Configuration settings
├── api_client.py         # Backend API communication
├── utils.py              # Utility functions and helpers
├── requirements.txt      # Python dependencies
├── .env                  # Environment configuration
└── README.md            # This documentation
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes with appropriate tests
4. Submit a pull request with detailed description

### Testing
```bash
# Run basic functionality tests
python -m pytest tests/

# Test API connectivity
python -c "from api_client import mock_api_client; print(mock_api_client.health_check())"
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Australian Government Department of Industry, Science and Resources
- State mining departments for regulatory guidance
- AI/ML libraries: OpenAI, Anthropic, LangChain
- Visualization: Plotly, Streamlit
- Data processing: Pandas, PyPDF2

---

**Version**: 1.0.0  
**Last Updated**: July 26, 2025  
**Developed for**: Australian Mining Industry Compliance
