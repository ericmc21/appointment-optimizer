#!/bin/bash
# setup.sh

echo "🏥 Setting up Appointment Optimizer..."

# Create venv
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Copy env template
cp .env.example .env

echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Infermedica credentials"
echo "2. Run: python infermedica_client.py"