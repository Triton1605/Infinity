import json
import os
from pathlib import Path
from typing import Dict, Optional


class FilepathManager:
    """Manages all file paths through a centralized configuration system."""
    
    def __init__(self, config_path: str = "configs/filepaths/paths.json"):
        self.config_path = config_path
        self.paths = self._load_paths()
        self._ensure_directories()
    
    def _load_paths(self) -> Dict[str, str]:
        """Load file paths from configuration JSON."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default paths if config doesn't exist
            default_paths = {
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
            self._save_paths(default_paths)
            return default_paths
    
    def _save_paths(self, paths: Dict[str, str]) -> None:
        """Save paths to configuration file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(paths, f, indent=2)
    
    def _ensure_directories(self) -> None:
        """Create all directories if they don't exist."""
        for key, path in self.paths.items():
            if key.endswith('_dir'):
                os.makedirs(path, exist_ok=True)
    
    def get_path(self, key: str) -> str:
        """Get a specific path by key."""
        if key not in self.paths:
            raise ValueError(f"Path key '{key}' not found in configuration")
        return self.paths[key]
    
    def get_asset_dir(self, asset_type: str) -> str:
        """Get directory path for specific asset type."""
        asset_key = f"{asset_type}_dir"
        return self.get_path(asset_key)
    
    def get_asset_file_path(self, asset_type: str, symbol: str) -> str:
        """Get full file path for an individual asset's JSON file."""
        asset_dir = self.get_asset_dir(asset_type)
        return os.path.join(asset_dir, f"{symbol}.json")
    
    def update_path(self, key: str, new_path: str) -> None:
        """Update a specific path and save to config."""
        self.paths[key] = new_path
        self._save_paths(self.paths)
        self._ensure_directories()
    
    def reload_paths(self) -> None:
        """Reload paths from configuration file."""
        self.paths = self._load_paths()
        self._ensure_directories()


# Global instance for easy access throughout the application
filepath_manager = FilepathManager()
