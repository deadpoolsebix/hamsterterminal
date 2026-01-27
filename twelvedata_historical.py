"""
Twelve Data Historical Data Downloader
Downloads 6+ years of hourly data for LSTM training
Uses pagination to get all data with minimal API credits
"""

import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twelve Data API Key (ULTRA Plan)
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY', 'd54ad684cd8f40de895ec569d6128821')

class TwelveDataHistorical:
    """
    Downloads historical data from Twelve Data API
    Supports pagination for large datasets (6+ years)
    """
    
    BASE_URL = "https://api.twelvedata.com"
    MAX_OUTPUT_SIZE = 5000  # Max candles per request
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or TWELVE_DATA_API_KEY
        self.session = requests.Session()
        self.credits_used = 0
        
    def download_historical(
        self,
        symbol: str = "BTC/USD",
        interval: str = "1h",
        years: int = 6,
        save_path: str = None
    ) -> Optional[pd.DataFrame]:
        """
        Download historical data with pagination
        
        Args:
            symbol: Trading pair (e.g., "BTC/USD")
            interval: Candle interval ("1h", "4h", "1day")
            years: Number of years to download
            save_path: Path to save CSV (optional)
            
        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"📊 Downloading {years} years of {interval} data for {symbol}")
        logger.info(f"   API Key: {self.api_key[:8]}...{self.api_key[-4:]}")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        logger.info(f"   Period: {start_date.date()} to {end_date.date()}")
        
        all_data = []
        current_end = end_date
        request_count = 0
        
        while current_end > start_date:
            # Make API request
            params = {
                "symbol": symbol,
                "interval": interval,
                "outputsize": self.MAX_OUTPUT_SIZE,
                "end_date": current_end.strftime("%Y-%m-%d %H:%M:%S"),
                "apikey": self.api_key,
                "format": "JSON",
                "order": "desc"  # Newest first
            }
            
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/time_series",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                
                if "values" not in data:
                    if "message" in data:
                        logger.error(f"   API Error: {data['message']}")
                    break
                    
                values = data["values"]
                if not values:
                    break
                    
                request_count += 1
                self.credits_used += 1
                
                # Parse data
                for candle in values:
                    all_data.append({
                        "datetime": candle["datetime"],
                        "open": float(candle["open"]),
                        "high": float(candle["high"]),
                        "low": float(candle["low"]),
                        "close": float(candle["close"]),
                        "volume": float(candle.get("volume", 0))
                    })
                
                # Get oldest date from this batch
                oldest_date = datetime.strptime(values[-1]["datetime"], "%Y-%m-%d %H:%M:%S")
                
                logger.info(f"   Request {request_count}: Got {len(values)} candles, oldest: {oldest_date.date()}")
                
                # Move window back
                current_end = oldest_date - timedelta(hours=1)
                
                # Rate limiting (be nice to API)
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"   Request failed: {e}")
                break
            except Exception as e:
                logger.error(f"   Error: {e}")
                break
        
        if not all_data:
            logger.error("   No data downloaded!")
            return None
            
        # Create DataFrame
        df = pd.DataFrame(all_data)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)
        df = df.drop_duplicates(subset=["datetime"])
        
        logger.info(f"")
        logger.info(f"✅ Download complete!")
        logger.info(f"   Total candles: {len(df):,}")
        logger.info(f"   Date range: {df['datetime'].min().date()} to {df['datetime'].max().date()}")
        logger.info(f"   API credits used: {self.credits_used}")
        
        # Save to CSV
        if save_path:
            os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else ".", exist_ok=True)
            df.to_csv(save_path, index=False)
            logger.info(f"   Saved to: {save_path}")
        
        return df
    
    def download_btc_6years(self) -> pd.DataFrame:
        """Convenience method to download 6 years of BTC hourly data"""
        return self.download_historical(
            symbol="BTC/USD",
            interval="1h",
            years=6,
            save_path="data/btc_6years_hourly.csv"
        )


def download_and_train_lstm():
    """Download 6 years data and train LSTM"""
    print("="*70)
    print("SAMANTA LSTM TRAINING - 6 YEARS TWELVE DATA")
    print("="*70)
    print()
    
    # Check if data already exists
    data_path = "data/btc_6years_hourly.csv"
    
    if os.path.exists(data_path):
        print(f"[OK] Found cached data: {data_path}")
        df = pd.read_csv(data_path)
        df["datetime"] = pd.to_datetime(df["datetime"])
        print(f"     Candles: {len(df):,}")
        print(f"     Period: {df['datetime'].min().date()} to {df['datetime'].max().date()}")
    else:
        print("[...] Downloading 6 years of BTC hourly data from Twelve Data...")
        print()
        
        downloader = TwelveDataHistorical()
        df = downloader.download_btc_6years()
        
        if df is None:
            print("[X] Download failed!")
            return None
    
    print()
    print("="*70)
    print("TRAINING LSTM ON 6 YEARS DATA...")
    print("="*70)
    print()
    
    # Train LSTM
    from genius_lstm_predictor import GeniusLSTMPredictor
    
    lstm = GeniusLSTMPredictor(sequence_length=60)
    
    # Prepare data for training
    df_training = df.copy()
    df_training.columns = [c.lower() for c in df_training.columns]
    
    if 'datetime' in df_training.columns:
        df_training = df_training.set_index('datetime')
    
    # Train on the data
    result = lstm.train_on_dataframe(df_training, epochs=50, batch_size=64)
    
    if result and 'error' not in result:
        print()
        print("="*70)
        print("LSTM TRAINING COMPLETE!")
        print("="*70)
        print(f"  Training samples: {result.get('samples', 'N/A'):,}")
        print(f"  Epochs trained:   {result.get('epochs_trained', 'N/A')}")
        print(f"  Final accuracy:   {result.get('accuracy', 'N/A')}%")
        print(f"  Model saved:      models/genius_lstm.h5")
        print()
        print("  SAMANTA NOW USES 6 YEARS OF HISTORICAL DATA! 🚀")
        print("="*70)
    else:
        print(f"[X] Training failed: {result}")
    
    return df


if __name__ == "__main__":
    download_and_train_lstm()
