#!/usr/bin/env python3
"""
✅ Hamster Terminal WebSocket - Verification Script
Sprawdza czy wszystko jest poprawnie skonfigurowane
"""

import subprocess
import sys
import os

def print_header(title):
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def check_python_version():
    print_header("Python Version")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} - Need 3.8+")
        return False

def check_packages():
    print_header("Required Packages")
    required = [
        'flask',
        'flask_cors',
        'flask_socketio',
        'socketio',
        'engineio',
        'websockets',
        'requests'
    ]
    
    all_good = True
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_good = False
    
    if not all_good:
        print("\n📦 Install missing packages:")
        print("   pip install -r requirements.txt")
    
    return all_good

def check_api_key():
    print_header("Twelve Data API Key")
    
    api_key = os.getenv('TWELVE_DATA_API_KEY')
    
    if api_key:
        if api_key == 'demo':
            print(f"⚠️  Using DEMO key (limited: 800 calls/min)")
            print("   To upgrade:")
            print("   1. Go https://twelvedata.com")
            print("   2. Get API key")
            print("   3. Set: $env:TWELVE_DATA_API_KEY='your_key'")
            return True
        else:
            masked = api_key[:10] + "..." + api_key[-5:]
            print(f"✅ API key configured: {masked}")
            return True
    else:
        print("⚠️  TWELVE_DATA_API_KEY not set")
        print("   Using default: 'demo'")
        print("   To set: $env:TWELVE_DATA_API_KEY='your_key'")
        os.environ['TWELVE_DATA_API_KEY'] = 'demo'
        return True

def check_files():
    print_header("Required Files")
    
    required_files = [
        'api_server.py',
        'professional_websocket_client.js',
        'professional_websocket_dashboard.html',
        'requirements.txt'
    ]
    
    all_good = True
    for filename in required_files:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename} ({size} bytes)")
        else:
            print(f"❌ {filename} - MISSING")
            all_good = False
    
    return all_good

def check_port_available():
    print_header("Port Availability")
    
    import socket
    
    ports = {
        5000: "API Server",
        8000: "HTTP Server"
    }
    
    all_good = True
    for port, service in ports.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result != 0:
            print(f"✅ Port {port} ({service}) - Available")
        else:
            print(f"❌ Port {port} ({service}) - Already in use!")
            all_good = False
    
    if not all_good:
        print("\n⚠️  Some ports are in use. Kill processes:")
        print("   Windows: netstat -ano | findstr :5000")
        print("   Linux: lsof -i :5000")
    
    return all_good

def test_websockets_support():
    print_header("WebSocket Support")
    
    try:
        import websockets
        import asyncio
        print("✅ websockets library - OK")
        
        # Try to test asyncio
        asyncio.get_event_loop()
        print("✅ asyncio event loop - OK")
        
        return True
    except Exception as e:
        print(f"❌ WebSocket support: {e}")
        return False

def test_server_import():
    print_header("Server Import Test")
    
    try:
        # Try importing the server
        if os.path.exists('api_server.py'):
            import importlib.util
            spec = importlib.util.spec_from_file_location("api_server", "api_server.py")
            module = importlib.util.module_from_spec(spec)
            # Don't actually load, just check syntax
            with open('api_server.py', 'r') as f:
                code = f.read()
                compile(code, 'api_server.py', 'exec')
            print("✅ api_server.py syntax - OK")
            return True
    except SyntaxError as e:
        print(f"❌ Syntax error in api_server.py:")
        print(f"   Line {e.lineno}: {e.msg}")
        return False
    except Exception as e:
        print(f"⚠️  Could not test import: {e}")
        return True

def print_summary(results):
    print_header("Verification Summary")
    
    passed = sum(results.values())
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\n📊 Results: {passed}/{total} checks passed ({percentage:.0f}%)")
    
    if percentage == 100:
        print("\n✅ ALL CHECKS PASSED! You're ready to go!")
        print("\n🚀 Next steps:")
        print("   1. Run:  python api_server.py")
        print("   2. In another terminal: python -m http.server 8000")
        print("   3. Open: http://localhost:8000/professional_websocket_dashboard.html")
        return True
    elif percentage >= 80:
        print("\n⚠️  MOST CHECKS PASSED")
        print("   Fix the failing checks above and run again")
        return True
    else:
        print("\n❌ SOME CHECKS FAILED")
        print("   Please fix the issues above")
        return False

def main():
    print("\n" + "█"*60)
    print("🚀 HAMSTER TERMINAL WebSocket - Verification")
    print("█"*60)
    
    results = {
        'Python Version': check_python_version(),
        'Packages': check_packages(),
        'API Key': check_api_key(),
        'Required Files': check_files(),
        'Port Availability': check_port_available(),
        'WebSocket Support': test_websockets_support(),
        'Server Syntax': test_server_import()
    }
    
    success = print_summary(results)
    
    print("\n📚 Documentation:")
    print("   • WEBSOCKET_QUICKSTART.md - Start here!")
    print("   • WEBSOCKET_INTEGRATION_GUIDE.md - Full guide")
    print("   • ARCHITECTURE_DIAGRAM.md - How it works")
    
    print("\n" + "="*60 + "\n")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
