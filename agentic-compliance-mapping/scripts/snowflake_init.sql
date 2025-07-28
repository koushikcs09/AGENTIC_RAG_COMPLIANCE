
-- Snowflake database initialization script
-- Run this script to set up the complete database schema

-- Create database and schemas
CREATE DATABASE IF NOT EXISTS COMPLIANCE_DB;
USE DATABASE COMPLIANCE_DB;

CREATE SCHEMA IF NOT EXISTS RAW;
CREATE SCHEMA IF NOT EXISTS PROCESSED;
CREATE SCHEMA IF NOT EXISTS VECTORS;
CREATE SCHEMA IF NOT EXISTS ANALYTICS;
CREATE SCHEMA IF NOT EXISTS REFERENCE;

-- RAW Schema Tables
CREATE TABLE IF NOT EXISTS RAW.RAW_DOCUMENTS (
    document_id VARCHAR(255) PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size_bytes NUMBER(15,0),
    file_hash VARCHAR(64),
    content_type VARCHAR(100),
    upload_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    document_type VARCHAR(100),
    processing_status VARCHAR(50) DEFAULT 'uploaded',
    raw_content TEXT,
    metadata VARIANT,
    created_by VARCHAR(255),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- PROCESSED Schema Tables
CREATE TABLE IF NOT EXISTS PROCESSED.CLAUSES (
    clause_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    processed_doc_id VARCHAR(255),
    clause_number VARCHAR(100),
    section_reference VARCHAR(200),
    clause_title VARCHAR(500),
    clause_text TEXT NOT NULL,
    clause_type VARCHAR(100),
    clause_subtype VARCHAR(100),
    page_numbers ARRAY,
    word_count NUMBER(8,0),
    sentence_count NUMBER(6,0),
    complexity_score FLOAT,
    mandatory_language BOOLEAN DEFAULT FALSE,
    penalty_clause BOOLEAN DEFAULT FALSE,
    extracted_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- VECTORS Schema Tables
CREATE TABLE IF NOT EXISTS VECTORS.CLAUSE_EMBEDDINGS (
    embedding_id VARCHAR(255) PRIMARY KEY,
    clause_id VARCHAR(255) NOT NULL,
    embedding VECTOR(FLOAT, 1536) NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'snowflake-arctic-embed-m',
    model_version VARCHAR(50),
    chunk_text TEXT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS VECTORS.REGULATION_EMBEDDINGS (
    reg_embedding_id VARCHAR(255) PRIMARY KEY,
    regulation_id VARCHAR(255) NOT NULL,
    embedding VECTOR(FLOAT, 1536) NOT NULL,
    regulation_text TEXT NOT NULL,
    regulation_category VARCHAR(100),
    jurisdiction VARCHAR(100),
    act_name VARCHAR(500),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- ANALYTICS Schema Tables
CREATE TABLE IF NOT EXISTS ANALYTICS.COMPLIANCE_MAPPINGS (
    compliance_mapping_id VARCHAR(255) PRIMARY KEY,
    clause_id VARCHAR(255) NOT NULL,
    regulation_id VARCHAR(255),
    mapping_type VARCHAR(100),
    compliance_status VARCHAR(50),
    compliance_score FLOAT,
    similarity_score FLOAT,
    compliance_category VARCHAR(100),
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS ANALYTICS.ANALYSIS_RESULTS (
    analysis_id VARCHAR(255) PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    analysis_type VARCHAR(100),
    overall_compliance_score FLOAT,
    overall_risk_score FLOAT,
    agent_analyses VARIANT,
    analysis_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE TABLE IF NOT EXISTS ANALYTICS.REPORTS (
    report_id VARCHAR(255) PRIMARY KEY,
    analysis_id VARCHAR(255) NOT NULL,
    report_type VARCHAR(100),
    report_format VARCHAR(50),
    file_size_bytes NUMBER(15,0),
    generated_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_raw_documents_status ON RAW.RAW_DOCUMENTS(processing_status);
CREATE INDEX IF NOT EXISTS idx_clauses_doc_id ON PROCESSED.CLAUSES(document_id);
CREATE INDEX IF NOT EXISTS idx_clause_embeddings_clause_id ON VECTORS.CLAUSE_EMBEDDINGS(clause_id);
CREATE INDEX IF NOT EXISTS idx_compliance_mappings_clause_id ON ANALYTICS.COMPLIANCE_MAPPINGS(clause_id);

-- Insert sample regulation data
INSERT INTO VECTORS.REGULATION_EMBEDDINGS (
    reg_embedding_id, regulation_id, embedding, regulation_text, 
    regulation_category, jurisdiction, act_name
) VALUES (
    'reg_whs_001',
    'WHS_ACT_2011_S19',
    SNOWFLAKE.CORTEX.EMBED_TEXT_1536('snowflake-arctic-embed-m', 'A person conducting a business or undertaking must ensure, so far as is reasonably practicable, the health and safety of workers engaged, or caused to be engaged by the person.'),
    'A person conducting a business or undertaking must ensure, so far as is reasonably practicable, the health and safety of workers engaged, or caused to be engaged by the person.',
    'safety_compliance',
    'federal',
    'Work Health and Safety Act 2011'
);

-- Grant permissions (adjust as needed)
GRANT USAGE ON DATABASE COMPLIANCE_DB TO ROLE COMPLIANCE_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE COMPLIANCE_DB TO ROLE COMPLIANCE_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN DATABASE COMPLIANCE_DB TO ROLE COMPLIANCE_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN DATABASE COMPLIANCE_DB TO ROLE COMPLIANCE_ROLE;

COMMIT;
