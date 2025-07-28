
# Main Terraform configuration for Agentic Compliance-Mapping System

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-2"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "compliance-mapping"
}

# S3 Buckets
resource "aws_s3_bucket" "raw_documents" {
  bucket = "${var.project_name}-docs-raw-${var.environment}"
}

resource "aws_s3_bucket" "processed_documents" {
  bucket = "${var.project_name}-docs-processed-${var.environment}"
}

resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-reports-${var.environment}"
}

# Lambda Functions
resource "aws_lambda_function" "document_ingestion" {
  filename         = "document_ingestion.zip"
  function_name    = "${var.project_name}-document-ingestion-${var.environment}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "handler.lambda_handler"
  runtime         = "python3.9"
  timeout         = 900
  memory_size     = 3008

  environment {
    variables = {
      ENVIRONMENT = var.environment
      S3_BUCKET_RAW = aws_s3_bucket.raw_documents.bucket
      S3_BUCKET_PROCESSED = aws_s3_bucket.processed_documents.bucket
    }
  }
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# API Gateway
resource "aws_api_gateway_rest_api" "compliance_api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "Agentic Compliance-Mapping API"
}

# EventBridge
resource "aws_cloudwatch_event_bus" "compliance_bus" {
  name = "compliance-processing-bus"
}

# Outputs
output "api_gateway_url" {
  value = aws_api_gateway_rest_api.compliance_api.execution_arn
}

output "s3_buckets" {
  value = {
    raw_documents = aws_s3_bucket.raw_documents.bucket
    processed_documents = aws_s3_bucket.processed_documents.bucket
    reports = aws_s3_bucket.reports.bucket
  }
}
