#!/usr/bin/env python3
"""
Infinity Stock Analysis Software - Terminal Version
Command-line entry point for the application.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.terminal.terminal_app import TerminalApplication
    from utils.filepath_manager import filepath_manager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the Infinity directory and have installed all requirements.")
    sys.exit(1)


def check_requirements():
    """Check if all required packages are installed."""
    required_packages = [
        'pandas', 'numpy', 'yfinance', 'requests'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        error_msg = f"""
Missing required packages: {', '.join(missing_packages)}

Please install them using:
pip install {' '.join(missing_packages)}

Or install all requirements:
pip install -r requirements.txt
"""
        print(error_msg)
        return False
    
    return True


def initialize_directories():
    """Initialize required directories and configuration files."""
    try:
        filepath_manager.reload_paths()
        print("Initialized directory structure successfully.")
        return True
    except Exception as e:
        print(f"Error initializing directories: {e}")
        return False


def main():
    """Main application entry point."""
    print("=" * 60)
    print("Infinity Stock Analysis Software - Terminal Mode")
    print("=" * 60)
    print()
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Initialize directories
    if not initialize_directories():
        print("Failed to initialize directory structure.")
        return 1
    
    try:
        # Create and run the terminal application
        app = TerminalApplication()
        print("Application initialized successfully.")
        print()
        
        # Handle Ctrl+C gracefully
        import signal
        def signal_handler(sig, frame):
            print("\n\nReceived interrupt signal. Exiting...")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        app.run()
        
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        return 0
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        print(error_msg)
        return 1
    
    print("\nApplication closed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
