#!/usr/bin/env python3
"""
Setup script to ensure all necessary files and directories are created.
Run this script after setting up the virtual environment and installing requirements.
"""

import os
import json
from pathlib import Path


def create_file_if_not_exists(filepath, content=""):
    """Create a file with given content if it doesn't exist."""
    if not os.path.exists(filepath):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Created: {filepath}")
    else:
        print(f"Exists: {filepath}")


def setup_project_structure():
    """Set up the complete project structure."""
    print("Setting up Infinity Stock Analysis Software...")
    
    # Create all necessary directories
    directories = [
        "src/gui",
        "src/data_management", 
        "src/analysis",
        "src/projects",
        "configs/filepaths",
        "configs/settings",
        "data/assets/equities",
        "data/assets/bonds",
        "data/assets/crypto", 
        "data/assets/commodities",
        "data/assets/futures",
        "data/metadata",
        "utils",
        "saves",
        "tests",
        "docs",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create __init__.py files
    init_files = [
        "src/__init__.py",
        "src/gui/__init__.py",
        "src/data_management/__init__.py",
        "src/analysis/__init__.py", 
        "src/projects/__init__.py",
        "utils/__init__.py"
    ]
    
    for init_file in init_files:
        create_file_if_not_exists(init_file, '"""Package initialization."""\n')
    
    # Create configuration files
    paths_config = {
        "data_dir": "data",
        "assets_dir": "data/assets",
        "equities_dir": "data/assets/equities",
        "bonds_dir": "data/assets/bonds",
        "crypto_dir": "data/assets/crypto",
        "commodities_dir": "data/assets/commodities",
        "futures_dir": "data/assets/futures",
        "metadata_dir": "data/metadata",
        "saves_dir": "saves",
        "configs_dir": "configs",
        "logs_dir": "logs",
        "tracked_assets_file": "data/metadata/tracked_assets.json",
        "filepath_registry": "data/metadata/filepath_registry.json"
    }
    
    create_file_if_not_exists(
        "configs/filepaths/paths.json",
        json.dumps(paths_config, indent=2)
    )
    
    app_config = {
        "app_name": "Infinity Stock Analysis",
        "version": "1.0.0",
        "default_chart_type": "line",
        "default_time_range": "1y",
        "max_concurrent_downloads": 3,
        "cache_data": True,
        "auto_save_interval": 300
    }
    
    create_file_if_not_exists(
        "configs/settings/app_config.json",
        json.dumps(app_config, indent=2)
    )
    
    # Create empty tracked assets file
    empty_tracked_assets = {
        "equities": {},
        "bonds": {},
        "crypto": {},
        "commodities": {},
        "futures": {}
    }
    
    create_file_if_not_exists(
        "data/metadata/tracked_assets.json",
        json.dumps(empty_tracked_assets, indent=2)
    )
    
    # Create filepath registry
    filepath_registry = {
        "last_updated": "2024-01-01T00:00:00",
        "version": "1.0",
        "paths": paths_config
    }
    
    create_file_if_not_exists(
        "data/metadata/filepath_registry.json", 
        json.dumps(filepath_registry, indent=2)
    )
    
    # Create basic documentation
    create_file_if_not_exists(
        "docs/architecture.md",
        """# Infinity Stock Analysis - Architecture

## Overview
This document describes the software architecture of the Infinity Stock Analysis application.

## Components
- **GUI Layer**: User interface components using tkinter
- **Data Management**: Handles asset data download and storage
- **Analysis Tools**: Data processing and analysis functions
- **Project Management**: Save/load project configurations
- **Utilities**: Helper functions and filepath management

## Data Flow
1. User selects assets through GUI
2. Data Manager downloads from Yahoo Finance
3. Data stored in JSON format by asset type
4. Analysis tools process data for visualization
5. Charts displayed using matplotlib
6. Projects saved for future use

## File Organization
- Modular filepath system for easy reorganization
- Asset data separated by type
- Project configurations saved independently
- Metadata tracks all assets and file locations
"""
    )
    
    print("\n" + "="*50)
    print("Project setup complete!")
    print("="*50)
    print("\nNext steps:")
    print("1. Activate your virtual environment: source venv/bin/activate")
    print("2. Install requirements: pip install -r requirements.txt")
    print("3. Run the application: python main.py")
    print("\nDirectory structure created successfully!")


if __name__ == "__main__":
    setup_project_structure()
