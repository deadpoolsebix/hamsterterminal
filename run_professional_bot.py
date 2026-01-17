"""
PROFESSIONAL WALL STREET STYLE BOT LAUNCHER
"""

import time
import threading
from advanced_live_bot import AdvancedLiveBot
from professional_wall_street_dashboard import WallStreetDashboard


def update_dashboard_loop(bot, dashboard, interval=60):
    """Background thread to update dashboard"""
    while True:
        try:
            time.sleep(interval)
            
            if not hasattr(bot, 'last_data') or bot.last_data is None:
                continue
            
            # Generate professional dashboard
            html = dashboard.create_professional_dashboard(
                data=bot.last_data,
                indicators=bot.last_indicators if hasattr(bot, 'last_indicators') else {},
                trades=bot.trades if hasattr(bot, 'trades') else [],
                starting_capital=getattr(bot, 'start_capital', getattr(bot, 'starting_capital', 5000))
            )
            
            # Save as live dashboard
            dashboard.save_dashboard(html, "professional_dashboard_live.html")
            print(f"\n[✓] Professional Dashboard updated: professional_dashboard_live.html")
            
        except Exception as e:
            print(f"\n[!] Dashboard update error: {e}")


def main():
    print("""
    
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                              ║
    ║           ⚡ PROFESSIONAL WALL STREET TRADING TERMINAL ⚡                    ║
    ║                                                                              ║
    ║  🏛️  BLOOMBERG TERMINAL INSPIRED DESIGN                                     ║
    ║                                                                              ║
    ║  📊 ADVANCED FEATURES:                                                       ║
    ║     • Real-time BUY/SELL Signals with Confidence Score                      ║
    ║     • Market Sentiment Analysis (Bullish/Bearish)                           ║
    ║     • Fair Value Gap (FVG) Detection & Visualization                        ║
    ║     • Insider News Feed & Market Alerts                                     ║
    ║     • Liquidity Grab Detection                                              ║
    ║     • Multi-Panel Professional Charts (Price, RSI, MACD, Volume)            ║
    ║     • Support & Resistance Levels                                           ║
    ║     • Real-time P&L Tracking                                                ║
    ║     • 24/7 Live Market Monitoring                                           ║
    ║                                                                              ║
    ║  ⚙️  CONFIGURATION:                                                          ║
    ║     Interval: 15 minutes                                                    ║
    ║     Capital: $5,000                                                         ║
    ║     Stop Loss: -10% | Take Profit: +8%                                      ║
    ║     Dashboard Refresh: Every 5 seconds                                      ║
    ║     Bot Update: Every 60 seconds                                            ║
    ║                                                                              ║
    ║  📁 OUTPUT FILES:                                                            ║
    ║     professional_dashboard_live.html  - Live updates                        ║
    ║     professional_dashboard_final.html - Final report                        ║
    ║                                                                              ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    
    """)
    
    # Initialize
    bot = AdvancedLiveBot(interval='15m')
    
    dashboard = WallStreetDashboard()
    
    print("\nInicjalizacja Professional Trading Terminal...")
    print("\nKonfiguracja:")
    print("  Interval: 15m")
    print("  Dashboard Update: co 60s")
    print("  Dashboard Refresh: co 5s (auto-reload)")
    print("  Mode: PROFESSIONAL WALL STREET STYLE")
    
    # Start dashboard update thread
    print("\n[*] Uruchamianie Professional Dashboard thread...")
    dashboard_thread = threading.Thread(
        target=update_dashboard_loop,
        args=(bot, dashboard, 60),
        daemon=True
    )
    dashboard_thread.start()
    print("[OK] Dashboard thread uruchomiony")
    
    try:
        # Run live trading (duration_minutes=None means infinite)
        bot.run_live_trading(duration_minutes=10080)  # 7 days = 7*24*60 = 10080 minutes
        
    except KeyboardInterrupt:
        print("\n\n[!] Bot zatrzymany przez użytkownika")
    
    except Exception as e:
        print(f"\n\n[!] Błąd: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Generate final professional dashboard
        print("\n[*] Generowanie final professional dashboarda...")
        
        try:
            if hasattr(bot, 'last_data') and bot.last_data is not None:
                html = dashboard.create_professional_dashboard(
                    data=bot.last_data,
                    indicators=bot.last_indicators if hasattr(bot, 'last_indicators') else {},
                    trades=bot.trades if hasattr(bot, 'trades') else [],
                    starting_capital=getattr(bot, 'start_capital', getattr(bot, 'starting_capital', 5000))
                )
                
                filename = dashboard.save_dashboard(html, "professional_dashboard_final.html")
                print(f"[✓] Zapisano: {filename}")
                
                # Open in browser
                import webbrowser
                import os
                webbrowser.open('file://' + os.path.realpath(filename))
                
        except Exception as e:
            print(f"[!] Błąd podczas generowania dashboarda: {e}")


if __name__ == "__main__":
    main()
