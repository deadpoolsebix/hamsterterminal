#!/bin/bash
# Bloomberg Ticker Integration Script
# Automated setup and deployment

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     BLOOMBERG TICKER - INTEGRATION & DEPLOYMENT           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

PROJECT_DIR=$(pwd)
DASHBOARD_FILE="$PROJECT_DIR/professional_dashboard_final.html"
COMPONENT_FILE="$PROJECT_DIR/bloomberg_ticker_component.html"
BACKUP_FILE="$PROJECT_DIR/professional_dashboard_final.html.backup"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "📋 Checking prerequisites..."
echo ""

# Check if files exist
if [ ! -f "$DASHBOARD_FILE" ]; then
    echo -e "${RED}✗ Dashboard file not found: $DASHBOARD_FILE${NC}"
    exit 1
fi

if [ ! -f "$COMPONENT_FILE" ]; then
    echo -e "${RED}✗ Component file not found: $COMPONENT_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All required files found${NC}"
echo ""

# Backup dashboard
echo "💾 Creating backup..."
if cp "$DASHBOARD_FILE" "$BACKUP_FILE"; then
    echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${RED}✗ Failed to create backup${NC}"
    exit 1
fi
echo ""

# Check for API key
echo "🔑 Checking API key configuration..."
if grep -q "YOUR_API_KEY_HERE" "$COMPONENT_FILE"; then
    echo -e "${YELLOW}⚠ API key not configured!${NC}"
    echo "   Add your Twelve Data API key to: $COMPONENT_FILE"
    echo "   Line: const TWELVE_DATA_KEY = 'YOUR_API_KEY_HERE';"
    echo ""
    read -p "Do you want to continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ API key configured${NC}"
fi
echo ""

# Show verification results
echo "✅ System ready for integration!"
echo ""
echo "Next steps:"
echo "  1. Edit $COMPONENT_FILE and set your Twelve Data API key"
echo "  2. Copy the component code into your dashboard (replace old ticker)"
echo "  3. Test in browser: Open dashboard and verify ticker shows live data"
echo ""
echo "For detailed instructions, see:"
echo "  - BLOOMBERG_TICKER_GUIDE.md (comprehensive)"
echo "  - BLOOMBERG_TICKER_QUICK_START.md (quick reference)"
echo ""

# Optional: Show file locations
echo "📁 File locations:"
echo "   Dashboard:  $DASHBOARD_FILE"
echo "   Component:  $COMPONENT_FILE"
echo "   Backup:     $BACKUP_FILE"
echo ""
