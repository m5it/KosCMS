#!/bin/bash
# KosDB Installation Script
# ========================
# Installs KosCMS with KosDB (LevelDB) - no PostgreSQL needed
#

set -e

echo "=== KosCMS + KosDB Installation ==="
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "→ Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "→ Upgrading pip..."
pip install --upgrade pip

# Install KosDB-optimized requirements
echo "→ Installing KosDB requirements (no PostgreSQL)..."
pip install -r requirements-kosdb.txt

# Verify KosDB client is importable
echo "→ Verifying KosDB client..."
python -c "from webcms.database.kosdb_client import KosDBClient; print('✓ KosDB client OK')"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "  1. Start KosDB server:  python -m webcms.database.kosdb_server"
echo "  2. Run KosCMS:           python -m webcms"
echo ""
echo "Configuration:"
echo "  - Edit .env file to set KOSDB_HOST and KOSDB_PORT"
echo "  - Default: localhost:9999"
echo ""
