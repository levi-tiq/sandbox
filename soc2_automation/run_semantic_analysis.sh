#!/bin/bash
# SOC2 Semantic Analysis Runner
# This script activates the virtual environment and runs semantic analysis

echo "🚀 SOC2 Semantic Analysis Runner"
echo "================================"

# Try to find and activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "📦 Activating venv..."
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    echo "📦 Activating .venv..."
    source .venv/bin/activate
elif [ -f "../venv/bin/activate" ]; then
    echo "📦 Activating ../venv..."
    source ../venv/bin/activate
else
    echo "⚠️  No virtual environment found. Using system Python."
    echo "   If you have a venv, please activate it manually:"
    echo "   source your-venv-path/bin/activate"
fi

echo "🔍 Checking Python and dependencies..."
python3 --version
pip list | grep -E "(sentence-transformers|scikit-learn|torch)" || echo "⚠️  Dependencies may not be installed"

echo ""
echo "🧪 Running integration tests..."
cd soc2_automation
python3 semantic_analysis/test_semantic_integration.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🧠 Running full semantic analysis..."
    
    # First ensure we have variance data
    if [ ! -f "data/processed/latest/control_variance_report.json" ]; then
        echo "📊 Generating variance data first..."
        python3 core/control_variance_analyzer.py
    fi
    
    # Run semantic analysis
    python3 semantic_analysis/semantic_analyzer.py
    
    echo ""
    echo "🎨 You can also run enhanced analysis with:"
    echo "   python3 core/control_variance_analyzer.py  # (will include semantic analysis)"
    echo ""
    echo "🔍 Or query results with:"
    echo "   python3 cli/control_query_cli.py"
    
else
    echo "❌ Tests failed. Please check dependencies and data availability."
fi