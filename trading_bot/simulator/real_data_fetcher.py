#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real-Time Data Fetcher
Pobieranie realnych danych z giełdy
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealDataFetcher:
    """
    Pobieranie realnych danych OHLCV
    """
    
    @staticmethod
    def fetch_btc_data(days: int = 7, interval: str = '1h') -> pd.DataFrame:
        """
        Pobierz realne dane BTC z ostatnich N dni
        
        Args:
            days: Liczba dni do pobrania
            interval: Interwał - '1m', '5m', '15m', '1h', '4h', '1d'
        
        Returns:
            DataFrame z OHLCV
        """
        print(f"\n[*] Pobieranie realnych danych BTC... ({days} dni, {interval})")
        
        try:
            # BTC-USD na Yahoo Finance
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            ticker = yf.Ticker("BTC-USD")
            data = ticker.history(start=start_date, end=end_date, interval=interval)
            
            # Rename columns do standardowego formatu
            if len(data.columns) >= 5:
                data = data[['Open', 'High', 'Low', 'Close', 'Volume']]
                data.columns = ['open', 'high', 'low', 'close', 'volume']
            else:
                # Fallback jeśli kolumny się różnią
                data.columns = ['open', 'high', 'low', 'close', 'volume']
            
            # Usuń wiersze bez volume
            data = data[data['volume'] > 0]
            
            print(f"[OK] Pobrano {len(data)} candles")
            print(f"   Zakres: {data.index[0]} do {data.index[-1]}")
            print(f"   Cena: ${data['close'].iloc[0]:,.0f} -> ${data['close'].iloc[-1]:,.0f}")
            
            return data
            
        except Exception as e:
            logger.error(f"Błąd przy pobieraniu danych: {e}")
            return None
    
    @staticmethod
    def fetch_multiple_symbols(symbols: list = None, days: int = 7, interval: str = '1h'):
        """
        Pobierz dane dla wielu symboli
        """
        if symbols is None:
            symbols = ['BTC-USD', 'ETH-USD']
        
        data_dict = {}
        
        for symbol in symbols:
            print(f"\n[*] Pobieranie {symbol}...")
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval=interval)
                
                data.columns = ['open', 'high', 'low', 'close', 'volume']
                data = data[data['volume'] > 0]
                
                data_dict[symbol] = data
                print(f"[OK] {symbol}: {len(data)} candles")
                
            except Exception as e:
                logger.error(f"Błąd dla {symbol}: {e}")
        
        return data_dict
    
    @staticmethod
    def save_data(df: pd.DataFrame, filename: str):
        """
        Zapisz dane do CSV
        """
        df.to_csv(filename)
        logger.info(f"Dane zapisane: {filename}")
    
    @staticmethod
    def load_data(filename: str) -> pd.DataFrame:
        """
        Wczytaj dane z CSV
        """
        df = pd.read_csv(filename, index_col=0, parse_dates=True)
        logger.info(f"Dane wczytane: {filename} ({len(df)} wierszy)")
        return df


if __name__ == "__main__":
    # Test - pobierz ostatnie 7 dni BTC
    fetcher = RealDataFetcher()
    
    data = fetcher.fetch_btc_data(days=7, interval='1h')
    
    if data is not None:
        print(f"\n📊 Statystyka danych:")
        print(f"   Open: ${data['open'].mean():.2f}")
        print(f"   Close: ${data['close'].mean():.2f}")
        print(f"   High: ${data['high'].max():.2f}")
        print(f"   Low: ${data['low'].min():.2f}")
        print(f"   Średni Volume: {data['volume'].mean():,.0f}")
