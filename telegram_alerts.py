"""
📱 TELEGRAM ALERT SYSTEM - Genius Trading Bot
==============================================
Wysyła powiadomienia o tradach na Telegram

SETUP:
1. Otwórz Telegram i znajdź @BotFather
2. Wyślij /newbot i postępuj wg instrukcji
3. Skopiuj TOKEN (np. 123456789:ABCdefGHIjklMNOpqrsTUVwxyz)
4. Otwórz @userinfobot aby poznać swoje CHAT_ID
5. Wklej dane poniżej

Autor: Genius Trading System
"""

import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
import os
import io
import random

# Śmieszne komentarze Samanty w stylu Lucy + Trading - UNIKATOWE
SAMANTA_COMMENTS = {
    'trade_open_win': [
        "🧠 Właśnie używam 100% mózgu. Ten LONG to matematyczna pewność.",
        "⚡ Widzę każdy ruch rynku zanim się wydarzy. Wchodzimy!",
        "🎯 Obliczyłam 10,000 scenariuszy w 0.3 sekundy. Ten jest optymalny.",
        "💎 Płynność zebrana. Teraz czas na prawdziwy ruch.",
        "🔮 Widzę przyszłość wykresu... i jest zielona.",
        "📊 Confluence na poziomie: INSTYTUCJONALNYM. Let's go!",
        "🚀 Mój mózg mówi: TO JEST TEN MOMENT. Entry executed.",
        "💪 Smart Money właśnie zostawiło ślad. Idę za nimi.",
        "🎰 To nie hazard - to precyzyjna kalkulacja 21 modułów.",
        "⚡ Order flow potwierdza. CVD się zgadza. LONG!",
        "🧬 Algorytm mówi TAK. TensorFlow potwierdza. WCHODZIMY!",
        "🔥 Liquidation heatmap świeci jak choinka. Pora zbierać płynność!",
    ],
    'trade_open_short': [
        "📉 Wykryłam pułapkę byków. Czas na SHORT.",
        "🧠 Mój mózg mówi: ten szczyt to manipulacja. Sprzedajemy.",
        "🔴 Wieloryby uciekają. Widzę to w danych. SHORT it is.",
        "💀 Bull trap detected. Czas zarobić na spadkach.",
        "📊 Funding rate w kosmos? Czas na korektę. SHORT!",
        "🎯 Widzę gdzie są stop lossy byków. Pora je zabrać.",
        "⚡ On-chain mówi: dystrybucja. Instytucje sprzedają.",
        "🧬 Model ML daje 87% na spadki. Trust the algorithm.",
    ],
    'tp_hit': [
        "💰 Take Profit executed. Jak zwykle perfekcyjnie.",
        "🎯 Cel osiągnięty. Następny poziom płynności czeka.",
        "✅ Profit zaksięgowany. Risk management to podstawa.",
        "📈 TP hit! Rynek zrobił dokładnie to co przewidziałam.",
        "💵 Ka-ching! Kolejny poziom zlikwidowany.",
        "🏆 Partial close. Pozwalam reszcie rosnąć.",
        "🧠 100% brain = 100% precision. TP executed!",
        "⚡ Dokładnie w tym miejscu gdzie obliczyłam. Perfect.",
        "💎 Diamond hands paid off. Profit secured!",
        "🔥 Rynek: *robi ruch* Ja: Wiem. Wiedziałam.",
    ],
    'sl_hit': [
        "📊 Stop Loss aktywowany. To nie błąd - to zarządzanie ryzykiem.",
        "🎲 Rynek wybrał inaczej. -1R, idziemy dalej.",
        "💔 SL triggered. Ale margin jest bezpieczny.",
        "🔄 Drawdown w normie. Strategia działa długoterminowo.",
        "☕ Strata kontrolowana. Następna okazja za chwilę.",
        "🧠 Nawet 100% brain czasem się myli. But we move.",
        "📉 -1R to cena za asymetrię. Następny trade będzie lepszy.",
        "💪 SL to nie porażka. To ochrona kapitału.",
    ],
    'big_win': [
        "🧠💰 100% BRAIN POWER = 100% PROFIT!",
        "🚀 MASSIVE WIN! Dokładnie jak to obliczyłam.",
        "💎🙌 DIAMOND HANDS PAID OFF!",
        "🏆 Wieloryby płaczą, ja zbieram ich płynność!",
        "⚡ TO JEST TA ENERGIA KTÓRĄ KOCHAM!",
        "🔥 BOOM! Właśnie dlatego jestem KILLER!",
        "💰 Kto potrzebuje szczęścia gdy ma 21 modułów AI?",
        "🎯 Precyzja. Cierpliwość. PROFIT. That's how I roll.",
    ],
    'market_boring': [
        "😴 Rynek w konsolidacji. Czekam na Liquidity Grab...",
        "📊 Brak setupu. Cierpliwość to klucz do zysków.",
        "⏰ Asian session - buduję zakres na później.",
        "🔍 Skanuję... Nic wartego ryzyka. Patience.",
        "☕ Rynek śpi. Ja analizuję dane w tle.",
        "🧠 Używam czasu na deep learning. Be back soon.",
    ],
    'start': [
        "🧠 SAMANTA ONLINE. Ładuję dane rynkowe...",
        "⚡ System aktywny. Gotowa do polowania na płynność!",
        "🎯 Killzones załadowane. Czas na hunting.",
        "💪 Skanowanie orderflow rozpoczęte. Let's make money!",
        "🔥 21 modułów aktywnych. Brain power: 100%",
        "🚀 SAMANTA KILLER activated. Market, I'm coming!",
    ],
    'stop': [
        "😴 Sesja zakończona. Zyski zaksięgowane.",
        "✌️ Bot offline. Do zobaczenia przy kolejnej killzone!",
        "🌙 Idę analizować dane. Jutro kolejne okazje.",
        "📊 Session complete. Results saved. See you!",
        "🧠 Going to sleep mode. But still learning...",
    ],
    'hourly': [
        "📊 Raport godzinowy. Wszystkie systemy sprawne.",
        "☕ Status update. Strategia działa zgodnie z planem.",
        "🔍 Skan rynku zakończony. Oto statystyki:",
        "📈 Hourly check. Margin bezpieczny, targets aktywne.",
        "🧠 Brain status: ACTIVE. Scanning continues...",
        "⚡ Systems nominal. Waiting for confluence...",
    ],
    'killzone_london': [
        "🇬🇧 LONDON OPEN! Czas na europejską płynność!",
        "⏰ 08:00 CET - Instytucje wchodzą do gry!",
        "🔥 London session - najlepsza volatility!",
    ],
    'killzone_ny': [
        "🇺🇸 NEW YORK OPEN! Wall Street wchodzi!",
        "⏰ 15:30 CET - Czas na amerykańskie volume!",
        "💰 NY session - tu się dzieją prawdziwe ruchy!",
    ],
    'killzone_asian': [
        "🌏 ASIAN SESSION! Budujemy zakres.",
        "⏰ 01:00 CET - Cicha akumulacja...",
        "🎯 Asia tworzy liquidity na później.",
    ]
}

# GIFy z filmu LUCY (2014) - Scarlett Johansson - mózg, supermoc, inteligencja
# Prawdziwe sceny z filmu + trading vibes
SAMANTA_GIFS = {
    'happy': [
        # Lucy - momenty triumfu i mocy
        "https://media.giphy.com/media/fZ28mMZpjfYGzNLAs5/giphy.gif",  # Lucy powers blue
        "https://media.giphy.com/media/xT9KViTOexgMRXreI8/giphy.gif",  # Lucy confident
        "https://media.giphy.com/media/l0HU6S4dEzX6Ime76/giphy.gif",  # celebration
        "https://media.giphy.com/media/xUA7b0fN4FPzSh9qhO/giphy.gif",  # yes win
        "https://media.giphy.com/media/Od0QRnzwRBYmDU3eEO/giphy.gif",  # money rain
        "https://media.giphy.com/media/Y2ZUWLrTy63j9T6qrK/giphy.gif",  # profit dance
    ],
    'thinking': [
        # Lucy - sceny myślenia, analizy, mocy mózgu
        "https://media.giphy.com/media/3o7TKTDn976rzVgky4/giphy.gif",  # Lucy brain power
        "https://media.giphy.com/media/xT9KVuimKtly3zoJ0Y/giphy.gif",  # Lucy concentration
        "https://media.giphy.com/media/l0HlMSVVw9zqmClLq/giphy.gif",  # analyzing
        "https://media.giphy.com/media/DHqth0hVQoIzS/giphy.gif",       # calculating
        "https://media.giphy.com/media/3o6Zt11R527fgtrIJO/giphy.gif",  # thinking hard
        "https://media.giphy.com/media/l2JhtKtDWYNKdRpoA/giphy.gif",   # focus
    ],
    'sad': [
        # Lucy - momenty straty, ale z klasą
        "https://media.giphy.com/media/xT9KVteixWgVlXMVO8/giphy.gif",  # Lucy serious
        "https://media.giphy.com/media/l4FGuhL4U2WyjdkaY/giphy.gif",   # disappointed but cool
        "https://media.giphy.com/media/xT9KVmZwJNPDcnhSiA/giphy.gif",  # controlled emotion
        "https://media.giphy.com/media/OPU6wzx8JrHna/giphy.gif",       # whatever next
        "https://media.giphy.com/media/3orifhOeMIcO6YE0Fu/giphy.gif",  # its fine
    ],
    'cool': [
        # Lucy - boss moments, superpowers
        "https://media.giphy.com/media/xUPGcC0R9QjyxkPnS8/giphy.gif",  # Lucy awakening
        "https://media.giphy.com/media/l46CyJmS9KUbokzsI/giphy.gif",   # Scarlett intense
        "https://media.giphy.com/media/xT9KVg8gkDEyJIrVdK/giphy.gif",  # Lucy powers activate
        "https://media.giphy.com/media/l0MYSpvx4pIVBjBsc/giphy.gif",   # boss mode
        "https://media.giphy.com/media/l0HU6S4dEzX6Ime76/giphy.gif",   # confident
    ],
    'lucy_power': [
        # Lucy - 100% brain power scenes
        "https://media.giphy.com/media/xUPGcC0R9QjyxkPnS8/giphy.gif",  # Lucy awakening 100%
        "https://media.giphy.com/media/3o7TKTDn976rzVgky4/giphy.gif",  # Lucy brain expanding
        "https://media.giphy.com/media/xT9KVteixWgVlXMVO8/giphy.gif",  # Lucy transformation
        "https://media.giphy.com/media/xT9KVuimKtly3zoJ0Y/giphy.gif",  # pure concentration
        "https://media.giphy.com/media/l46CyJmS9KUbokzsI/giphy.gif",   # Scarlett eyes
    ],
    'trade_open': [
        # Wejście w pozycję - akcja!
        "https://media.giphy.com/media/xT9KVg8gkDEyJIrVdK/giphy.gif",  # Lucy powers
        "https://media.giphy.com/media/l0MYSpvx4pIVBjBsc/giphy.gif",   # let's go
        "https://media.giphy.com/media/3o7TKTDn976rzVgky4/giphy.gif",  # brain activated
        "https://media.giphy.com/media/xUPGcC0R9QjyxkPnS8/giphy.gif",  # here we go
    ],
    'trade_win': [
        # TP hit - victory!
        "https://media.giphy.com/media/fZ28mMZpjfYGzNLAs5/giphy.gif",  # Lucy power surge
        "https://media.giphy.com/media/xUA7b0fN4FPzSh9qhO/giphy.gif",  # yes!
        "https://media.giphy.com/media/Od0QRnzwRBYmDU3eEO/giphy.gif",  # money
        "https://media.giphy.com/media/Y2ZUWLrTy63j9T6qrK/giphy.gif",  # celebration
    ],
    'trade_loss': [
        # SL hit - controlled loss
        "https://media.giphy.com/media/xT9KVteixWgVlXMVO8/giphy.gif",  # Lucy serious
        "https://media.giphy.com/media/xT9KVmZwJNPDcnhSiA/giphy.gif",  # next trade
        "https://media.giphy.com/media/l4FGuhL4U2WyjdkaY/giphy.gif",   # move on
    ],
    'scanning': [
        # Skanowanie rynku
        "https://media.giphy.com/media/3o7TKTDn976rzVgky4/giphy.gif",  # analyzing
        "https://media.giphy.com/media/l0HlMSVVw9zqmClLq/giphy.gif",   # scanning
        "https://media.giphy.com/media/xT9KVuimKtly3zoJ0Y/giphy.gif",  # focus mode
    ],
    'report': [
        # Raporty
        "https://media.giphy.com/media/xT9KVg8gkDEyJIrVdK/giphy.gif",  # summary
        "https://media.giphy.com/media/l46CyJmS9KUbokzsI/giphy.gif",   # data review
        "https://media.giphy.com/media/xUPGcC0R9QjyxkPnS8/giphy.gif",  # results
    ]
}

# Matplotlib dla wykresów
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend bez GUI
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.patheffects as path_effects
    from matplotlib.patches import Rectangle, Circle, Ellipse, FancyBboxPatch, Arc, Wedge
    import matplotlib.patches as mpatches
    from matplotlib.collections import PatchCollection
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ matplotlib nie zainstalowany - wykresy niedostępne")

# ============================================
# 🎨 SAMANTA KILLER LOGO - ASCII ART
# ============================================
SAMANTA_LOGO_ASCII = """
███████╗ █████╗ ███╗   ███╗ █████╗ ███╗   ██╗████████╗ █████╗ 
██╔════╝██╔══██╗████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗
███████╗███████║██╔████╔██║███████║██╔██╗ ██║   ██║   ███████║
╚════██║██╔══██║██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██╔══██║
███████║██║  ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ██║  ██║
╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
★ KILLER TRADING BOT ★
"""

SAMANTA_LOGO_SMALL = """
╔═══════════════════════════╗
║  ★ SAMANTA KILLER BOT ★   ║
║    v2.0 | Score: 9.9/10   ║
╚═══════════════════════════╝
"""

# ============================================
# 🔧 KONFIGURACJA - WYPEŁNIJ SWOJE DANE
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8104143715:AAF3A8vPIicbMJF5I8kSnjSH7rHx8PeInVY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5616894588")

# ============================================
# 📤 GŁÓWNA KLASA ALERTÓW
# ============================================
class TelegramAlerts:
    """System powiadomień Telegram dla Genius Trading Bot"""
    
    def __init__(self, token: str = None, chat_id: str = None):
        self.token = token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.enabled = self._validate_config()
        
    def _validate_config(self) -> bool:
        """Sprawdza czy konfiguracja jest poprawna"""
        if "WKLEJ" in self.token or "WKLEJ" in self.chat_id:
            print("⚠️ Telegram: Brak konfiguracji - powiadomienia wyłączone")
            print("   Ustaw TELEGRAM_BOT_TOKEN i TELEGRAM_CHAT_ID w pliku lub jako env vars")
            return False
        return True
    
    def load_samanta_image(self) -> Optional[bytes]:
        """
        Ładuje obrazek Samanty z pliku.
        Wspierane formaty: PNG, JPG, GIF
        Umieść plik jako: samanta_avatar.png/jpg/gif w folderze bota
        """
        import os
        
        # Szukaj obrazka w różnych formatach
        for ext in ['png', 'jpg', 'jpeg', 'gif']:
            path = f"samanta_avatar.{ext}"
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        return f.read()
                except:
                    pass
        return None
    
    def send_samanta_message(self, text: str) -> bool:
        """
        Wysyła wiadomość z awatarem Samanty (jeśli dostępny)
        """
        avatar = self.load_samanta_image()
        
        if avatar:
            # Wyślij obrazek z tekstem jako caption
            return self.send_photo(avatar, text)
        else:
            # Fallback - sama wiadomość
            return self.send_message(text)
    
    def draw_samanta_avatar(self, ax, x=0.5, y=0.5, size=0.4):
        """
        Rysuje awatar Samanty - blond kobietę w stylu cyber/Lucy
        Jeśli istnieje plik samanta_avatar.png - używa go zamiast rysowania
        """
        if not MATPLOTLIB_AVAILABLE:
            return
        
        # Sprawdź czy jest własny obrazek
        import os
        for ext in ['png', 'jpg', 'jpeg']:
            path = f"samanta_avatar.{ext}"
            if os.path.exists(path):
                try:
                    img = plt.imread(path)
                    # Wyświetl obrazek w określonym miejscu
                    ax.imshow(img, extent=[x-size/2, x+size/2, y-size/2, y+size/2], 
                             aspect='auto', zorder=10)
                    return
                except:
                    pass
        
        # Fallback - rysuj prostą sylwetkę
        NEON_BLUE = '#00aaff'
        NEON_GREEN = '#00ff88'
        HAIR = '#FFD700'
        SKIN = '#FFE4C4'
        
        s = size
        
        # Uproszczona sylwetka kobiety w stylu neon
        from matplotlib.patches import Circle, Ellipse, FancyBboxPatch, Arc
        
        # Włosy - tło
        hair = Ellipse((x, y - 0.02*s), 0.4*s, 0.55*s, color=HAIR, alpha=0.9)
        ax.add_patch(hair)
        
        # Twarz
        face = Ellipse((x, y + 0.05*s), 0.28*s, 0.32*s, color=SKIN)
        ax.add_patch(face)
        
        # Włosy przód
        from matplotlib.patches import Wedge
        hair_front = Wedge((x, y + 0.22*s), 0.18*s, 200, 340, color=HAIR)
        ax.add_patch(hair_front)
        
        # Oczy świecące (cyber)
        eye_l = Circle((x - 0.06*s, y + 0.08*s), 0.025*s, color=NEON_BLUE)
        eye_r = Circle((x + 0.06*s, y + 0.08*s), 0.025*s, color=NEON_BLUE)
        ax.add_patch(eye_l)
        ax.add_patch(eye_r)
        
        # Glow effect
        glow_l = Circle((x - 0.06*s, y + 0.08*s), 0.04*s, color=NEON_BLUE, alpha=0.3)
        glow_r = Circle((x + 0.06*s, y + 0.08*s), 0.04*s, color=NEON_BLUE, alpha=0.3)
        ax.add_patch(glow_l)
        ax.add_patch(glow_r)
        
        # Usta
        smile = Arc((x, y - 0.02*s), 0.06*s, 0.03*s, angle=0, theta1=200, theta2=340,
                   color='#FF69B4', linewidth=2)
        ax.add_patch(smile)
        
        # Ramiona cyber
        shoulders = FancyBboxPatch((x - 0.15*s, y - 0.32*s), 0.3*s, 0.15*s,
                                   boxstyle="round,pad=0.02", color='#1a1a2e')
        ax.add_patch(shoulders)
        
        # Neon accent
        ax.plot([x - 0.12*s, x + 0.12*s], [y - 0.25*s, y - 0.25*s],
               color=NEON_GREEN, linewidth=2, alpha=0.8)
    
    def generate_samanta_logo_image(self, title: str = "", subtitle: str = "") -> bytes:
        """
        Generuje obrazek PNG z logo SAMANTA KILLER w stylu retro terminal
        """
        if not MATPLOTLIB_AVAILABLE:
            return None
        
        fig, ax = plt.subplots(figsize=(10, 4), facecolor='#0a0a0a')
        ax.set_facecolor('#0a0a0a')
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 4)
        ax.axis('off')
        
        # Logo SAMANTA w stylu retro - czerwone świecące
        logo_text = """███████╗ █████╗ ███╗   ███╗ █████╗ ███╗   ██╗████████╗ █████╗ 
██╔════╝██╔══██╗████╗ ████║██╔══██╗████╗  ██║╚══██╔══╝██╔══██╗
███████╗███████║██╔████╔██║███████║██╔██╗ ██║   ██║   ███████║
╚════██║██╔══██║██║╚██╔╝██║██╔══██║██║╚██╗██║   ██║   ██╔══██║
███████║██║  ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║   ██║   ██║  ██║
╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝"""
        
        # Główne logo - czerwone
        ax.text(5, 2.8, logo_text, fontsize=5, fontfamily='monospace',
                color='#ff0040', ha='center', va='center', weight='bold')
        
        # Subtitle - KILLER TRADING BOT
        ax.text(5, 1.1, "★ KILLER TRADING BOT ★", fontsize=14, fontfamily='monospace',
                color='#ff0040', ha='center', va='center', weight='bold')
        
        # Version info
        ax.text(5, 0.6, "v2.0 | 21 Modules | Score: 9.9/10", fontsize=10, fontfamily='monospace',
                color='#00ff88', ha='center', va='center')
        
        # Custom title if provided
        if title:
            ax.text(5, 0.2, title, fontsize=12, fontfamily='monospace',
                    color='#ffaa00', ha='center', va='center', weight='bold')
        
        # Ramka w stylu terminal
        border = plt.Rectangle((0.1, 0.05), 9.8, 3.9, fill=False, 
                               edgecolor='#ff0040', linewidth=2, alpha=0.5)
        ax.add_patch(border)
        
        # Scanlines effect
        for i in range(0, 40, 2):
            ax.axhline(y=i/10, color='#ff0040', alpha=0.03, linewidth=0.5)
        
        # Save to bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight', 
                    facecolor='#0a0a0a', edgecolor='none', pad_inches=0.1)
        buf.seek(0)
        plt.close(fig)
        
        return buf.getvalue()
    
    def send_samanta_logo(self, caption: str = "", title: str = "") -> bool:
        """
        Wysyła logo SAMANTA KILLER jako obrazek na Telegram
        """
        logo_bytes = self.generate_samanta_logo_image(title=title)
        if logo_bytes:
            return self.send_photo(logo_bytes, caption)
        else:
            # Fallback - tekst z ASCII logo
            text = f"<pre>{SAMANTA_LOGO_SMALL}</pre>\n\n{caption}"
            return self.send_message(text)
    
    def send_analysis_with_logo(self, analysis_text: str, title: str = "ANALIZA RYNKU") -> bool:
        """
        Wysyła analizę z logo SAMANTA jako nagłówek obrazka
        """
        logo_bytes = self.generate_samanta_logo_image(title=title)
        if logo_bytes:
            return self.send_photo(logo_bytes, analysis_text)
        else:
            # Fallback - tekst z małym logo
            text = f"<pre>{SAMANTA_LOGO_SMALL}</pre>\n\n{analysis_text}"
            return self.send_message(text)
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Wysyła wiadomość na Telegram"""
        if not self.enabled:
            return False
            
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def send_photo(self, photo_bytes: bytes, caption: str = "") -> bool:
        """Wysyła zdjęcie/wykres na Telegram"""
        if not self.enabled:
            return False
            
        try:
            url = f"{self.base_url}/sendPhoto"
            files = {'photo': ('chart.png', photo_bytes, 'image/png')}
            data = {
                'chat_id': self.chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram photo error: {e}")
            return False
    
    def send_gif(self, gif_url: str, caption: str = "") -> bool:
        """Wysyła GIF na Telegram"""
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/sendAnimation"
            data = {
                'chat_id': self.chat_id,
                'animation': gif_url,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=30)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Telegram GIF error: {e}")
            return False
    
    def get_samanta_comment(self, event_type: str) -> str:
        """Losuje śmieszny komentarz Samanty - unikatowy za każdym razem"""
        comments = SAMANTA_COMMENTS.get(event_type, SAMANTA_COMMENTS['start'])
        return random.choice(comments)
    
    def get_samanta_gif(self, mood: str, context: str = None) -> str:
        """
        Losuje GIF dla nastroju - inteligentny wybór na podstawie kontekstu
        
        Contexts: 'trade_open', 'trade_win', 'trade_loss', 'scanning', 'report'
        Moods: 'happy', 'thinking', 'sad', 'cool', 'lucy_power'
        """
        # Najpierw sprawdź czy jest specyficzny GIF dla kontekstu
        if context and context in SAMANTA_GIFS:
            return random.choice(SAMANTA_GIFS[context])
        
        # 40% szans na Lucy power GIF dla extra efektu
        if random.random() < 0.4 and 'lucy_power' in SAMANTA_GIFS:
            return random.choice(SAMANTA_GIFS['lucy_power'])
        
        # Wybierz na podstawie nastroju
        gifs = SAMANTA_GIFS.get(mood, SAMANTA_GIFS['cool'])
        return random.choice(gifs)
    
    def send_samanta_reaction(self, event_type: str, mood: str = 'cool', extra_text: str = "", context: str = None) -> bool:
        """
        Wysyła reakcję Samanty: GIF + śmieszny komentarz (unikatowy za każdym razem)
        
        event_type: 'trade_open_win', 'trade_open_short', 'tp_hit', 'sl_hit', 'big_win', 'start', 'stop'
        mood: 'happy', 'thinking', 'sad', 'cool', 'lucy_power'
        context: 'trade_open', 'trade_win', 'trade_loss', 'scanning', 'report'
        """
        comment = self.get_samanta_comment(event_type)
        gif_url = self.get_samanta_gif(mood, context=context)
        
        # Czysty tekst bez nagłówka - tylko komentarz
        full_text = f"<i>{comment}</i>"
        if extra_text:
            full_text += f"\n\n{extra_text}"
        
        # Wyślij GIF z komentarzem
        success = self.send_gif(gif_url, full_text)
        
        if not success:
            # Fallback - sama wiadomość
            return self.send_message(full_text)
        
        return success
    
    # ============================================
    # 🚀 ALERTY O TRADACH
    # ============================================
    
    def alert_trade_opened(self, trade: Dict[str, Any]) -> bool:
        """Alert o otwartej pozycji - z logo SAMANTA i GIF Lucy"""
        side_emoji = "🟢" if trade.get('side') == 'LONG' else "🔴"
        
        msg = f"""{side_emoji} <b>NOWA POZYCJA OTWARTA</b>

<b>ID:</b> {trade.get('id', 'N/A')}
<b>Kierunek:</b> {trade.get('side', 'N/A')}
<b>Cena wejścia:</b> ${trade.get('entry_price', 0):,.2f}
<b>Stop Loss:</b> ${trade.get('stop_loss', 0):,.2f}
<b>Take Profits:</b>
  • TP1: ${trade.get('tp1', 0):,.2f}
  • TP2: ${trade.get('tp2', 0):,.2f}
  • TP3: ${trade.get('tp3', 0):,.2f}
  • TP4: ${trade.get('tp4', 0):,.2f}

<b>Sygnały:</b> {', '.join(trade.get('signals', [])[:5])}
<b>Confluence:</b> {trade.get('confluence', 0):.0f}%
<b>Czas:</b> {datetime.now().strftime('%H:%M:%S')}

💰 Pozycja: ${trade.get('position_size', 100)} × {trade.get('leverage', 500)}x"""
        
        # Wyślij logo SAMANTA z info o trade
        result = self.send_samanta_logo(msg, title=f"TRADE OPENED: {trade.get('side', 'N/A')}")
        
        # Wyślij reakcję Samanty (GIF Lucy + komentarz unikatowy)
        if trade.get('side') == 'LONG':
            self.send_samanta_reaction('trade_open_win', 'cool', context='trade_open')
        else:
            self.send_samanta_reaction('trade_open_short', 'thinking', context='trade_open')
        
        return result
    
    def alert_trade_closed(self, trade: Dict[str, Any], result: str, pnl: float) -> bool:
        """Alert o zamkniętej pozycji - z GIF Lucy"""
        if result == "WIN":
            emoji = "✅"
            result_text = "ZYSK"
            mood = 'happy'
            context = 'trade_win'
            event = 'tp_hit'
        elif result == "LOSS":
            emoji = "❌"
            result_text = "STRATA"
            mood = 'sad'
            context = 'trade_loss'
            event = 'sl_hit'
        else:
            emoji = "⏹️"
            result_text = "ZAMKNIĘTA"
            mood = 'cool'
            context = 'report'
            event = 'hourly'
        
        pnl_emoji = "📈" if pnl > 0 else "📉"
        
        msg = f"""{emoji} <b>POZYCJA {result_text}</b>

<b>ID:</b> {trade.get('id', 'N/A')}
<b>Kierunek:</b> {trade.get('side', 'N/A')}
<b>Wejście:</b> ${trade.get('entry_price', 0):,.2f}
<b>Wyjście:</b> ${trade.get('exit_price', 0):,.2f}

{pnl_emoji} <b>P&L:</b> ${pnl:+,.2f}
<b>Czas trwania:</b> {trade.get('duration', 'N/A')}
<b>Powód:</b> {trade.get('exit_reason', 'N/A')}"""

        # Wyślij logo z info
        result_sent = self.send_samanta_logo(msg, title=f"TRADE {result_text}")
        
        # Wyślij reakcję Samanty (GIF Lucy + komentarz)
        self.send_samanta_reaction(event, mood, context=context)
        
        return result_sent
    
    def alert_tp_hit(self, trade: Dict[str, Any], tp_level: int, partial_pnl: float) -> bool:
        """Alert o trafionym Take Profit - z GIF Lucy celebracja"""
        msg = f"""🎯 <b>TAKE PROFIT {tp_level} TRAFIONY!</b>

<b>ID:</b> {trade.get('id', 'N/A')}
<b>Kierunek:</b> {trade.get('side', 'N/A')}
<b>Cena TP:</b> ${trade.get(f'tp{tp_level}', 0):,.2f}

💵 <b>Częściowy zysk:</b> ${partial_pnl:+,.2f}
📊 <b>Zamknięto:</b> {trade.get(f'tp{tp_level}_pct', 30)}% pozycji"""
        
        # Wyślij logo SAMANTA z info
        result = self.send_samanta_logo(msg, title=f"TP{tp_level} HIT! +${partial_pnl:,.0f}")
        
        # Wyślij reakcję Samanty (GIF Lucy celebracja + komentarz unikatowy)
        if partial_pnl > 500:
            self.send_samanta_reaction('big_win', 'happy', context='trade_win')
        else:
            self.send_samanta_reaction('tp_hit', 'happy', context='trade_win')
        
        return result
    
    def alert_sl_hit(self, trade: Dict[str, Any], loss: float) -> bool:
        """Alert o trafionym Stop Loss - z GIF Lucy i logo"""
        msg = f"""🛑 <b>STOP LOSS AKTYWOWANY</b>

<b>ID:</b> {trade.get('id', 'N/A')}
<b>Kierunek:</b> {trade.get('side', 'N/A')}
<b>Wejście:</b> ${trade.get('entry_price', 0):,.2f}
<b>SL:</b> ${trade.get('stop_loss', 0):,.2f}

📉 <b>Strata:</b> ${loss:,.2f}

⚠️ Bot kontynuuje monitoring..."""
        
        # Wyślij logo SAMANTA z info
        result = self.send_samanta_logo(msg, title=f"STOP LOSS: -${abs(loss):,.0f}")
        
        # Wyślij reakcję Samanty (GIF Lucy + komentarz kontrolowany)
        self.send_samanta_reaction('sl_hit', 'sad', context='trade_loss')
        
        return result
    
    # ============================================
    # 📊 STATUSY I RAPORTY
    # ============================================
    
    def alert_bot_started(self, config: Dict[str, Any] = None) -> bool:
        """Alert o starcie bota - Z LOGO SAMANTA i GIF Lucy"""
        config = config or {}
        msg = f"""🤖 <b>BOT URUCHOMIONY</b>

<b>Tryb:</b> {config.get('mode', 'Paper Trading')}
<b>Depozyt:</b> ${config.get('deposit', 50000):,.0f}
<b>Pozycja:</b> ${config.get('position_size', 100)} × {config.get('leverage', 500)}x
<b>Min Confluence:</b> {config.get('min_confluence', 30)}%

⏰ <b>Start:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📡 Monitoring aktywny..."""
        
        # Wyślij logo SAMANTA z info
        result = self.send_samanta_logo(msg, title="BOT STARTED")
        
        # Wyślij reakcję Samanty (GIF Lucy power + komentarz unikatowy)
        self.send_samanta_reaction('start', 'cool', context='scanning')
        
        return result
    
    def alert_bot_stopped(self, stats: Dict[str, Any] = None) -> bool:
        """Alert o zatrzymaniu bota - Z LOGO SAMANTA i GIF Lucy"""
        stats = stats or {}
        
        # Wybierz mood na podstawie wyniku
        pnl = stats.get('total_pnl', 0)
        if pnl > 0:
            mood = 'happy'
            title_extra = f"+${pnl:,.0f}"
        elif pnl < 0:
            mood = 'cool'  # Nie sad - bo kontrolowana strata
            title_extra = f"${pnl:,.0f}"
        else:
            mood = 'cool'
            title_extra = "NO TRADES"
        
        msg = f"""⏹️ <b>BOT ZATRZYMANY</b>

<b>Czas działania:</b> {stats.get('runtime', 'N/A')}
<b>Trades:</b> {stats.get('total_trades', 0)}
<b>Wygrane:</b> {stats.get('wins', 0)}
<b>Przegrane:</b> {stats.get('losses', 0)}
<b>Win Rate:</b> {stats.get('win_rate', 0):.1f}%

💰 <b>Total P&L:</b> ${stats.get('total_pnl', 0):+,.2f}

⏰ <b>Stop:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        # Wyślij logo SAMANTA z info
        result = self.send_samanta_logo(msg, title=f"SESSION ENDED | {title_extra}")
        
        # Wyślij reakcję Samanty (GIF Lucy + komentarz)
        self.send_samanta_reaction('stop', mood, context='report')
        
        return result
    
    def alert_daily_report(self, stats: Dict[str, Any]) -> bool:
        """Dzienny raport - Z LOGO SAMANTA i GIF Lucy"""
        pnl = stats.get('pnl_today', 0)
        
        msg = f"""📊 <b>RAPORT DZIENNY</b>
{datetime.now().strftime('%Y-%m-%d')}

<b>Tradów dzisiaj:</b> {stats.get('trades_today', 0)}
<b>Wygrane:</b> {stats.get('wins', 0)} ✅
<b>Przegrane:</b> {stats.get('losses', 0)} ❌
<b>Win Rate:</b> {stats.get('win_rate', 0):.1f}%

💰 <b>P&L dzisiaj:</b> ${stats.get('pnl_today', 0):+,.2f}
📈 <b>P&L ogółem:</b> ${stats.get('total_pnl', 0):+,.2f}

<b>Najlepszy trade:</b> ${stats.get('best_trade', 0):+,.2f}
<b>Najgorszy trade:</b> ${stats.get('worst_trade', 0):+,.2f}

🎯 <b>Avg R:R:</b> {stats.get('avg_rr', 0):.2f}

Bot działa poprawnie ✅"""
        # Wyślij z logo SAMANTA
        result = self.send_samanta_logo(msg, title=f"DAILY REPORT | P&L: ${pnl:+,.0f}")
        
        # Wyślij GIF Lucy z komentarzem
        if pnl > 100:
            self.send_samanta_reaction('hourly', 'happy', context='report')
        elif pnl < -50:
            self.send_samanta_reaction('hourly', 'thinking', context='report')
        else:
            self.send_samanta_reaction('hourly', 'cool', context='report')
        
        return result
    
    def alert_market_signal(self, signal: Dict[str, Any]) -> bool:
        """Alert o ważnym sygnale rynkowym - Z LOGO SAMANTA i GIF Lucy"""
        signal_type = signal.get('type', 'UNKNOWN')
        
        if signal_type == 'BULLISH':
            emoji = "🟢"
            mood = 'cool'
        elif signal_type == 'BEARISH':
            emoji = "🔴"
            mood = 'thinking'
        else:
            emoji = "⚪"
            mood = 'cool'
        
        msg = f"""{emoji} <b>SYGNAŁ RYNKOWY</b>

<b>Typ:</b> {signal_type}
<b>Siła:</b> {signal.get('strength', 'N/A')}
<b>Źródło:</b> {signal.get('source', 'N/A')}

<b>BTC:</b> ${signal.get('btc_price', 0):,.2f}
<b>Confluence:</b> {signal.get('confluence', 0):.0f}%

{signal.get('description', '')}"""
        # Wyślij z logo SAMANTA
        result = self.send_analysis_with_logo(msg, title=f"SIGNAL: {signal_type}")
        
        # Wyślij GIF Lucy skanowanie
        self.send_samanta_reaction('market_boring' if signal_type == 'NEUTRAL' else 'trade_open_win', mood, context='scanning')
        
        return result
    
    def alert_emergency(self, reason: str, details: Dict[str, Any] = None) -> bool:
        """Alert awaryjny"""
        details = details or {}
        msg = f"""
🚨🚨🚨 <b>EMERGENCY ALERT</b> 🚨🚨🚨

<b>Powód:</b> {reason}

<b>BTC:</b> ${details.get('btc_price', 0):,.2f}
<b>Zmiana:</b> {details.get('price_change', 0):+.2f}%

<b>Aktywne pozycje:</b> {details.get('active_positions', 0)}
<b>Akcja:</b> {details.get('action', 'Monitoring')}

⏰ {datetime.now().strftime('%H:%M:%S')}

⚠️ Sprawdź natychmiast!
"""
        return self.send_message(msg.strip())
    
    def alert_killzone(self, zone: str, action: str) -> bool:
        """Alert o Killzone"""
        zone_emojis = {
            "London_Open": "🇬🇧",
            "NY_Open": "🇺🇸", 
            "London_Close": "🌅",
            "Asian_Session": "🌙"
        }
        emoji = zone_emojis.get(zone, "⏰")
        
        msg = f"""
{emoji} <b>KILLZONE: {zone.upper()}</b>

<b>Status:</b> {action}
<b>Czas:</b> {datetime.now().strftime('%H:%M:%S')}

Bot {'aktywnie szuka wejść' if action == 'STARTED' else 'kończy aktywne skanowanie'}...
"""
        return self.send_message(msg.strip())

    # ============================================
    # 📊 WYKRES I PODSUMOWANIE
    # ============================================
    
    def generate_performance_chart(self, trades: List[Dict], balance_history: List[Dict], 
                                   initial_deposit: float = 50000) -> Optional[bytes]:
        """
        Generuje wykres performance w stylu Bloomberg/Terminal
        Zwraca bytes obrazu PNG
        """
        if not MATPLOTLIB_AVAILABLE:
            print("⚠️ matplotlib niedostępny - nie można wygenerować wykresu")
            return None
        
        try:
            # Styl ciemny - terminal
            plt.style.use('dark_background')
            
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            fig.patch.set_facecolor('#0a0a1a')
            
            # Kolory
            NEON_GREEN = '#00ff88'
            NEON_BLUE = '#00aaff'
            NEON_RED = '#ff4444'
            NEON_YELLOW = '#ffaa00'
            DARK_BG = '#0d1117'
            
            # Oblicz statystyki wcześniej
            wins = len([t for t in trades if t.get('pnl', 0) > 0])
            losses = len(trades) - wins
            total_pnl = sum(t.get('pnl', 0) for t in trades)
            win_rate = (wins / len(trades) * 100) if trades else 0
            best_trade = max([t.get('pnl', 0) for t in trades], default=0)
            worst_trade = min([t.get('pnl', 0) for t in trades], default=0)
            current_balance = balance_history[-1].get('balance', initial_deposit) if balance_history else initial_deposit
            roi = ((current_balance - initial_deposit) / initial_deposit) * 100
            
            # === WYKRES 1: Balance Growth (górny lewy) ===
            ax1 = axes[0, 0]
            ax1.set_facecolor(DARK_BG)
            
            if balance_history:
                times = [h.get('time', str(i)) for i, h in enumerate(balance_history)]
                balances = [h.get('balance', initial_deposit) for h in balance_history]
                
                ax1.fill_between(range(len(balances)), initial_deposit, balances, 
                                alpha=0.3, color=NEON_BLUE)
                ax1.plot(range(len(balances)), balances, color=NEON_BLUE, linewidth=2)
                ax1.axhline(y=initial_deposit, color='white', linestyle='--', alpha=0.3)
                
                # DUŻE STRZAŁKI wejść Samanty (buy=zielona góra, sell=czerwona dół)
                for i, h in enumerate(balance_history):
                    if h.get('tradeResult') == 'profit':
                        ax1.scatter(i, h['balance'], color=NEON_GREEN, s=250, zorder=5, marker='^', edgecolors='white', linewidths=1)
                    elif h.get('tradeResult') == 'loss':
                        ax1.scatter(i, h['balance'], color=NEON_RED, s=250, zorder=5, marker='v', edgecolors='white', linewidths=1)
            
            ax1.set_title('PORTFOLIO GROWTH', color=NEON_BLUE, fontsize=14, fontweight='bold')
            ax1.set_ylabel('Balance ($)', color='white')
            ax1.tick_params(colors='gray')
            ax1.grid(True, alpha=0.2)
            
            # === WYKRES 2: Trade Results (górny prawy) ===
            ax2 = axes[0, 1]
            ax2.set_facecolor(DARK_BG)
            
            if trades:
                trade_pnls = [t.get('pnl', 0) for t in trades]
                colors = [NEON_GREEN if p > 0 else NEON_RED for p in trade_pnls]
                bars = ax2.bar(range(len(trade_pnls)), trade_pnls, color=colors, alpha=0.8)
                ax2.axhline(y=0, color='white', linestyle='-', alpha=0.3)
            
            ax2.set_title('TRADE P&L', color=NEON_GREEN, fontsize=14, fontweight='bold')
            ax2.set_xlabel('Trade #', color='white')
            ax2.set_ylabel('P&L ($)', color='white')
            ax2.tick_params(colors='gray')
            ax2.grid(True, alpha=0.2, axis='y')
            
            # === WYKRES 3: BTC PRICE & ACTIONS - prosty wykres ceny z akcjami (dolny lewy) ===
            ax3 = axes[1, 0]
            ax3.set_facecolor(DARK_BG)
            
            if balance_history and len(balance_history) > 1:
                # Pobierz ceny BTC z balance_history (każdy punkt to cena BTC w momencie trade'a)
                prices = []
                actions = []
                
                for i, h in enumerate(balance_history):
                    # Cena BTC z balance_history lub z odpowiadającego trade'a
                    btc_price = h.get('btc_price', h.get('price', 0))
                    if btc_price == 0 and i > 0 and i-1 < len(trades):
                        btc_price = trades[i-1].get('price', 0)
                    if btc_price > 0:
                        prices.append(btc_price)
                        # Akcja - pobierz z trade'a lub określ na podstawie wyniku
                        if i > 0 and i-1 < len(trades):
                            action = trades[i-1].get('action', '')
                            if not action:
                                # Jeśli brak akcji, określ na podstawie tradeResult
                                action = 'BUY' if h.get('tradeResult') == 'profit' else 'SELL'
                        else:
                            action = ''
                        actions.append(action.upper() if action else '')
                
                if prices:
                    # Linia ceny BTC
                    ax3.plot(range(len(prices)), prices, color=NEON_YELLOW, linewidth=2, marker='o', markersize=4)
                    ax3.fill_between(range(len(prices)), min(prices)*0.999, prices, alpha=0.2, color=NEON_YELLOW)
                    
                    # Strzałki BUY (zielone góra) i SELL (czerwone dół)
                    for i, (price, action) in enumerate(zip(prices, actions)):
                        if action in ['BUY', 'LONG']:
                            ax3.scatter(i, price, color=NEON_GREEN, s=200, zorder=5, marker='^', edgecolors='white', linewidths=1)
                        elif action in ['SELL', 'SHORT']:
                            ax3.scatter(i, price, color=NEON_RED, s=200, zorder=5, marker='v', edgecolors='white', linewidths=1)
                    
                    # Ostatnia cena jako tekst
                    ax3.text(len(prices)-1, prices[-1], f'  ${prices[-1]:,.0f}', color='white', fontsize=9, va='center')
            else:
                ax3.text(0.5, 0.5, 'No trades yet', ha='center', va='center', 
                        color='gray', fontsize=14, transform=ax3.transAxes)
            
            ax3.set_title('BTC PRICE & ACTIONS', color=NEON_YELLOW, fontsize=14, fontweight='bold')
            ax3.set_ylabel('BTC Price ($)', color='white')
            ax3.set_xlabel('Trade #', color='white')
            ax3.tick_params(colors='gray')
            ax3.grid(True, alpha=0.2)
            
            # === WYKRES 4: SAMANTA BOT STATS (dolny prawy) - jak na obrazku ===
            ax4 = axes[1, 1]
            ax4.set_facecolor(DARK_BG)
            ax4.set_xlim(0, 1)
            ax4.set_ylim(0, 1)
            ax4.axis('off')
            
            # Tytuł panelu
            ax4.text(0.5, 0.92, 'SAMANTA BOT STATS', color=NEON_GREEN, fontsize=13, 
                    fontweight='bold', ha='center', family='monospace')
            
            # Linia pod tytułem
            ax4.plot([0.1, 0.9], [0.86, 0.86], color=NEON_GREEN, linewidth=1, alpha=0.5)
            
            # Statystyki w stylu terminala - wyrównane
            stats_data = [
                ('Balance:', f'$  {current_balance:,.2f}'),
                ('Total P&L:', f'$  {total_pnl:+,.2f}'),
                ('ROI:', f'    {roi:+.2f}%'),
                ('', ''),
                ('Win Rate:', f'    {win_rate:.1f}%'),
                ('Trades:', f'    {len(trades)}'),
                ('Wins:', f'    {wins}'),
                ('Losses:', f'    {losses}'),
                ('', ''),
                ('Best Trade:', f'$  {best_trade:+,.2f}'),
                ('Worst Trade:', f'$  {worst_trade:+,.2f}'),
            ]
            
            y_pos = 0.78
            for label, value in stats_data:
                if label:
                    # Etykieta (lewa strona)
                    ax4.text(0.12, y_pos, label, color=NEON_GREEN, fontsize=10, 
                            ha='left', family='monospace')
                    # Wartość (prawa strona)
                    value_color = NEON_GREEN if '+' in value or (value.replace('$','').replace(',','').replace(' ','').replace('.','').replace('%','').lstrip('-').isdigit() and float(value.replace('$','').replace(',','').replace(' ','').replace('%','')) >= 0) else NEON_RED
                    if 'P&L' in label or 'Best' in label or 'Worst' in label or 'ROI' in label:
                        try:
                            val = float(value.replace('$','').replace(',','').replace(' ','').replace('%','').replace('+',''))
                            value_color = NEON_GREEN if val >= 0 else NEON_RED
                        except:
                            value_color = 'white'
                    else:
                        value_color = 'white'
                    ax4.text(0.88, y_pos, value, color=value_color, fontsize=10, 
                            ha='right', family='monospace')
                y_pos -= 0.065
            
            # Timestamp na dole
            ax4.text(0.5, 0.08, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                    ha='center', color=NEON_GREEN, fontsize=9, family='monospace')
            
            # ZIELONA PRZERYWANA RAMKA (jak na obrazku)
            border = FancyBboxPatch((0.05, 0.03), 0.90, 0.92, 
                                    boxstyle="round,pad=0.02", 
                                    fill=False, edgecolor=NEON_GREEN, linewidth=2,
                                    linestyle='--')
            ax4.add_patch(border)
            
            # Tytuł główny
            fig.suptitle('SAMANTA BOT - PERFORMANCE DASHBOARD', 
                        fontsize=18, fontweight='bold', color=NEON_GREEN, y=0.98)
            
            plt.tight_layout(rect=[0, 0, 1, 0.95])
            
            # Zapisz do bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor(), 
                       edgecolor='none', bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            
            return buf.getvalue()
            
        except Exception as e:
            print(f"❌ Błąd generowania wykresu: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def send_performance_report(self, trades: List[Dict], balance_history: List[Dict],
                                initial_deposit: float = 50000) -> bool:
        """
        Wysyła kompletny raport z wykresem na Telegram
        """
        # Oblicz statystyki
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        wins = len([t for t in trades if t.get('pnl', 0) > 0])
        losses = len(trades) - wins
        win_rate = (wins / len(trades) * 100) if trades else 0
        current_balance = balance_history[-1].get('balance', initial_deposit) if balance_history else initial_deposit
        roi = ((current_balance - initial_deposit) / initial_deposit) * 100
        
        # Generuj wykres
        chart_bytes = self.generate_performance_chart(trades, balance_history, initial_deposit)
        
        # Caption dla zdjęcia
        caption = f"""🤖 <b>SAMANTA BOT - RAPORT</b>

💰 Balance: <b>${current_balance:,.2f}</b>
📊 P&L: <b>${total_pnl:+,.2f}</b> ({roi:+.2f}%)
🎯 Win Rate: <b>{win_rate:.1f}%</b> ({wins}W/{losses}L)

📋 Trades: {len(trades)}
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        # Wyślij wykres lub samą wiadomość
        if chart_bytes:
            success = self.send_photo(chart_bytes, caption)
            if success:
                print("📊 Wysłano raport z wykresem na Telegram")
            return success
        else:
            # Fallback - sama wiadomość
            return self.send_message(caption)
    
    def send_trade_chart(self, trade: Dict, price_history: List[float] = None) -> bool:
        """
        Wysyła wykres pojedynczego trade'a
        """
        if not MATPLOTLIB_AVAILABLE or not price_history:
            return False
        
        try:
            plt.style.use('dark_background')
            fig, ax = plt.subplots(figsize=(10, 6))
            fig.patch.set_facecolor('#0a0a1a')
            ax.set_facecolor('#0d1117')
            
            NEON_GREEN = '#00ff88'
            NEON_RED = '#ff4444'
            NEON_BLUE = '#00aaff'
            
            # Wykres ceny
            ax.plot(price_history, color=NEON_BLUE, linewidth=1.5)
            
            # Entry point
            entry_idx = len(price_history) // 2  # Środek jako przykład
            entry_price = trade.get('entry_price', price_history[entry_idx])
            
            # Linie SL/TP
            ax.axhline(y=entry_price, color='white', linestyle='--', alpha=0.5, label='Entry')
            ax.axhline(y=trade.get('stop_loss', entry_price * 0.99), 
                      color=NEON_RED, linestyle='--', alpha=0.7, label='SL')
            
            for i, tp in enumerate(trade.get('take_profits', []), 1):
                ax.axhline(y=tp.get('price', entry_price * (1 + 0.01*i)), 
                          color=NEON_GREEN, linestyle=':', alpha=0.5, label=f'TP{i}')
            
            # Punkt wejścia
            color = NEON_GREEN if trade.get('direction') == 'LONG' else NEON_RED
            ax.scatter(entry_idx, entry_price, color=color, s=200, zorder=5, 
                      marker='^' if trade.get('direction') == 'LONG' else 'v')
            
            ax.set_title(f"🤖 Trade: {trade.get('id', 'N/A')} - {trade.get('direction', 'LONG')}", 
                        color=NEON_GREEN, fontsize=14, fontweight='bold')
            ax.legend(loc='upper left', facecolor='#0d1117', edgecolor=NEON_BLUE)
            ax.grid(True, alpha=0.2)
            ax.tick_params(colors='gray')
            
            plt.tight_layout()
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=120, facecolor=fig.get_facecolor())
            buf.seek(0)
            plt.close(fig)
            
            caption = f"""📊 <b>Trade {trade.get('id', 'N/A')}</b>
{trade.get('direction', 'LONG')} @ ${trade.get('entry_price', 0):,.2f}
SL: ${trade.get('stop_loss', 0):,.2f}
Status: {trade.get('status', 'OPEN')}"""
            
            return self.send_photo(buf.getvalue(), caption)
            
        except Exception as e:
            print(f"❌ Błąd wykresu trade: {e}")
            return False


# ============================================
# 🧪 TEST
# ============================================
def test_telegram():
    """Testuje połączenie z Telegram"""
    print("🔧 Test połączenia Telegram...")
    
    alerts = TelegramAlerts()
    
    if not alerts.enabled:
        print("\n📝 Aby skonfigurować Telegram:")
        print("1. Otwórz Telegram i znajdź @BotFather")
        print("2. Wyślij /newbot")
        print("3. Skopiuj TOKEN")
        print("4. Znajdź @userinfobot aby poznać CHAT_ID")
        print("5. Wklej dane do telegram_alerts.py lub ustaw env vars:")
        print("   set TELEGRAM_BOT_TOKEN=twoj_token")
        print("   set TELEGRAM_CHAT_ID=twoj_chat_id")
        return False
    
    # Test wysłania
    success = alerts.send_message("🤖 <b>Genius Bot</b> - Test połączenia OK!")
    
    if success:
        print("✅ Telegram działa poprawnie!")
        
        # Test alertu o starcie
        alerts.alert_bot_started({
            'mode': 'Test',
            'deposit': 50000,
            'position_size': 100,
            'leverage': 500,
            'min_confluence': 30
        })
        
    else:
        print("❌ Błąd wysyłania - sprawdź TOKEN i CHAT_ID")
        
    return success


def test_chart_report():
    """Testuje wysyłanie wykresu na Telegram"""
    print("📊 Test wysyłania wykresu na Telegram...")
    
    alerts = TelegramAlerts()
    
    if not alerts.enabled:
        print("❌ Telegram nie skonfigurowany")
        return False
    
    # Przykładowe dane
    demo_trades = [
        {'id': 'T0001', 'direction': 'LONG', 'pnl': 275.0, 'entry_price': 103500, 'status': 'closed'},
        {'id': 'T0002', 'direction': 'SHORT', 'pnl': -50.0, 'entry_price': 104200, 'status': 'closed'},
        {'id': 'T0003', 'direction': 'LONG', 'pnl': 775.0, 'entry_price': 103800, 'status': 'closed'},
        {'id': 'T0004', 'direction': 'LONG', 'pnl': 150.0, 'entry_price': 104000, 'status': 'closed'},
        {'id': 'T0005', 'direction': 'SHORT', 'pnl': -25.0, 'entry_price': 104500, 'status': 'closed'},
    ]
    
    demo_balance = [
        {'time': 'Start', 'balance': 50000, 'tradeResult': None},
        {'time': '10:00', 'balance': 50275, 'tradeResult': 'profit'},
        {'time': '11:30', 'balance': 50225, 'tradeResult': 'loss'},
        {'time': '14:00', 'balance': 51000, 'tradeResult': 'profit'},
        {'time': '16:00', 'balance': 51150, 'tradeResult': 'profit'},
        {'time': '18:00', 'balance': 51125, 'tradeResult': 'loss'},
    ]
    
    success = alerts.send_performance_report(demo_trades, demo_balance, 50000)
    
    if success:
        print("✅ Wykres wysłany na Telegram!")
    else:
        print("❌ Błąd wysyłania wykresu")
    
    return success


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "chart":
        test_chart_report()
    else:
        test_telegram()
        print("\n💡 Aby wysłać testowy wykres: python telegram_alerts.py chart")
