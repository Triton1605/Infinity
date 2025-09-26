"""
Terminal-based application for Infinity Stock Analysis Software.
Provides command-line interface for all non-graphing functionality.
"""

import sys
import os
from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd
import json

from src.data_management.data_manager import DataManager
from src.terminal.terminal_commands import TerminalCommands
from src.terminal.terminal_display import TerminalDisplay


class TerminalApplication:
    """Main terminal application controller."""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.commands = TerminalCommands(self.data_manager)
        self.display = TerminalDisplay()
        self.running = True
        
        # Command mapping
        self.command_map = {
            # Asset Management
            'add': self.commands.add_asset,
            'update': self.commands.update_asset,
            'updateall': self.commands.update_all_assets,
            'remove': self.commands.remove_asset,
            'list': self.commands.list_assets,
            'view': self.commands.view_asset,
            'search': self.commands.search_assets,
            
            # Analysis
            'analyze': self.commands.analyze_asset,
            'compare': self.commands.compare_assets,
            'events': self.commands.manage_events,
            'patterns': self.commands.find_patterns,
            'sentiment': self.commands.analyze_sentiment,
            
            # Data Export
            'export': self.commands.export_data,
            'report': self.commands.generate_report,
            
            # General
            'help': self.show_help,
            'clear': self.clear_screen,
            'exit': self.exit_app,
            'quit': self.exit_app,
        }
    
    def run(self):
        """Main application loop."""
        self.display.show_welcome()
        self.show_help()
        
        while self.running:
            try:
                # Get user input
                command_line = input("\n> ").strip()
                
                if not command_line:
                    continue
                
                # Parse command and arguments
                parts = command_line.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                # Execute command
                if command in self.command_map:
                    self.command_map[command](args)
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for a list of available commands.")
                    
            except KeyboardInterrupt:
                print("\n\nUse 'exit' or 'quit' to close the application.")
            except Exception as e:
                print(f"\nError: {str(e)}")
                print("Type 'help' for command usage.")
    
    def show_help(self, args=""):
        """Show help information."""
        if args:
            # Show help for specific command
            command = args.strip().lower()
            if command in self.command_map:
                self.display.show_command_help(command)
            else:
                print(f"Unknown command: {command}")
        else:
            # Show general help
            self.display.show_help()
    
    def clear_screen(self, args=""):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
        self.display.show_welcome()
    
    def exit_app(self, args=""):
        """Exit the application."""
        print("\nThank you for using Infinity Stock Analysis!")
        print("Goodbye.\n")
        self.running = False
        sys.exit(0)
