# 🎨 HAMSTER TERMINAL - APP DESIGN SPECIFICATION

## Concept: Modern Financial App Interface

Design Philosophy: **Bloomberg Terminal + Modern Mobile App**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  🟧 ORANGE HEADER - Bloomberg Branding              │
├──┬──────────────────────────────────────────────────┤
│  │                                                   │
│ S│  MAIN DASHBOARD CONTENT                          │
│ I│  ┌────────────────────────────────┐             │
│ D│  │  Charts, Panels, Data          │             │
│ E│  │                                 │             │
│ B│  │  Dynamic Content Area          │             │
│ A│  │                                 │             │
│ R│  │  Slide-in panels overlay       │             │
│  │  └────────────────────────────────┘             │
│ 🐹│                                                  │
└──┴──────────────────────────────────────────────────┘
```

---

## 🎯 Components

### 1. APP SIDEBAR (Left)

**Collapsed State**: 70px wide
**Expanded State**: 260px wide

#### Visual Style:
- **Background**: Dark gradient `#0d0d0d → #050505`
- **Border**: `1px solid rgba(255, 140, 0, 0.3)` (Orange glow)
- **Position**: Fixed left, full height
- **Z-Index**: 9999 (above all)

#### Toggle Button:
```
┌──────────┐
│    ☰     │  ← 48x48px
│          │     Orange border
└──────────┘     Glassmorphism effect
```
- Animated hamburger → X transformation
- Hover: Scale 1.05, brighter glow

#### Menu Items (Icons + Labels):

**Core Navigation:**
```
🏠  Dashboard       ← Default active
📊  Markets         ← Real-time data
🔔  Smart Alerts    ← Badge: "3" (red)
💬  Genius Chat     ← AI Assistant
💼  Portfolio       ← Health check
📰  News Intel      ← Sentiment
```

**Advanced Tools:**
```
SECTION: TOOLS ──────
🎯  Strategy Builder
📈  Chart Patterns
⚙️  Settings
👤  Account
```

**Visual Specs per item:**
- Height: `48px`
- Padding: `14px 20px`
- Border-radius: `10px`
- Hover: `background: rgba(255, 140, 0, 0.1)`
- Active: Orange accent bar (left 3px)
- Icon size: `22px`
- Label: `13px`, letter-spacing `0.5px`

---

### 2. SLIDE-OUT PANELS (Right side overlay)

When menu item clicked → Panel slides from right

#### Panel Structure:
```
┌─────────────────────────────┐
│  ← Back    PANEL TITLE    ✕ │  ← Header (60px)
├─────────────────────────────┤
│                             │
│  Panel Content              │  ← Glassmorphism
│  - Cards                    │     background
│  - Forms                    │
│  - Data displays            │
│                             │
│  Scrollable area            │
│                             │
└─────────────────────────────┘
```

**Dimensions:**
- Width: `420px` (desktop), `100vw` (mobile)
- Animation: `cubic-bezier(0.4, 0, 0.2, 1)` 300ms
- Background: `rgba(13, 13, 13, 0.95)` + backdrop-blur
- Border-left: `1px solid rgba(255, 140, 0, 0.5)`

**Panel Types:**

#### A) Smart Alerts Panel
```
┌─────────────────────────────┐
│  🔔 SMART ALERTS            │
├─────────────────────────────┤
│  [+ Create Alert]           │
│                             │
│  ┌─────────────────────┐   │
│  │ BTC > $96,000       │   │
│  │ Active • 2h ago     │   │
│  │ [Edit] [Delete]     │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │ ETH < $2,800        │   │
│  │ Triggered! 🔴       │   │
│  │ Genius: "Watch..."  │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

#### B) Genius Chat Panel
```
┌─────────────────────────────┐
│  💬 GENIUS AI CHAT          │
│  [EN] [PL] [ES] [🔊Voice]  │
├─────────────────────────────┤
│  User:                      │
│  > What's BTC doing?        │
│                             │
│  🐹 Genius:                 │
│  BTC consolidating at       │
│  $95k. Watch $96k           │
│  resistance...              │
│  [🔊 Play voice]            │
│                             │
│  ┌─────────────────────┐   │
│  │ Type message...     │   │
│  │                [📤] │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

#### C) Portfolio Health Panel
```
┌─────────────────────────────┐
│  💼 PORTFOLIO HEALTH        │
├─────────────────────────────┤
│  Health Score: 76/100 ✅    │
│  [██████████░░░░░] 76%      │
│                             │
│  Risk Level: Moderate       │
│  Diversification: Good      │
│                             │
│  ┌─────────────────────┐   │
│  │ BTC  50% $47,500    │   │
│  │ ETH  30% $28,500    │   │
│  │ SOL  20% $19,000    │   │
│  └─────────────────────┘   │
│                             │
│  🤖 Genius Says:            │
│  "Reduce BTC position to    │
│   40% for better balance"   │
│                             │
│  [Analyze Now]              │
└─────────────────────────────┘
```

#### D) News Intelligence Panel
```
┌─────────────────────────────┐
│  📰 NEWS INTELLIGENCE       │
├─────────────────────────────┤
│  Market Sentiment: 🟢 62%   │
│  Bullish • 15 articles      │
│                             │
│  TOP STORIES:               │
│                             │
│  ┌─────────────────────┐   │
│  │ 🔥 Bitcoin Tests    │   │
│  │    $96k Resistance  │   │
│  │ Bullish • 2h ago    │   │
│  │ Genius: "Strong..." │   │
│  └─────────────────────┘   │
│                             │
│  ┌─────────────────────┐   │
│  │ 📊 ETH Staking ATH  │   │
│  │ Neutral • 4h ago    │   │
│  │ Genius: "Watch..."  │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
```

---

## 🎨 Visual Design System

### Colors:
```css
--orange: #ff8c00;        /* Primary brand */
--burgundy: #800020;      /* Secondary */
--black: #000000;         /* Background */
--panel: #0a0a0a;         /* Panels */
--border: #1a1a1a;        /* Borders */
--green: #00ff41;         /* Buy/Profit */
--red: #ff0033;           /* Sell/Loss */
--yellow: #ffff00;        /* Warning */
--cyan: #00d4ff;          /* Info */
--gray: #bdbdbd;          /* Text secondary */
```

### Typography:
```css
font-family: 'Roboto Mono', monospace;

/* Headings */
h1: 24px, 700, letter-spacing: 1.5px
h2: 18px, 700, letter-spacing: 1px
h3: 14px, 600, letter-spacing: 0.8px

/* Body */
body: 13px, 400, line-height: 1.5
small: 11px, 400
```

### Glassmorphism Effects:
```css
.glass-panel {
  background: rgba(10, 10, 10, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
}
```

### Animations:
```css
/* Slide in from right */
@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

/* Fade in */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Pulse (notifications) */
@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}
```

---

## 📱 Responsive Behavior

### Desktop (>1024px):
- Sidebar: Visible, collapsible
- Panels: 420px width, slide from right
- Main content: Adjusts margin when sidebar expands

### Tablet (768px - 1024px):
- Sidebar: Hidden by default, slides over content
- Panels: 380px width
- Touch gestures: Swipe from left (sidebar), swipe from right (close panel)

### Mobile (<768px):
- Sidebar: Full-width overlay when opened
- Panels: Full-screen
- Bottom nav: Quick actions (optional)

---

## 🚀 Implementation Priority

### Phase 1: Core Structure ✅
1. App sidebar HTML/CSS
2. Toggle functionality
3. Basic menu items

### Phase 2: Panels
1. Smart Alerts panel
2. Genius Chat panel
3. Portfolio Health panel
4. News Intelligence panel

### Phase 3: Integration
1. Connect to API endpoints
2. Real-time data updates
3. WebSocket for live chat

### Phase 4: Polish
1. Animations
2. Mobile responsive
3. Accessibility (ARIA labels)
4. Loading states

---

## 💡 User Flows

### Creating Smart Alert:
```
1. Click 🔔 in sidebar
2. Panel slides in
3. Click "+ Create Alert"
4. Form appears:
   - Symbol dropdown
   - Condition (above/below)
   - Value input
   - Type (price/volume/change)
5. Click "Create"
6. Success toast
7. Alert appears in list
```

### Chatting with Genius:
```
1. Click 💬 in sidebar
2. Chat panel slides in
3. Type message or click mic 🎤
4. Genius responds with:
   - Text analysis
   - Voice playback option
5. Context-aware (knows current BTC price)
6. Can ask follow-ups
```

### Checking Portfolio Health:
```
1. Click 💼 in sidebar
2. Portfolio panel slides in
3. Click "Analyze Now"
4. Shows:
   - Health score (0-100)
   - Risk level
   - Diversification
   - Recommendations
5. Genius commentary appears
6. Can adjust positions
```

---

## ✨ Special Effects

### Hover States:
- Scale: 1.02-1.05
- Glow: `box-shadow: 0 0 20px rgba(255, 140, 0, 0.4)`
- Transition: 200ms ease

### Active States:
- Orange accent border/glow
- Background: `rgba(255, 140, 0, 0.15)`

### Loading States:
- Skeleton screens for data loading
- Spinner with orange color
- Progress bars for long operations

### Notifications:
- Toast messages (top-right)
- Badge counters (red dot)
- Sound effects (optional)

---

## 🎯 Design Goals

✅ **Professional**: Bloomberg Terminal aesthetic
✅ **Modern**: App-like interactions
✅ **Fast**: <300ms all transitions
✅ **Intuitive**: Clear visual hierarchy
✅ **Responsive**: Works on all devices
✅ **Accessible**: WCAG AA compliance

---

**Next Step**: Implement Phase 1 (Core Structure) in docs/index.html
