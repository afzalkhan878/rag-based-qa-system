#!/bin/bash

echo "=================================="
echo "Advanced RAG System Setup"
echo "=================================="
echo ""

# Check Python version
python3 --version

echo ""
echo "Installing dependencies..."
pip install --break-system-packages -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Run demo: python demo.py"
echo "  2. Run tests: python test_rag.py"
echo "  3. Start API: python api.py"
echo "  4. Try examples: python examples.py"
echo ""
echo "Documentation:"
echo "  • README.md - Setup and usage"
echo "  • EXPLANATION.md - Technical details"
echo "  • DEPLOYMENT.md - Production deployment"
echo ""
