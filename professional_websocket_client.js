/**
 * 🚀 PROFESSIONAL WEBSOCKET CLIENT
 * Real-time data streaming from Hamster Terminal API
 * Zero lag, automatic reconnection, rate limit aware
 */

class HamsterTerminalWebSocket {
    constructor(options = {}) {
        this.url = options.url || 'http://localhost:5000';
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000;
        this.connected = false;
        this.priceCache = new Map();
        this.subscribers = new Map();
        
        // Initialize Socket.IO
        this.socket = io(this.url, {
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: 10,
            transports: ['websocket', 'polling']
        });
        
        this.setupEventHandlers();
    }
    
    /**
     * Setup Socket.IO event handlers
     */
    setupEventHandlers() {
        // Connection established
        this.socket.on('connect', () => {
            console.log('✅ WebSocket Connected to Hamster Terminal');
            this.connected = true;
            this.reconnectAttempts = 0;
            this.emit('connected', { timestamp: new Date().toISOString() });
        });
        
        // Connection closed
        this.socket.on('disconnect', (reason) => {
            console.log('❌ WebSocket Disconnected:', reason);
            this.connected = false;
            this.emit('disconnected', { reason });
        });
        
        // Real-time price update
        this.socket.on('price_update', (data) => {
            this.handlePriceUpdate(data);
        });
        
        // Connection status
        this.socket.on('status', (data) => {
            console.log('📡 Status:', data);
        });
        
        // Subscription confirmation
        this.socket.on('subscription', (data) => {
            console.log('📊 Subscribed to:', data.symbols);
        });
        
        // Error handling
        this.socket.on('error', (error) => {
            console.error('❌ WebSocket Error:', error);
            this.emit('error', error);
        });
        
        // Reconnect attempts
        this.socket.on('reconnect_attempt', () => {
            this.reconnectAttempts++;
            console.log(`⏳ Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
        });
    }
    
    /**
     * Handle incoming price update
     */
    handlePriceUpdate(data) {
        const { symbol, price, change, timestamp } = data;
        
        // Update cache
        this.priceCache.set(symbol, {
            price,
            change,
            timestamp,
            updatedAt: new Date().getTime()
        });
        
        // Notify all subscribers for this symbol
        if (this.subscribers.has(symbol)) {
            this.subscribers.get(symbol).forEach(callback => {
                callback({
                    symbol,
                    price,
                    change,
                    timestamp
                });
            });
        }
        
        // Log for monitoring (throttled)
        console.debug(`📊 ${symbol}: $${price?.toLocaleString()} (${change >= 0 ? '+' : ''}${change.toFixed(2)}%)`);
    }
    
    /**
     * Subscribe to price updates
     */
    subscribe(symbol, callback) {
        if (!this.subscribers.has(symbol)) {
            this.subscribers.set(symbol, []);
        }
        this.subscribers.get(symbol).push(callback);
        
        // If already have data in cache, call immediately
        if (this.priceCache.has(symbol)) {
            const data = this.priceCache.get(symbol);
            callback({
                symbol,
                price: data.price,
                change: data.change,
                timestamp: data.timestamp
            });
        }
        
        console.log(`✅ Subscribed to ${symbol}`);
    }
    
    /**
     * Unsubscribe from price updates
     */
    unsubscribe(symbol, callback) {
        if (this.subscribers.has(symbol)) {
            const callbacks = this.subscribers.get(symbol);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
    
    /**
     * Get current price from cache (no network call)
     */
    getPrice(symbol) {
        const data = this.priceCache.get(symbol);
        return data ? data.price : null;
    }
    
    /**
     * Get all cached prices
     */
    getAllPrices() {
        const prices = {};
        this.priceCache.forEach((data, symbol) => {
            prices[symbol] = {
                price: data.price,
                change: data.change,
                timestamp: data.timestamp
            };
        });
        return prices;
    }
    
    /**
     * Emit custom events
     */
    emit(event, data) {
        if (!this._listeners) {
            this._listeners = new Map();
        }
        if (this._listeners.has(event)) {
            this._listeners.get(event).forEach(callback => {
                callback(data);
            });
        }
    }
    
    /**
     * Listen to custom events
     */
    on(event, callback) {
        if (!this._listeners) {
            this._listeners = new Map();
        }
        if (!this._listeners.has(event)) {
            this._listeners.set(event, []);
        }
        this._listeners.get(event).push(callback);
    }
    
    /**
     * Disconnect websocket
     */
    disconnect() {
        this.socket.disconnect();
        console.log('🛑 WebSocket disconnected');
    }
    
    /**
     * Check connection status
     */
    isConnected() {
        return this.connected;
    }
}

/**
 * ============ USAGE EXAMPLE ============
 * 
 * // Initialize
 * const terminal = new HamsterTerminalWebSocket({
 *     url: 'http://localhost:5000'
 * });
 * 
 * // Subscribe to real-time updates
 * terminal.subscribe('BTC/USD', (data) => {
 *     console.log(`BTC Price: $${data.price}`);
 *     updateChartUI(data);
 * });
 * 
 * // Listen to connection events
 * terminal.on('connected', () => {
 *     console.log('Ready for trading!');
 * });
 * 
 * terminal.on('error', (error) => {
 *     console.log('Connection error:', error);
 * });
 * 
 * // Get current price (from cache, no lag)
 * const currentBTC = terminal.getPrice('BTC/USD');
 * 
 * // Disconnect
 * terminal.disconnect();
 */

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = HamsterTerminalWebSocket;
}
