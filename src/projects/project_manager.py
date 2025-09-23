import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from utils.filepath_manager import filepath_manager


class ProjectManager:
    """Manages project creation, saving, loading, and deletion."""
    
    def __init__(self):
        self.filepath_manager = filepath_manager
        self.saves_dir = self.filepath_manager.get_path("saves_dir")
        os.makedirs(self.saves_dir, exist_ok=True)
    
    def create_project(self, project_type: str, project_name: str, config: Dict[str, Any]) -> Dict:
        """
        Create a new project configuration.
        
        Args:
            project_type: Type of project ('graphing', 'options_simulation', etc.)
            project_name: User-defined project name
            config: Project-specific configuration
            
        Returns:
            Complete project dictionary
        """
        project_data = {
            "project_name": project_name,
            "project_type": project_type,
            "created_date": datetime.now().isoformat(),
            "last_modified": datetime.now().isoformat(),
            "config": config,
            "version": "1.0"
        }
        
        return project_data
    
    def save_project(self, project_data: Dict, project_name: Optional[str] = None) -> bool:
        """
        Save a project to disk.
        
        Args:
            project_data: Project data dictionary
            project_name: Optional override for project name
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            name = project_name or project_data.get("project_name", "untitled_project")
            
            # Update last modified time
            project_data["last_modified"] = datetime.now().isoformat()
            
            # Create filename (sanitize name for filesystem)
            safe_name = self._sanitize_filename(name)
            filename = f"{safe_name}.json"
            filepath = os.path.join(self.saves_dir, filename)
            
            # Save to JSON
            with open(filepath, 'w') as f:
                json.dump(project_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error saving project: {str(e)}")
            return False
    
    def load_project(self, project_name: str) -> Optional[Dict]:
        """
        Load a project from disk.
        
        Args:
            project_name: Name of project to load
            
        Returns:
            Project data dictionary or None if not found
        """
        try:
            safe_name = self._sanitize_filename(project_name)
            filename = f"{safe_name}.json"
            filepath = os.path.join(self.saves_dir, filename)
            
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            print(f"Error loading project: {str(e)}")
            return None
    
    def get_saved_projects(self) -> List[Dict]:
        """
        Get list of all saved projects with metadata.
        
        Returns:
            List of project metadata dictionaries
        """
        projects = []
        
        try:
            if not os.path.exists(self.saves_dir):
                return projects
            
            for filename in os.listdir(self.saves_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.saves_dir, filename)
                    
                    try:
                        with open(filepath, 'r') as f:
                            project_data = json.load(f)
                        
                        project_info = {
                            "filename": filename,
                            "project_name": project_data.get("project_name", "Unknown"),
                            "project_type": project_data.get("project_type", "Unknown"),
                            "created_date": project_data.get("created_date", "Unknown"),
                            "last_modified": project_data.get("last_modified", "Unknown"),
                            "file_size": os.path.getsize(filepath)
                        }
                        
                        projects.append(project_info)
                        
                    except json.JSONDecodeError:
                        print(f"Warning: Corrupted project file {filename}")
                        continue
            
            # Sort by last modified date (newest first)
            projects.sort(key=lambda x: x["last_modified"], reverse=True)
            
        except Exception as e:
            print(f"Error getting saved projects: {str(e)}")
        
        return projects
    
    def delete_project(self, project_name: str) -> bool:
        """
        Delete a project from disk.
        
        Args:
            project_name: Name of project to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            safe_name = self._sanitize_filename(project_name)
            filename = f"{safe_name}.json"
            filepath = os.path.join(self.saves_dir, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            else:
                print(f"Project file not found: {filepath}")
                return False
                
        except Exception as e:
            print(f"Error deleting project: {str(e)}")
            return False
    
    def project_exists(self, project_name: str) -> bool:
        """
        Check if a project exists.
        
        Args:
            project_name: Name of project to check
            
        Returns:
            True if project exists, False otherwise
        """
        safe_name = self._sanitize_filename(project_name)
        filename = f"{safe_name}.json"
        filepath = os.path.join(self.saves_dir, filename)
        
        return os.path.exists(filepath)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Limit length
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        # Ensure not empty
        if not sanitized:
            sanitized = "untitled_project"
        
        return sanitized


class GraphingProjectManager(ProjectManager):
    """Specialized project manager for graphing projects."""
    
    def create_graphing_project(self, project_name: str, 
                              assets: List[Dict], 
                              chart_config: Dict,
                              date_config: Dict,
                              exclusions: Dict) -> Dict:
        """
        Create a graphing project with specific configuration.
        
        Args:
            project_name: Name of the project
            assets: List of assets to display
            chart_config: Chart display configuration
            date_config: Date range and resolution settings
            exclusions: Date/range exclusions
            
        Returns:
            Complete graphing project dictionary
        """
        config = {
            "assets": assets,  # [{symbol, asset_type, display_name, color, etc.}]
            "chart_config": {
                "chart_types": chart_config.get("chart_types", ["line"]),  # line, bar, candlestick
                "overlays": chart_config.get("overlays", []),
                "include_weekends": chart_config.get("include_weekends", False),
                "resolution": chart_config.get("resolution", "daily")  # daily, weekly, monthly
            },
            "date_config": {
                "time_range": date_config.get("time_range", "1y"),  # 1d, 1w, 1m, 1y, 5y, all
                "custom_start": date_config.get("custom_start"),
                "custom_end": date_config.get("custom_end")
            },
            "exclusions": {
                "date_ranges": exclusions.get("date_ranges", []),  # [{start, end, reason}]
                "specific_dates": exclusions.get("specific_dates", [])  # [{date, reason}]
            }
        }
        
        return self.create_project("graphing", project_name, config)


# Default instance
project_manager = ProjectManager()
graphing_project_manager = GraphingProjectManager()
