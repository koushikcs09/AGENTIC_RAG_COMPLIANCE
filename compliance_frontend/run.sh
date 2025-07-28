
#!/bin/bash

# Agentic Compliance-Mapping System Frontend Startup Script

echo "🚀 Starting Agentic Compliance-Mapping System Frontend..."
echo "=================================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

echo "✅ Python environment verified"

# Install requirements if not already installed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies. Please check requirements.txt"
    exit 1
fi

echo "✅ Dependencies installed successfully"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Using default configuration."
fi

# Start the Streamlit application
echo "🌐 Starting Streamlit application..."
echo "📍 Access the application at: http://localhost:8501"
echo "🛑 Press Ctrl+C to stop the application"
echo "=================================================="

streamlit run app.py --server.port 8501 --server.address 0.0.0.0

echo "👋 Application stopped. Goodbye!"
