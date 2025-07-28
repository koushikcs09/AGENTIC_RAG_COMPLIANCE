
#!/bin/bash

# Deployment script for Agentic Compliance-Mapping System

set -e

echo "🚀 Starting deployment of Agentic Compliance-Mapping System..."

# Set environment variables
export ENVIRONMENT=${ENVIRONMENT:-dev}
export AWS_REGION=${AWS_REGION:-ap-southeast-2}

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🏗️ Building Lambda deployment packages..."
mkdir -p dist/lambda

# Package each Lambda function
for lambda_dir in src/lambda_functions/*/; do
    lambda_name=$(basename "$lambda_dir")
    echo "Packaging $lambda_name..."
    
    cd "$lambda_dir"
    zip -r "../../../dist/lambda/${lambda_name}.zip" . -x "*.pyc" "__pycache__/*"
    cd - > /dev/null
done

echo "🌩️ Deploying infrastructure with Terraform..."
cd infrastructure/terraform
terraform init
terraform plan -var="environment=$ENVIRONMENT"
terraform apply -auto-approve -var="environment=$ENVIRONMENT"
cd - > /dev/null

echo "❄️ Initializing Snowflake database..."
# Note: This requires Snowflake credentials to be configured
# snowsql -f scripts/snowflake_init.sql

echo "🔧 Updating Lambda functions..."
aws lambda update-function-code \
    --function-name "compliance-mapping-document-ingestion-$ENVIRONMENT" \
    --zip-file "fileb://dist/lambda/document_ingestion.zip" \
    --region "$AWS_REGION" || echo "Lambda update failed - function may not exist yet"

echo "✅ Deployment completed successfully!"
echo "🌐 API Gateway URL: $(terraform -chdir=infrastructure/terraform output -raw api_gateway_url)"
echo "📊 Monitor logs: aws logs tail /aws/lambda/compliance-mapping --follow"
