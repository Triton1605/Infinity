import json
import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from utils.filepath_manager import filepath_manager


class DataManager:
    """Handles all data operations for assets including downloading and storage."""
    
    def __init__(self):
        self.filepath_manager = filepath_manager
    
    def download_asset_data(self, symbol: str, asset_type: str, period: str = "max") -> Dict:
        """
        Download historical data for an asset using yfinance.
        
        Args:
            symbol: Asset symbol (e.g., 'AAPL', 'BTC-USD')
            asset_type: Type of asset ('equities', 'crypto', etc.)
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
        
        Returns:
            Dictionary containing asset metadata and historical data
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist_data = ticker.history(period=period)
            
            if hist_data.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Get basic info
            info = ticker.info
            
            # Prepare asset data structure
            asset_data = {
                "symbol": symbol,
                "asset_type": asset_type,
                "company_name": info.get("longName", "Unknown"),
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", "Unknown"),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "ipo_date": self._get_ipo_date(info),
                "last_data_pull": datetime.now().isoformat(),
                "latest_price": float(hist_data['Close'].iloc[-1]),
                "data_period": period,
                "total_records": len(hist_data),
                "date_range": {
                    "start": hist_data.index[0].isoformat(),
                    "end": hist_data.index[-1].isoformat()
                },
                "historical_data": self._convert_dataframe_to_dict(hist_data)
            }
            
            return asset_data
            
        except Exception as e:
            raise Exception(f"Error downloading data for {symbol}: {str(e)}")
    
    def _get_ipo_date(self, info: Dict) -> str:
        """Extract IPO date from ticker info, with fallback."""
        ipo_date = info.get("ipoDate")
        if ipo_date:
            return ipo_date
        
        # Fallback to first trade date if available
        first_trade = info.get("firstTradeDateEpochUtc")
        if first_trade:
            return datetime.fromtimestamp(first_trade).date().isoformat()
        
        return "Unknown"
    
    def _convert_dataframe_to_dict(self, df: pd.DataFrame) -> List[Dict]:
        """Convert pandas DataFrame to list of dictionaries."""
        data_list = []
        for date, row in df.iterrows():
            data_point = {
                "date": date.isoformat(),
                "open": float(row['Open']) if pd.notna(row['Open']) else None,
                "high": float(row['High']) if pd.notna(row['High']) else None,
                "low": float(row['Low']) if pd.notna(row['Low']) else None,
                "close": float(row['Close']) if pd.notna(row['Close']) else None,
                "volume": int(row['Volume']) if pd.notna(row['Volume']) else None
            }
            data_list.append(data_point)
        return data_list
    
    def save_asset_data(self, asset_data: Dict) -> bool:
        """
        Save asset data to JSON file.
        
        Args:
            asset_data: Asset data dictionary
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            symbol = asset_data["symbol"]
            asset_type = asset_data["asset_type"]
            
            file_path = self.filepath_manager.get_asset_file_path(asset_type, symbol)
            
            with open(file_path, 'w') as f:
                json.dump(asset_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving asset data: {str(e)}")
            return False
    
    def load_asset_data(self, symbol: str, asset_type: str) -> Optional[Dict]:
        """
        Load asset data from JSON file.
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            
        Returns:
            Asset data dictionary or None if not found
        """
        try:
            file_path = self.filepath_manager.get_asset_file_path(asset_type, symbol)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading asset data: {str(e)}")
            return None
    
    def get_tracked_assets(self) -> Dict:
        """Load tracked assets list."""
        try:
            tracked_file = self.filepath_manager.get_path("tracked_assets_file")
            
            if not os.path.exists(tracked_file):
                # Create empty tracked assets file
                empty_tracked = {
                    "equities": {},
                    "bonds": {},
                    "crypto": {},
                    "commodities": {},
                    "futures": {}
                }
                self.save_tracked_assets(empty_tracked)
                return empty_tracked
            
            with open(tracked_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading tracked assets: {str(e)}")
            return {}
    
    def save_tracked_assets(self, tracked_assets: Dict) -> bool:
        """Save tracked assets list."""
        try:
            tracked_file = self.filepath_manager.get_path("tracked_assets_file")
            
            with open(tracked_file, 'w') as f:
                json.dump(tracked_assets, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving tracked assets: {str(e)}")
            return False
    
    def add_asset_to_tracking(self, symbol: str, asset_type: str) -> bool:
        """
        Add an asset to the tracked assets list and download its data.
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Download asset data
            print(f"Downloading data for {symbol}...")
            asset_data = self.download_asset_data(symbol, asset_type)
            
            # Save individual asset file
            if not self.save_asset_data(asset_data):
                return False
            
            # Update tracked assets list
            tracked_assets = self.get_tracked_assets()
            
            if asset_type not in tracked_assets:
                tracked_assets[asset_type] = {}
            
            tracked_assets[asset_type][symbol] = {
                "ipo_date": asset_data["ipo_date"],
                "last_data_pull": asset_data["last_data_pull"],
                "latest_price": asset_data["latest_price"],
                "company_name": asset_data.get("company_name", "Unknown")
            }
            
            return self.save_tracked_assets(tracked_assets)
            
        except Exception as e:
            print(f"Error adding asset to tracking: {str(e)}")
            return False
    
    def update_asset_data(self, symbol: str, asset_type: str) -> bool:
        """Update existing asset data with latest information."""
        try:
            existing_data = self.load_asset_data(symbol, asset_type)
            if not existing_data:
                print(f"Asset {symbol} not found. Use add_asset_to_tracking instead.")
                return False
            
            # Download fresh data
            new_data = self.download_asset_data(symbol, asset_type)
            
            # Save updated data
            if not self.save_asset_data(new_data):
                return False
            
            # Update tracked assets metadata
            tracked_assets = self.get_tracked_assets()
            if asset_type in tracked_assets and symbol in tracked_assets[asset_type]:
                tracked_assets[asset_type][symbol].update({
                    "last_data_pull": new_data["last_data_pull"],
                    "latest_price": new_data["latest_price"]
                })
                return self.save_tracked_assets(tracked_assets)
            
            return True
            
        except Exception as e:
            print(f"Error updating asset data: {str(e)}")
            return False
    
    def asset_exists(self, symbol: str, asset_type: str) -> bool:
        """Check if an asset file exists."""
        file_path = self.filepath_manager.get_asset_file_path(asset_type, symbol)
        return os.path.exists(file_path)
    
    def remove_asset_from_tracking(self, symbol: str, asset_type: str) -> bool:
        """
        Remove an asset from tracking and delete its data file.
        
        Args:
            symbol: Asset symbol
            asset_type: Type of asset
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from tracked assets list
            tracked_assets = self.get_tracked_assets()
            
            if asset_type in tracked_assets and symbol in tracked_assets[asset_type]:
                del tracked_assets[asset_type][symbol]
                
                # Save updated tracked assets
                if not self.save_tracked_assets(tracked_assets):
                    return False
            
            # Delete the asset data file
            file_path = self.filepath_manager.get_asset_file_path(asset_type, symbol)
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"Deleted asset file: {file_path}")
            
            return True
            
        except Exception as e:
            print(f"Error removing asset from tracking: {str(e)}")
            return False
    
    def get_asset_list(self, asset_type: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Get list of all tracked assets.
        
        Args:
            asset_type: Optional filter by asset type
            
        Returns:
            List of tuples (symbol, asset_type)
        """
        tracked_assets = self.get_tracked_assets()
        asset_list = []
        
        for a_type, assets in tracked_assets.items():
            if asset_type is None or a_type == asset_type:
                for symbol in assets.keys():
                    asset_list.append((symbol, a_type))
        
        return sorted(asset_list)
