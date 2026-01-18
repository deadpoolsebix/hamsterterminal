with open('professional_dashboard_final.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position where we need to insert (before THE TAPE section)
search_text = '<div class="news-panel" style="border-color:#ff00ff;'
pos = content.find(search_text)

if pos == -1:
    print("ERROR: Could not find insertion point")
else:
    # Insert the hamster panel
    hamster_panel = '''        <!-- 🐹 AI GENIUS HAMSTER • MARKET COMMENTARY & SIGNALS -->
        <div style="padding: 15px; background: linear-gradient(135deg, #1a0a1a 0%, #0f0a0f 100%); border: 2px solid #bb86fc; border-radius: 8px; margin-bottom: 15px; margin-top: 15px;">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <h3 style="color: #bb86fc; font-family: 'Courier New', monospace; text-transform: uppercase; letter-spacing: 1px; margin: 0; font-size: 0.9em;">🐹 AI GENIUS HAMSTER • LIVE ANALYSIS</h3>
            </div>
            <div id="hamster-container" style="display: grid; grid-template-columns: 100px 1fr 80px; gap: 12px; align-items: center; background: #0f0f1a; padding: 12px; border-radius: 6px; border: 2px solid #bb86fc;">
                <div style="text-align: center; font-size: 3em; animation: hamsterBounce 1.5s ease-in-out infinite;">🐹</div>
                <div id="hamster-comment" style="color: #9fff9f; font-size: 0.85em; line-height: 1.6; font-family: 'Courier New', 'Courier', monospace; min-height: 50px; text-transform: uppercase; letter-spacing: 0.5px; text-shadow: 0 0 5px rgba(159, 255, 159, 0.5); background: rgba(0, 20, 0, 0.6); padding: 8px; border-radius: 3px; border: 1px solid #00ff41; overflow-y: auto;">ANALIZUJE RSI & MACD...</div>
                <div id="hamster-emotion" style="text-align: center; font-size: 2.4em; animation: hamsterMood 2s ease-in-out infinite;">🤔</div>
            </div>
            
            <!-- Signal Badges -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 6px; margin-top: 10px;">
                <div id="signal-buy" style="padding: 6px; background: rgba(0,255,65,0.15); border: 1px solid #00ff41; border-radius: 3px; text-align: center; font-size: 0.7em; color: #00ff41; font-weight: 700; cursor: pointer; transition: all 0.3s;">🟢 KUP</div>
                <div id="signal-sell" style="padding: 6px; background: rgba(255,0,51,0.15); border: 1px solid #ff0033; border-radius: 3px; text-align: center; font-size: 0.7em; color: #ff0033; font-weight: 700; cursor: pointer; transition: all 0.3s;">🔴 SPRZEDAJ</div>
                <div id="signal-scalp" style="padding: 6px; background: rgba(255,170,0,0.15); border: 1px solid #ffaa00; border-radius: 3px; text-align: center; font-size: 0.7em; color: #ffaa00; font-weight: 700; cursor: pointer; transition: all 0.3s;">⚡ SCALP</div>
                <div id="signal-bounce" style="padding: 6px; background: rgba(0,212,255,0.15); border: 1px solid #00d4ff; border-radius: 3px; text-align: center; font-size: 0.7em; color: #00d4ff; font-weight: 700; cursor: pointer; transition: all 0.3s;">📈 ODBICIE</div>
            </div>
        </div>
        
        '''
    
    new_content = content[:pos] + hamster_panel + content[pos:]
    
    with open('professional_dashboard_final.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Hamster panel inserted successfully!")
