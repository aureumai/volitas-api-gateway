#!/bin/bash

# Cloud Run startup script for debugging
echo "🚀 Starting Volitas backend for Cloud Run..."
echo "📍 PORT: ${PORT:-8080}"
echo "📍 Environment: ${ENVIRONMENT:-development}"

# Check if we can import our modules
echo "🔍 Testing imports..."
python -c "
try:
    from app.core.config import settings
    print('✅ Config imported successfully')
    print(f'✅ Project name: {settings.PROJECT_NAME}')
except Exception as e:
    print(f'❌ Config import failed: {e}')
    exit(1)

try:
    from app.api.v1 import api_router
    print('✅ API router imported successfully')
except Exception as e:
    print(f'❌ API router import failed: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ All imports successful, starting server..."
    exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --log-level info
else
    echo "❌ Import check failed, exiting..."
    exit 1
fi
