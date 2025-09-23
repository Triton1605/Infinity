#!/usr/bin/env python3
"""
Infinity Stock Analysis Software
Main entry point for the application.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.gui.main_gui import MainApplication
    from utils.filepath_manager import filepath_manager
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running from the Infinity directory and have installed all requirements.")
    sys.exit(1)


def check_requirements():
    """Check if all required packages are installed."""
    required_packages = [
        'pandas', 'numpy', 'yfinance', 'matplotlib', 'requests'
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
        
        # Show GUI error if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Missing Dependencies", error_msg)
            root.destroy()
        except:
            pass
        
        return False
    
    return True


def initialize_directories():
    """Initialize required directories and configuration files."""
    try:
        # This will create all necessary directories
        filepath_manager.reload_paths()
        print("Initialized directory structure successfully.")
        return True
    except Exception as e:
        print(f"Error initializing directories: {e}")
        return False


def main():
    """Main application entry point."""
    print("Starting Infinity Stock Analysis Software...")
    
    # Check requirements
    if not check_requirements():
        return 1
    
    # Initialize directories
    if not initialize_directories():
        print("Failed to initialize directory structure.")
        return 1
    
    try:
        # Create and run the main application
        app = MainApplication()
        print("Application initialized successfully.")
        print("GUI is now running...")
        print("Press Ctrl+C to exit or use the window's close button.")
        
        # Handle Ctrl+C gracefully
        import signal
        def signal_handler(sig, frame):
            print("\nReceived interrupt signal. Closing application...")
            try:
                app.root.quit()
                app.root.destroy()
            except:
                pass
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return 0
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        print(error_msg)
        
        # Show GUI error if possible
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Application Error", error_msg)
            root.destroy()
        except:
            pass
        
        return 1
    
    print("Application closed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
