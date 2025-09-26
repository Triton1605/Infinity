"""
Command handlers for terminal interface.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

from src.data_management.data_manager import DataManager
from src.terminal.terminal_display import TerminalDisplay
from utils.filepath_manager import filepath_manager


class TerminalCommands:
    """Handles all terminal commands."""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.display = TerminalDisplay()
    
    def add_asset(self, args: str):
        """Add a new asset."""
        if not args:
            print("\nUsage: add <SYMBOL> <TYPE>")
            print("Example: add AAPL equities")
            print("\nAsset types: equities, crypto, commodities, futures, bonds")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Both symbol and asset type are required.")
            print("Usage: add <SYMBOL> <TYPE>")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        
        valid_types = ['equities', 'crypto', 'commodities', 'futures', 'bonds']
        if asset_type not in valid_types:
            print(f"\nError: Invalid asset type '{asset_type}'")
            print(f"Valid types: {', '.join(valid_types)}")
            return
        
        # Check if already exists
        if self.data_manager.asset_exists(symbol, asset_type):
            response = input(f"\nAsset {symbol} already exists. Update it? (y/n): ").lower()
            if response == 'y':
                self.update_asset(f"{symbol} {asset_type}")
            return
        
        print(f"\nDownloading data for {symbol}...")
        try:
            success = self.data_manager.add_asset_to_tracking(symbol, asset_type)
            if success:
                print(f"✓ Successfully added {symbol} to {asset_type}")
            else:
                print(f"✗ Failed to add {symbol}")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    def update_asset(self, args: str):
        """Update an existing asset."""
        if not args:
            print("\nUsage: update <SYMBOL> <TYPE>")
            print("Example: update AAPL equities")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Both symbol and asset type are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        
        print(f"\nUpdating {symbol}...")
        try:
            success = self.data_manager.update_asset_data(symbol, asset_type)
            if success:
                print(f"✓ Successfully updated {symbol}")
            else:
                print(f"✗ Failed to update {symbol}")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    def update_all_assets(self, args: str):
        """Update all tracked assets."""
        tracked_assets = self.data_manager.get_tracked_assets()
        total_assets = sum(len(assets) for assets in tracked_assets.values())
        
        if total_assets == 0:
            print("\nNo assets to update.")
            return
        
        response = input(f"\nUpdate all {total_assets} assets? This may take a while. (y/n): ").lower()
        if response != 'y':
            print("Update cancelled.")
            return
        
        print(f"\nUpdating {total_assets} assets...\n")
        
        success_count = 0
        failed_count = 0
        
        for asset_type, assets in tracked_assets.items():
            for symbol in assets.keys():
                print(f"Updating {symbol} ({asset_type})...", end=" ")
                try:
                    if self.data_manager.update_asset_data(symbol, asset_type):
                        print("✓")
                        success_count += 1
                    else:
                        print("✗")
                        failed_count += 1
                except Exception as e:
                    print(f"✗ Error: {str(e)}")
                    failed_count += 1
        
        print(f"\n{'='*50}")
        print(f"Update complete: {success_count} successful, {failed_count} failed")
        print(f"{'='*50}")
    
    def remove_asset(self, args: str):
        """Remove an asset from tracking."""
        if not args:
            print("\nUsage: remove <SYMBOL> <TYPE>")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Both symbol and asset type are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        
        response = input(f"\nRemove {symbol} from tracking? This will delete all data. (y/n): ").lower()
        if response != 'y':
            print("Removal cancelled.")
            return
        
        try:
            success = self.data_manager.remove_asset_from_tracking(symbol, asset_type)
            if success:
                print(f"✓ Successfully removed {symbol}")
            else:
                print(f"✗ Failed to remove {symbol}")
        except Exception as e:
            print(f"✗ Error: {str(e)}")
    
    def list_assets(self, args: str):
        """List all tracked assets."""
        filter_type = args.strip().lower() if args else None
        
        tracked_assets = self.data_manager.get_tracked_assets()
        
        if filter_type and filter_type not in tracked_assets:
            print(f"\nInvalid asset type: {filter_type}")
            print(f"Valid types: {', '.join(tracked_assets.keys())}")
            return
        
        self.display.show_assets_list(tracked_assets, filter_type)
    
    def view_asset(self, args: str):
        """View detailed information about an asset."""
        if not args:
            print("\nUsage: view <SYMBOL> <TYPE>")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Both symbol and asset type are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        
        asset_data = self.data_manager.load_asset_data(symbol, asset_type)
        if not asset_data:
            print(f"\nAsset {symbol} not found.")
            return
        
        self.display.show_asset_details(asset_data)
    
    def search_assets(self, args: str):
        """Search for assets by symbol or name."""
        if not args:
            print("\nUsage: search <QUERY>")
            return
        
        query = args.strip().lower()
        tracked_assets = self.data_manager.get_tracked_assets()
        
        results = []
        for asset_type, assets in tracked_assets.items():
            for symbol, data in assets.items():
                if (query in symbol.lower() or 
                    query in data.get('company_name', '').lower()):
                    results.append({
                        'symbol': symbol,
                        'type': asset_type,
                        'name': data.get('company_name', 'Unknown'),
                        'price': data.get('latest_price', 0)
                    })
        
        if results:
            self.display.show_search_results(results)
        else:
            print(f"\nNo assets found matching '{args}'")
    
    def analyze_asset(self, args: str):
        """Analyze asset price movements and statistics."""
        if not args:
            print("\nUsage: analyze <SYMBOL> <TYPE> [TIMEFRAME]")
            print("Example: analyze AAPL equities 1y")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Symbol and asset type are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        timeframe = parts[2] if len(parts) > 2 else '1y'
        
        asset_data = self.data_manager.load_asset_data(symbol, asset_type)
        if not asset_data:
            print(f"\nAsset {symbol} not found.")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(asset_data['historical_data'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Apply timeframe filter
        df = self._apply_timeframe(df, timeframe)
        
        if df.empty:
            print(f"\nNo data available for timeframe {timeframe}")
            return
        
        self.display.show_asset_analysis(symbol, df, timeframe)
    
    def compare_assets(self, args: str):
        """Compare multiple assets."""
        if not args:
            print("\nUsage: compare <SYMBOL1:TYPE1> <SYMBOL2:TYPE2> [SYMBOL3:TYPE3] ...")
            print("Example: compare AAPL:equities TSLA:equities")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: At least two assets are required for comparison.")
            return
        
        assets_data = []
        for part in parts:
            if ':' not in part:
                print(f"\nError: Invalid format for '{part}'. Use SYMBOL:TYPE")
                return
            
            symbol, asset_type = part.split(':', 1)
            symbol = symbol.upper()
            asset_type = asset_type.lower()
            
            asset_data = self.data_manager.load_asset_data(symbol, asset_type)
            if not asset_data:
                print(f"\nAsset {symbol} not found.")
                return
            
            df = pd.DataFrame(asset_data['historical_data'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            assets_data.append({
                'symbol': symbol,
                'type': asset_type,
                'data': df
            })
        
        self.display.show_asset_comparison(assets_data)
    
    def manage_events(self, args: str):
        """Manage events for an asset."""
        if not args:
            print("\nUsage: events <SYMBOL> <TYPE> [add|list|delete]")
            print("Example: events AAPL equities list")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Symbol and asset type are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        action = parts[2].lower() if len(parts) > 2 else 'list'
        
        events_file = self._get_events_file_path(symbol, asset_type)
        
        if action == 'list':
            self._list_events(events_file, symbol)
        elif action == 'add':
            self._add_event(events_file, symbol)
        elif action == 'delete':
            self._delete_event(events_file, symbol)
        else:
            print(f"\nInvalid action: {action}")
            print("Valid actions: add, list, delete")
    
    def find_patterns(self, args: str):
        """Find similar patterns in historical data."""
        if not args:
            print("\nUsage: patterns <SYMBOL> <TYPE> <EVENT_DATE> [PRECISION]")
            print("Example: patterns AAPL equities 2024-01-15 0.80")
            return
        
        parts = args.split()
        if len(parts) < 3:
            print("\nError: Symbol, type, and event date are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        event_date = parts[2]
        precision = float(parts[3]) if len(parts) > 3 else 0.80
        
        asset_data = self.data_manager.load_asset_data(symbol, asset_type)
        if not asset_data:
            print(f"\nAsset {symbol} not found.")
            return
        
        df = pd.DataFrame(asset_data['historical_data'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        print(f"\nSearching for patterns similar to {event_date} with {precision:.0%} precision...")
        
        similar_patterns = self._find_similar_patterns(df, event_date, precision)
        
        if similar_patterns:
            self.display.show_pattern_results(similar_patterns, event_date, precision)
        else:
            print(f"No patterns found with {precision:.0%}+ similarity")
    
    def analyze_sentiment(self, args: str):
        """Analyze price-based sentiment."""
        if not args:
            print("\nUsage: sentiment <SYMBOL> <TYPE> <PRICE> [TOLERANCE%]")
            print("Example: sentiment AAPL equities 150.00 5")
            return
        
        parts = args.split()
        if len(parts) < 3:
            print("\nError: Symbol, type, and price are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        target_price = float(parts[2])
        tolerance = float(parts[3]) if len(parts) > 3 else 5.0
        
        asset_data = self.data_manager.load_asset_data(symbol, asset_type)
        if not asset_data:
            print(f"\nAsset {symbol} not found.")
            return
        
        df = pd.DataFrame(asset_data['historical_data'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        sentiment_data = self._analyze_price_sentiment(df, target_price, tolerance)
        
        if sentiment_data['occurrences'] > 0:
            self.display.show_sentiment_analysis(symbol, target_price, tolerance, sentiment_data)
        else:
            print(f"\nNo occurrences found at ${target_price:.2f} ±{tolerance}%")
    
    def export_data(self, args: str):
        """Export asset data to CSV."""
        if not args:
            print("\nUsage: export <SYMBOL> <TYPE> [FILENAME]")
            print("Example: export AAPL equities AAPL_data.csv")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Symbol and type are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        filename = parts[2] if len(parts) > 2 else f"{symbol}_{asset_type}_export.csv"
        
        asset_data = self.data_manager.load_asset_data(symbol, asset_type)
        if not asset_data:
            print(f"\nAsset {symbol} not found.")
            return
        
        try:
            df = pd.DataFrame(asset_data['historical_data'])
            df.to_csv(filename, index=False)
            print(f"\n✓ Data exported to {filename}")
        except Exception as e:
            print(f"\n✗ Export failed: {str(e)}")
    
    def generate_report(self, args: str):
        """Generate a text report for an asset."""
        if not args:
            print("\nUsage: report <SYMBOL> <TYPE> [FILENAME]")
            return
        
        parts = args.split()
        if len(parts) < 2:
            print("\nError: Symbol and type are required.")
            return
        
        symbol = parts[0].upper()
        asset_type = parts[1].lower()
        filename = parts[2] if len(parts) > 2 else f"{symbol}_{asset_type}_report.txt"
        
        asset_data = self.data_manager.load_asset_data(symbol, asset_type)
        if not asset_data:
            print(f"\nAsset {symbol} not found.")
            return
        
        try:
            report = self._generate_text_report(symbol, asset_data)
            with open(filename, 'w') as f:
                f.write(report)
            print(f"\n✓ Report saved to {filename}")
        except Exception as e:
            print(f"\n✗ Report generation failed: {str(e)}")
    
    # Helper methods
    def _apply_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Apply timeframe filter to dataframe."""
        end_date = df.index.max()
        
        if timeframe == '1d':
            start_date = end_date - pd.Timedelta(days=1)
        elif timeframe == '1w':
            start_date = end_date - pd.Timedelta(weeks=1)
        elif timeframe == '1m':
            start_date = end_date - pd.Timedelta(days=30)
        elif timeframe == '3m':
            start_date = end_date - pd.Timedelta(days=90)
        elif timeframe == '6m':
            start_date = end_date - pd.Timedelta(days=180)
        elif timeframe == '1y':
            start_date = end_date - pd.Timedelta(days=365)
        elif timeframe == '5y':
            start_date = end_date - pd.Timedelta(days=1825)
        else:
            return df
        
        return df[df.index >= start_date]
    
    def _get_events_file_path(self, symbol: str, asset_type: str) -> str:
        """Get events file path for an asset."""
        asset_dir = filepath_manager.get_asset_dir(asset_type)
        return os.path.join(asset_dir, f"{symbol}_events.json")
    
    def _list_events(self, events_file: str, symbol: str):
        """List events for an asset."""
        if not os.path.exists(events_file):
            print(f"\nNo events found for {symbol}")
            return
        
        with open(events_file, 'r') as f:
            events = json.load(f)
        
        if not events:
            print(f"\nNo events found for {symbol}")
            return
        
        print(f"\nEvents for {symbol}:")
        print("="*60)
        for i, event in enumerate(events, 1):
            if event['type'] == 'single':
                print(f"{i}. {event['date']} - {event['label']}")
            else:
                print(f"{i}. {event['start_date']} to {event['end_date']} - {event['label']}")
        print("="*60)
    
    def _add_event(self, events_file: str, symbol: str):
        """Add an event for an asset."""
        event_type = input("\nEvent type (single/range): ").lower()
        
        if event_type == 'single':
            date = input("Enter date (YYYY-MM-DD): ")
            label = input("Enter event description: ")
            
            event = {
                'type': 'single',
                'date': date,
                'label': label,
                'created': datetime.now().isoformat()
            }
        elif event_type == 'range':
            start_date = input("Enter start date (YYYY-MM-DD): ")
            end_date = input("Enter end date (YYYY-MM-DD): ")
            label = input("Enter event description: ")
            
            event = {
                'type': 'range',
                'start_date': start_date,
                'end_date': end_date,
                'label': label,
                'created': datetime.now().isoformat()
            }
        else:
            print("Invalid event type")
            return
        
        # Load existing events or create new list
        events = []
        if os.path.exists(events_file):
            with open(events_file, 'r') as f:
                events = json.load(f)
        
        events.append(event)
        
        os.makedirs(os.path.dirname(events_file), exist_ok=True)
        with open(events_file, 'w') as f:
            json.dump(events, f, indent=2)
        
        print(f"✓ Event added successfully")
    
    def _delete_event(self, events_file: str, symbol: str):
        """Delete an event."""
        if not os.path.exists(events_file):
            print(f"\nNo events found for {symbol}")
            return
        
        with open(events_file, 'r') as f:
            events = json.load(f)
        
        if not events:
            print(f"\nNo events found for {symbol}")
            return
        
        self._list_events(events_file, symbol)
        
        try:
            index = int(input("\nEnter event number to delete: ")) - 1
            if 0 <= index < len(events):
                deleted = events.pop(index)
                with open(events_file, 'w') as f:
                    json.dump(events, f, indent=2)
                print(f"✓ Deleted event: {deleted['label']}")
            else:
                print("Invalid event number")
        except ValueError:
            print("Invalid input")
    
    def _find_similar_patterns(self, df: pd.DataFrame, event_date: str, precision: float) -> List[Dict]:
        """Find similar price patterns."""
        try:
            event_date = pd.to_datetime(event_date)
        except:
            print("Invalid date format")
            return []
        
        # Get pattern window around event
        pattern_start = event_date - pd.Timedelta(days=10)
        pattern_end = event_date + pd.Timedelta(days=10)
        
        pattern_data = df[(df.index >= pattern_start) & (df.index <= pattern_end)]
        if pattern_data.empty:
            return []
        
        pattern_prices = pattern_data['close'].values
        pattern_normalized = (pattern_prices - pattern_prices.min()) / (pattern_prices.max() - pattern_prices.min())
        
        similar_patterns = []
        search_window_size = len(pattern_normalized)
        
        for i in range(0, len(df) - search_window_size + 1, 5):
            window_data = df.iloc[i:i+search_window_size]
            window_prices = window_data['close'].values
            
            if len(window_prices) < search_window_size:
                continue
            
            # Skip original event
            if abs((window_data.index[0] - pattern_start).days) < 30:
                continue
            
            if window_prices.max() == window_prices.min():
                continue
            
            window_normalized = (window_prices - window_prices.min()) / (window_prices.max() - window_prices.min())
            
            correlation = np.corrcoef(pattern_normalized, window_normalized)[0, 1]
            
            if not np.isnan(correlation) and correlation >= precision:
                similar_patterns.append({
                    'start_date': window_data.index[0],
                    'end_date': window_data.index[-1],
                    'similarity': correlation,
                    'price_change': ((window_prices[-1] - window_prices[0]) / window_prices[0]) * 100
                })
        
        similar_patterns.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_patterns[:20]  # Return top 20
    
    def _analyze_price_sentiment(self, df: pd.DataFrame, target_price: float, tolerance: float) -> Dict:
        """Analyze sentiment at similar price levels."""
        tolerance_decimal = tolerance / 100
        price_range_min = target_price * (1 - tolerance_decimal)
        price_range_max = target_price * (1 + tolerance_decimal)
        
        similar_price_data = df[
            (df['close'] >= price_range_min) & 
            (df['close'] <= price_range_max)
        ]
        
        reactions = []
        for idx, (date, row) in enumerate(similar_price_data.iterrows()):
            future_dates = df[df.index > date].head(5)
            if not future_dates.empty:
                start_price = row['close']
                end_price = future_dates['close'].iloc[-1]
                reaction_pct = ((end_price - start_price) / start_price) * 100
                reactions.append({
                    'date': date,
                    'reaction_pct': reaction_pct,
                    'direction': 'Positive' if reaction_pct > 1 else 'Negative' if reaction_pct < -1 else 'Neutral'
                })
        
        if not reactions:
            return {'occurrences': 0}
        
        positive = [r for r in reactions if r['direction'] == 'Positive']
        negative = [r for r in reactions if r['direction'] == 'Negative']
        neutral = [r for r in reactions if r['direction'] == 'Neutral']
        
        return {
            'occurrences': len(reactions),
            'positive': len(positive),
            'negative': len(negative),
            'neutral': len(neutral),
            'avg_reaction': np.mean([r['reaction_pct'] for r in reactions]),
            'reactions': reactions[:10]  # Top 10
        }
    
    def _generate_text_report(self, symbol: str, asset_data: Dict) -> str:
        """Generate a text report."""
        df = pd.DataFrame(asset_data['historical_data'])
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calculate statistics
        current_price = df['close'].iloc[-1]
        price_change_1d = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100) if len(df) > 1 else 0
        
        df_1m = self._apply_timeframe(df, '1m')
        price_change_1m = ((df_1m['close'].iloc[-1] - df_1m['close'].iloc[0]) / df_1m['close'].iloc[0] * 100) if not df_1m.empty else 0
        
        df_1y = self._apply_timeframe(df, '1y')
        price_change_1y = ((df_1y['close'].iloc[-1] - df_1y['close'].iloc[0]) / df_1y['close'].iloc[0] * 100) if not df_1y.empty else 0
        
        all_time_high = df['high'].max()
        all_time_low = df['low'].min()
        
        volatility_1m = df_1m['close'].pct_change().std() * 100 if not df_1m.empty else 0
        
        report = f"""
{'='*70}
ASSET ANALYSIS REPORT: {symbol}
{'='*70}

ASSET INFORMATION
-----------------
Symbol: {symbol}
Company Name: {asset_data.get('company_name', 'Unknown')}
Asset Type: {asset_data.get('asset_type', 'Unknown').title()}
Exchange: {asset_data.get('exchange', 'Unknown')}
Sector: {asset_data.get('sector', 'Unknown')}
Industry: {asset_data.get('industry', 'Unknown')}
IPO Date: {asset_data.get('ipo_date', 'Unknown')}

CURRENT STATISTICS
------------------
Current Price: ${current_price:.2f}
24h Change: {price_change_1d:+.2f}%
1 Month Change: {price_change_1m:+.2f}%
1 Year Change: {price_change_1y:+.2f}%

All-Time High: ${all_time_high:.2f}
All-Time Low: ${all_time_low:.2f}
30-Day Volatility: {volatility_1m:.2f}%

DATA INFORMATION
----------------
Total Records: {len(df)}
Date Range: {df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}
Last Update: {asset_data.get('last_data_pull', 'Unknown')}

{'='*70}
Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}
"""
        return report
