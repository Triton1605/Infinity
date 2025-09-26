"""
Display formatting for terminal interface.
"""

import pandas as pd
from typing import Dict, List
from datetime import datetime


class TerminalDisplay:
    """Handles all terminal display formatting."""
    
    def show_welcome(self):
        """Display welcome banner."""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          INFINITY STOCK ANALYSIS - TERMINAL MODE            ║
║                                                              ║
║              Professional Asset Analysis Tools               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    def show_help(self):
        """Display help information."""
        print("""
AVAILABLE COMMANDS:
==================

ASSET MANAGEMENT:
  add <SYMBOL> <TYPE>           Add a new asset to tracking
  update <SYMBOL> <TYPE>         Update asset data
  updateall                      Update all tracked assets
  remove <SYMBOL> <TYPE>         Remove asset from tracking
  list [TYPE]                    List all assets (optionally filter by type)
  view <SYMBOL> <TYPE>           View detailed asset information
  search <QUERY>                 Search for assets

ANALYSIS:
  analyze <SYMBOL> <TYPE> [TIME] Analyze asset price movements
  compare <SYM1:TYPE1> <SYM2:TYPE2> ... Compare multiple assets
  events <SYMBOL> <TYPE> [ACTION] Manage events (add/list/delete)
  patterns <SYMBOL> <TYPE> <DATE> [PREC] Find similar patterns
  sentiment <SYMBOL> <TYPE> <PRICE> [TOL%] Analyze price sentiment

DATA EXPORT:
  export <SYMBOL> <TYPE> [FILE]  Export asset data to CSV
  report <SYMBOL> <TYPE> [FILE]  Generate text report

GENERAL:
  help [COMMAND]                 Show this help or command-specific help
  clear                          Clear the screen
  exit, quit                     Exit the application

EXAMPLES:
  add AAPL equities
  analyze TSLA equities 1y
  compare AAPL:equities TSLA:equities
  patterns AAPL equities 2024-01-15 0.80
  sentiment AAPL equities 150.00 5

ASSET TYPES: equities, crypto, commodities, futures, bonds
TIMEFRAMES: 1d, 1w, 1m, 3m, 6m, 1y, 5y, all
""")
    
    def show_command_help(self, command: str):
        """Show help for a specific command."""
        help_text = {
            'add': """
ADD ASSET
Usage: add <SYMBOL> <TYPE>
Example: add AAPL equities

Downloads and adds a new asset to tracking. Asset types:
  - equities: Stocks (AAPL, TSLA, MSFT)
  - crypto: Cryptocurrencies (BTC-USD, ETH-USD)
  - commodities: Commodities (GC=F, CL=F)
  - futures: Futures contracts (ES=F, NQ=F)
  - bonds: Bonds (^TNX)
""",
            'analyze': """
ANALYZE ASSET
Usage: analyze <SYMBOL> <TYPE> [TIMEFRAME]
Example: analyze AAPL equities 1y

Shows price statistics, trends, and movements for the specified timeframe.
Timeframes: 1d, 1w, 1m, 3m, 6m, 1y, 5y, all
""",
            'patterns': """
FIND SIMILAR PATTERNS
Usage: patterns <SYMBOL> <TYPE> <EVENT_DATE> [PRECISION]
Example: patterns AAPL equities 2024-01-15 0.80

Finds historical price patterns similar to the pattern around the event date.
Precision: 0.0 to 1.0 (default 0.80 = 80% similarity)
""",
            'sentiment': """
PRICE SENTIMENT ANALYSIS
Usage: sentiment <SYMBOL> <TYPE> <PRICE> [TOLERANCE%]
Example: sentiment AAPL equities 150.00 5

Analyzes how the market typically reacts when the asset reaches similar price levels.
Tolerance: Percentage range around target price (default 5%)
"""
        }
        
        print(help_text.get(command, f"\nNo detailed help available for '{command}'"))
    
    def show_assets_list(self, tracked_assets: Dict, filter_type: str = None):
        """Display list of tracked assets."""
        print("\n" + "="*80)
        print("TRACKED ASSETS")
        print("="*80)
        
        total_count = 0
        
        for asset_type, assets in tracked_assets.items():
            if filter_type and asset_type != filter_type:
                continue
            
            if not assets:
                continue
            
            print(f"\n{asset_type.upper()}:")
            print("-" * 80)
            print(f"{'Symbol':<12} {'Company Name':<30} {'Price':<12} {'Last Update':<20}")
            print("-" * 80)
            
            for symbol, data in sorted(assets.items()):
                name = data.get('company_name', 'Unknown')[:28]
                price = f"${data.get('latest_price', 0):.2f}"
                last_update = data.get('last_data_pull', 'Unknown')[:19].replace('T', ' ')
                
                print(f"{symbol:<12} {name:<30} {price:<12} {last_update:<20}")
                total_count += 1
        
        print("\n" + "="*80)
        print(f"Total Assets: {total_count}")
        print("="*80)
    
    def show_asset_details(self, asset_data: Dict):
        """Display detailed asset information."""
        print("\n" + "="*70)
        print(f"ASSET DETAILS: {asset_data.get('symbol', 'Unknown')}")
        print("="*70)
        
        print(f"\nCOMPANY INFORMATION:")
        print(f"  Name: {asset_data.get('company_name', 'Unknown')}")
        print(f"  Symbol: {asset_data.get('symbol', 'Unknown')}")
        print(f"  Type: {asset_data.get('asset_type', 'Unknown').title()}")
        print(f"  Exchange: {asset_data.get('exchange', 'Unknown')}")
        print(f"  Currency: {asset_data.get('currency', 'Unknown')}")
        print(f"  Sector: {asset_data.get('sector', 'Unknown')}")
        print(f"  Industry: {asset_data.get('industry', 'Unknown')}")
        print(f"  IPO Date: {asset_data.get('ipo_date', 'Unknown')}")
        
        print(f"\nPRICE INFORMATION:")
        print(f"  Current Price: ${asset_data.get('latest_price', 0):.2f}")
        
        print(f"\nDATA INFORMATION:")
        print(f"  Total Records: {asset_data.get('total_records', 0):,}")
        print(f"  Date Range: {asset_data.get('date_range', {}).get('start', 'Unknown')} to {asset_data.get('date_range', {}).get('end', 'Unknown')}")
        print(f"  Last Updated: {asset_data.get('last_data_pull', 'Unknown')[:19].replace('T', ' ')}")
        print(f"  Data Period: {asset_data.get('data_period', 'Unknown')}")
        
        print("\n" + "="*70)
    
    def show_search_results(self, results: List[Dict]):
        """Display search results."""
        print("\n" + "="*70)
        print(f"SEARCH RESULTS ({len(results)} found)")
        print("="*70)
        print(f"\n{'Symbol':<12} {'Type':<15} {'Name':<30} {'Price':<12}")
        print("-" * 70)
        
        for result in results:
            print(f"{result['symbol']:<12} {result['type']:<15} {result['name'][:28]:<30} ${result['price']:.2f}")
        
        print("\n" + "="*70)
    
    def show_asset_analysis(self, symbol: str, df: pd.DataFrame, timeframe: str):
        """Display asset analysis."""
        # Calculate statistics
        current_price = df['close'].iloc[-1]
        start_price = df['close'].iloc[0]
        price_change = current_price - start_price
        price_change_pct = (price_change / start_price) * 100
        
        high = df['high'].max()
        low = df['low'].min()
        avg_volume = df['volume'].mean()
        
        # Volatility
        daily_returns = df['close'].pct_change().dropna()
        volatility = daily_returns.std() * 100
        
        # Trend (simple moving average crossover)
        if len(df) >= 20:
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
            trend = "Bullish" if current_price > sma_20 else "Bearish"
        else:
            trend = "Insufficient data"
        
        print("\n" + "="*70)
        print(f"ASSET ANALYSIS: {symbol} ({timeframe.upper()})")
        print("="*70)
        
        print(f"\nPRICE STATISTICS:")
        print(f"  Current Price: ${current_price:.2f}")
        print(f"  Period Change: ${price_change:+.2f} ({price_change_pct:+.2f}%)")
        print(f"  Period High: ${high:.2f}")
        print(f"  Period Low: ${low:.2f}")
        print(f"  Price Range: ${high - low:.2f}")
        
        print(f"\nVOLUME & VOLATILITY:")
        print(f"  Average Volume: {avg_volume:,.0f}")
        print(f"  Daily Volatility: {volatility:.2f}%")
        
        print(f"\nTREND ANALYSIS:")
        print(f"  Trend: {trend}")
        if len(df) >= 20:
            print(f"  20-Day SMA: ${sma_20:.2f}")
        
        print(f"\nDATA POINTS:")
        print(f"  Records: {len(df):,}")
        print(f"  Date Range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
        print("\n" + "="*70)
    
    def show_asset_comparison(self, assets_data: List[Dict]):
        """Display asset comparison."""
        print("\n" + "="*80)
        print("ASSET COMPARISON")
        print("="*80)
        
        # Find common date range
        start_date = max(data['data'].index.min() for data in assets_data)
        end_date = min(data['data'].index.max() for data in assets_data)
        
        print(f"\nComparison Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print()
        
        # Calculate performance for each asset
        print(f"{'Symbol':<12} {'Type':<12} {'Start $':<12} {'End $':<12} {'Change $':<12} {'Change %':<12}")
        print("-" * 80)
        
        for asset in assets_data:
            df = asset['data']
            df_filtered = df[(df.index >= start_date) & (df.index <= end_date)]
            
            if df_filtered.empty:
                continue
            
            start_price = df_filtered['close'].iloc[0]
            end_price = df_filtered['close'].iloc[-1]
            change = end_price - start_price
            change_pct = (change / start_price) * 100
            
            print(f"{asset['symbol']:<12} {asset['type']:<12} ${start_price:<11.2f} ${end_price:<11.2f} "
                  f"${change:+11.2f} {change_pct:+11.2f}%")
        
        print("\n" + "="*80)
    
    def show_pattern_results(self, patterns: List[Dict], event_date: str, precision: float):
        """Display pattern matching results."""
        print("\n" + "="*80)
        print(f"SIMILAR PATTERNS TO {event_date} (Precision: {precision:.0%})")
        print("="*80)
        
        if not patterns:
            print("\nNo similar patterns found.")
            return
        
        print(f"\nFound {len(patterns)} similar patterns:")
        print()
        print(f"{'Rank':<6} {'Similarity':<12} {'Start Date':<15} {'End Date':<15} {'Price Change':<15}")
        print("-" * 80)
        
        for i, pattern in enumerate(patterns, 1):
            similarity = f"{pattern['similarity']:.1%}"
            start = pattern['start_date'].strftime('%Y-%m-%d')
            end = pattern['end_date'].strftime('%Y-%m-%d')
            change = f"{pattern['price_change']:+.2f}%"
            
            print(f"{i:<6} {similarity:<12} {start:<15} {end:<15} {change:<15}")
        
        print("\n" + "="*80)
    
    def show_sentiment_analysis(self, symbol: str, target_price: float, tolerance: float, sentiment_data: Dict):
        """Display sentiment analysis results."""
        print("\n" + "="*70)
        print(f"PRICE SENTIMENT ANALYSIS: {symbol}")
        print("="*70)
        
        print(f"\nTarget Price: ${target_price:.2f} (±{tolerance}%)")
        print(f"Price Range: ${target_price * (1 - tolerance/100):.2f} - ${target_price * (1 + tolerance/100):.2f}")
        
        print(f"\nOCCURRENCES: {sentiment_data['occurrences']}")
        print(f"  Positive Reactions: {sentiment_data['positive']} ({sentiment_data['positive']/sentiment_data['occurrences']*100:.1f}%)")
        print(f"  Negative Reactions: {sentiment_data['negative']} ({sentiment_data['negative']/sentiment_data['occurrences']*100:.1f}%)")
        print(f"  Neutral Reactions: {sentiment_data['neutral']} ({sentiment_data['neutral']/sentiment_data['occurrences']*100:.1f}%)")
        
        print(f"\nAVERAGE REACTION: {sentiment_data['avg_reaction']:+.2f}%")
        
        if sentiment_data['positive'] > sentiment_data['negative'] * 1.5:
            sentiment = "BULLISH"
        elif sentiment_data['negative'] > sentiment_data['positive'] * 1.5:
            sentiment = "BEARISH"
        else:
            sentiment = "MIXED"
        
        print(f"\nMARKET SENTIMENT: {sentiment}")
        
        if sentiment_data.get('reactions'):
            print(f"\nRECENT OCCURRENCES:")
            print(f"{'Date':<15} {'Reaction':<12}")
            print("-" * 30)
            for reaction in sentiment_data['reactions'][:10]:
                date = reaction['date'].strftime('%Y-%m-%d')
                react = f"{reaction['reaction_pct']:+.2f}%"
                print(f"{date:<15} {react:<12}")
        
        print("\n" + "="*70)
