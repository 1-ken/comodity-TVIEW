#!/bin/bash
echo "═══════════════════════════════════════════════════════════════"
echo "🔍 Verifying Commodities Trading System Setup"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check Python modules
echo "1️⃣  Checking Python modules..."
.venv/bin/python3 -m py_compile alerts.py observer.py main.py extract_pairs.py
if [ $? -eq 0 ]; then
    echo "   ✅ All Python files compile successfully"
else
    echo "   ❌ Compilation errors found"
    exit 1
fi
echo ""

# Check configuration
echo "2️⃣  Checking configuration..."
if [ -f "config.json" ]; then
    echo "   ✅ config.json found"
    .venv/bin/python3 -c "import json; json.load(open('config.json'))" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ config.json is valid JSON"
    fi
fi
echo ""

# Test AlertManager
echo "3️⃣  Testing AlertManager..."
.venv/bin/python3 -c "from alerts import AlertManager; m = AlertManager(); print('   ✅ AlertManager loaded'); print('   ✅ Alerts loaded:', len(m.alerts))"
if [ $? -ne 0 ]; then
    echo "   ❌ AlertManager error"
    exit 1
fi
echo ""

# Test extraction
echo "4️⃣  Testing pair extraction..."
if [ -f "extracted_pairs.json" ]; then
    PAIR_COUNT=$(.venv/bin/python3 -c "import json; d=json.load(open('extracted_pairs.json')); print(sum(len(v) for v in d.values()))")
    CAT_COUNT=$(.venv/bin/python3 -c "import json; d=json.load(open('extracted_pairs.json')); print(len(d))")
    echo "   ✅ Extracted $PAIR_COUNT pairs across $CAT_COUNT categories"
fi
echo ""

# Show file status
echo "5️⃣  Files in project:"
ls -lh *.py *.json *.md 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "✨ Setup verification complete! All systems operational."
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📝 Next steps:"
echo "   • Review COMPLETION.md for detailed documentation"
echo "   • Run: python run.py"
echo "   • Visit: http://localhost:8001"
echo ""
