#!/bin/bash

# AUTO-Translate v.2 Setup Script

echo "=========================================="
echo "AUTO-Translate v.2 - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d "ATvenv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "ATvenv" ]; then
    source ATvenv/bin/activate
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers..."
playwright install chromium

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   Get your API key from: https://console.anthropic.com/"
else
    echo "✓ .env file already exists"
fi

# Create workspace directories
echo ""
echo "Creating workspace directories..."
mkdir -p workspace/{raw_panels,stitched,splits,ocr,filtered,inpainted,rendered,final}
echo "✓ Workspace directories created"

# Run installation test
echo ""
echo "=========================================="
echo "Running installation test..."
echo "=========================================="
python test_installation.py

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your ANTHROPIC_API_KEY"
echo "  2. Run: streamlit run app.py"
echo "  3. Or:  python cli.py <manhwa-url>"
echo ""
