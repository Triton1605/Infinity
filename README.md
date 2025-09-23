# Infinity Stock Analysis Software

A comprehensive Python-based stock analysis application with GUI interface for simulating options trades and analyzing historical stock data.

## Features

- **Multi-Asset Support**: Track equities, cryptocurrencies, commodities, futures, and bonds
- **Interactive Graphing**: Create line charts, bar charts, and candlestick charts with customizable overlays
- **Flexible Time Ranges**: View data from 1 day to all-time, with custom date range support
- **Data Exclusions**: Remove outlier events and specific date ranges from analysis
- **Project Management**: Save and load graphing projects with all configurations
- **Modular Architecture**: Easy file path management and extensible design
- **Raspberry Pi Compatible**: Designed to run efficiently on Raspberry Pi

## Installation

### Prerequisites
- Python 3.7 or higher
- Internet connection for downloading stock data

### Setup

1. **Clone or download** the Infinity directory to your system

2. **Navigate to the directory**:
   ```bash
   cd Infinity
   ```

3. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

## Usage

### Getting Started

1. **Start the application** by running `python main.py`
2. **Add assets** using the "Add New Asset" button
   - Enter stock symbols like AAPL, TSLA, BTC-USD, etc.
   - Select the appropriate asset type
3. **Create a graphing project** to visualize your data
4. **Configure charts** with different types, time ranges, and exclusions
5. **Save projects** for future analysis

### Adding Assets

### Adding Assets

The software supports various asset types:
- **Equities**: AAPL, TSLA, MSFT, GOOGL
- **Cryptocurrency**: BTC-USD, ETH-USD, ADA-USD
- **Commodities**: GC=F (Gold), CL=F (Crude Oil), SI=F (Silver)
- **Futures**: ES=F (S&P 500), NQ=F (NASDAQ)
- **Bonds**: ^TNX (10-Year Treasury)

### Creating Charts

1. Select "New Graphing Project"
2. Search and add assets to your chart
3. Configure chart types:
   - Line charts for trend analysis
   - Bar charts for volume visualization
   - Candlestick charts for OHLC data
4. Set time ranges and resolution
5. Add date exclusions to remove outlier events
6. Save your project for future use

### Project Management

- **Save Projects**: Store chart configurations and asset selections
- **Open Projects**: Load previously saved analysis setups
- **Export Charts**: Save charts as PNG or PDF files

## Directory Structure

```
Infinity/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── src/                   # Source code
│   ├── gui/               # GUI components
│   ├── data_management/   # Data handling
│   ├── analysis/          # Analysis tools
│   └── projects/          # Project management
├── configs/               # Configuration files
│   ├── filepaths/         # File path settings
│   └── settings/          # Application settings
├── data/                  # Data storage
│   ├── assets/            # Asset data by type
│   │   ├── equities/
│   │   ├── crypto/
│   │   ├── commodities/
│   │   ├── futures/
│   │   └── bonds/
│   └── metadata/          # Asset metadata
├── saves/                 # Saved projects
├── utils/                 # Utility functions
├── tests/                 # Unit tests
└── docs/                  # Documentation
```

## Configuration

The application uses a modular filepath system. All file paths are configured in `configs/filepaths/paths.json`. To relocate directories, simply update this file instead of modifying code.

## Data Sources

- Historical stock data is downloaded from Yahoo Finance via the `yfinance` library
- Data includes Open, High, Low, Close, and Volume information
- Supports various time periods from 1 day to maximum available history

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you've activated the virtual environment and installed all requirements
2. **No Data Found**: Verify the asset symbol is correct (check Yahoo Finance for valid symbols)
3. **Chart Not Updating**: Ensure you have selected assets and clicked "Update Chart"
4. **Permission Errors**: Make sure you have write permissions in the Infinity directory

### Raspberry Pi Specific

- Ensure you have sufficient RAM for matplotlib operations
- Consider using lighter chart configurations for better performance
- Use SSD storage if possible for faster data access

## Development

### Adding New Features

The modular architecture makes it easy to extend functionality:

1. **New Asset Types**: Add directories in `data/assets/` and update filepath configuration
2. **New Chart Types**: Extend the charting functionality in `src/gui/graphing_window.py`
3. **New Analysis Tools**: Add modules in `src/analysis/`
4. **New Project Types**: Extend `src/projects/project_manager.py`

### Testing

Run tests using:
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is for educational and personal use. Please respect the terms of service of data providers.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify your asset symbols are valid
3. Ensure all dependencies are installed correctly
4. Check file permissions in the project directory

## Future Enhancements

- Options trading simulation
- Technical indicators (RSI, MACD, etc.)
- Portfolio optimization tools
- Real-time data feeds
- Advanced charting features
- Machine learning analysis tools
