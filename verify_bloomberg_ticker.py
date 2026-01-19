#!/usr/bin/env python3
"""
Bloomberg Ticker Integration Helper
Helps you integrate the new Bloomberg-style ticker into your dashboard
"""

import os
import re
import sys

def find_old_ticker_section(file_path):
    """Find the old ticker section in the dashboard"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the old ticker comment
        if '<!-- LIVE EVENTS & INSTRUMENTS TICKER - PIXEL STYLE ANIMATED -->' in content:
            print("✅ Found old ticker section in dashboard")
            
            # Find line numbers
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'LIVE EVENTS & INSTRUMENTS TICKER' in line:
                    print(f"   Located at line {i}")
                    
                    # Find end of section
                    for j in range(i, len(lines)):
                        if '</div>' in lines[j] and 'pixel-ticker-container' in '\n'.join(lines[max(0,j-10):j]):
                            print(f"   Section ends at approximately line {j+1}")
                            print(f"   Total lines to replace: ~{j-i+1}")
                            break
                    break
            return True
        else:
            print("❌ Old ticker section not found")
            return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def check_api_key(file_path):
    """Check if Twelve Data API key is set"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "const TWELVE_DATA_KEY = 'YOUR_API_KEY_HERE'" in content:
            print("⚠️  API key not configured (still has placeholder)")
            print("   Set your Twelve Data API key in bloomberg_ticker_component.html")
            return False
        elif "const TWELVE_DATA_KEY = ''" in content:
            print("⚠️  API key is empty")
            return False
        else:
            print("✅ API key appears to be configured")
            return True
    except Exception as e:
        print(f"❌ Error checking API key: {e}")
        return False

def verify_symbols(file_path):
    """Verify ticker symbols are valid"""
    valid_symbols = {
        # Metals
        'XAU/USD', 'XAG/USD',
        # Indices
        'SPX', 'INDU', 'IXIC', 'GDAXI', 'N100', 'FTSE',
        # Mega Caps
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JPM', 'V',
        # Forex
        'EUR/USD', 'GBP/USD', 'USD/JPY'
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract symbols from config
        symbols_in_config = re.findall(r"'([A-Z/]+)'(?=\s*[,\}\]])", content)
        
        invalid_symbols = []
        for sym in symbols_in_config:
            if sym not in ['METALS', 'INDICES', 'MEGA CAPS', 'COMMODITIES'] and sym not in valid_symbols:
                invalid_symbols.append(sym)
        
        if not symbols_in_config:
            print("⚠️  No symbols found in configuration")
            return False
        
        print(f"✅ Found {len(symbols_in_config)} symbols configured")
        
        if invalid_symbols:
            print(f"⚠️  Unknown symbols: {', '.join(invalid_symbols)}")
            print("   Verify these are valid Twelve Data symbols")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error verifying symbols: {e}")
        return False

def check_batch_api_call(file_path):
    """Verify batch API call implementation"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if ".join(',');" in content and "api.twelvedata.com/quote" in content:
            print("✅ Batch API call implementation found")
            print("   Uses single request with comma-separated symbols")
            return True
        else:
            print("⚠️  Batch API call might not be properly implemented")
            return False
    except Exception as e:
        print(f"❌ Error checking API implementation: {e}")
        return False

def print_integration_steps():
    """Print step-by-step integration instructions"""
    print("\n" + "="*60)
    print("BLOOMBERG TICKER INTEGRATION STEPS")
    print("="*60)
    
    steps = [
        ("1. Backup Dashboard",
         "cp professional_dashboard_final.html professional_dashboard_final.html.backup"),
        
        ("2. Open bloomberg_ticker_component.html",
         "View the new ticker component and copy its content"),
        
        ("3. Find Old Ticker Section",
         "In professional_dashboard_final.html, search for: 'LIVE EVENTS & INSTRUMENTS TICKER'"),
        
        ("4. Replace Old Ticker",
         "Delete lines from old comment to closing </div> (about 140 lines total)"),
        
        ("5. Paste New Ticker",
         "Insert bloomberg_ticker_component.html content (about 140 lines)"),
        
        ("6. Set API Key",
         "Edit TWELVE_DATA_KEY = 'YOUR_KEY_HERE' with your actual key"),
        
        ("7. Test in Browser",
         "Open dashboard in browser, check console (F12) for errors"),
        
        ("8. Verify Live Data",
         "Ticker should show grouped assets with dynamic colors")
    ]
    
    for title, description in steps:
        print(f"\n{title}")
        print(f"  → {description}")
    
    print("\n" + "="*60)

def main():
    print("\n" + "="*60)
    print("BLOOMBERG TICKER SETUP VERIFICATION")
    print("="*60 + "\n")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check component file
    component_file = os.path.join(script_dir, 'bloomberg_ticker_component.html')
    print("📋 Checking Bloomberg Ticker Component...")
    if os.path.exists(component_file):
        print(f"✅ Component file exists: {component_file}\n")
        
        # Run checks
        print("🔍 Performing validation checks...\n")
        
        api_configured = check_api_key(component_file)
        print()
        
        symbols_valid = verify_symbols(component_file)
        print()
        
        batch_api = check_batch_api_call(component_file)
        print()
        
        # Check dashboard
        dashboard_file = os.path.join(script_dir, 'professional_dashboard_final.html')
        print(f"\n📊 Checking Dashboard...")
        if os.path.exists(dashboard_file):
            print(f"✅ Dashboard file exists\n")
            old_ticker_exists = find_old_ticker_section(dashboard_file)
            print()
        else:
            print(f"❌ Dashboard file not found: {dashboard_file}\n")
            old_ticker_exists = False
        
        # Summary
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        status = {
            'API Key Configured': api_configured,
            'Valid Symbols': symbols_valid,
            'Batch API Implemented': batch_api,
            'Old Ticker Found': old_ticker_exists
        }
        
        for check, result in status.items():
            symbol = "✅" if result else "❌"
            print(f"{symbol} {check}")
        
        all_pass = all(status.values())
        
        if all_pass:
            print("\n✅ All checks passed! Ready to integrate.")
        else:
            print("\n⚠️  Some checks failed. Review above.")
            if not api_configured:
                print("   → Add your Twelve Data API key to bloomberg_ticker_component.html")
        
        # Print steps
        print_integration_steps()
        
        print("\n📚 For detailed instructions, see: BLOOMBERG_TICKER_GUIDE.md")
        print("="*60 + "\n")
        
    else:
        print(f"❌ Component file not found: {component_file}")
        print("\nExpected location:", component_file)
        sys.exit(1)

if __name__ == '__main__':
    main()
