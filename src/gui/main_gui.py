import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import pandas as pd
from typing import Dict, List, Optional
from src.data_management.data_manager import DataManager
from src.projects.project_manager import project_manager, graphing_project_manager
from src.gui.graphing_window import GraphingWindow
from src.gui.add_asset_dialog import AddAssetDialog


class MainApplication:
    """Main application window and controller."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Infinity - Stock Analysis Software")
        self.root.geometry("800x600")
        
        # Initialize managers
        self.data_manager = DataManager()
        
        # Track open windows
        self.open_windows = []
        
        # Initialize GUI
        self.setup_gui()
        
    def setup_gui(self):
        """Set up the main GUI elements."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Infinity Stock Analysis", 
                               font=('Arial', 24, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 30))
        
        # Left column - Project options
        project_frame = ttk.LabelFrame(main_frame, text="Projects", padding="15")
        project_frame.grid(row=1, column=0, padx=(0, 10), pady=(0, 20), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(project_frame, text="New Graphing Project", 
                  command=self.new_graphing_project, width=25).grid(row=0, column=0, pady=5)
        
        ttk.Button(project_frame, text="Open Saved Project", 
                  command=self.open_project_dialog, width=25).grid(row=1, column=0, pady=5)
        
        # Right column - Asset management
        asset_frame = ttk.LabelFrame(main_frame, text="Asset Management", padding="15")
        asset_frame.grid(row=1, column=1, padx=(10, 0), pady=(0, 20), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(asset_frame, text="Add New Asset", 
                  command=self.add_asset_dialog, width=25).grid(row=0, column=0, pady=5)
        
        ttk.Button(asset_frame, text="View Assets", 
                  command=self.view_assets, width=25).grid(row=1, column=0, pady=5)
        
        ttk.Button(asset_frame, text="Update Asset Data", 
                  command=self.update_asset_dialog, width=25).grid(row=2, column=0, pady=5)
        
        ttk.Button(asset_frame, text="Update ALL Assets", 
                  command=self.update_all_assets, width=25).grid(row=3, column=0, pady=5)
        
        # Bottom section - Recent projects
        recent_frame = ttk.LabelFrame(main_frame, text="Recent Projects", padding="15")
        recent_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Treeview for recent projects
        columns = ('name', 'type', 'modified')
        self.recent_tree = ttk.Treeview(recent_frame, columns=columns, show='headings', height=8)
        
        self.recent_tree.heading('name', text='Project Name')
        self.recent_tree.heading('type', text='Type')
        self.recent_tree.heading('modified', text='Last Modified')
        
        self.recent_tree.column('name', width=300)
        self.recent_tree.column('type', width=150)
        self.recent_tree.column('modified', width=200)
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(recent_frame, orient=tk.VERTICAL, command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=scrollbar.set)
        
        self.recent_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons for recent projects
        button_frame = ttk.Frame(recent_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(button_frame, text="Open Selected", 
                  command=self.open_selected_project).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(button_frame, text="Delete Selected", 
                  command=self.delete_selected_project).grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="Refresh List", 
                  command=self.refresh_project_list).grid(row=0, column=2, padx=(5, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        recent_frame.columnconfigure(0, weight=1)
        recent_frame.rowconfigure(0, weight=1)
        
        # Double-click to open project
        self.recent_tree.bind('<Double-1>', lambda e: self.open_selected_project())
        
        # Load recent projects
        self.refresh_project_list()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def new_graphing_project(self):
        """Create a new graphing project."""
        try:
            graphing_window = GraphingWindow(self.root, self.data_manager)
            self.open_windows.append(graphing_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create graphing project: {str(e)}")
    
    def add_asset_dialog(self):
        """Open dialog to add a new asset."""
        try:
            dialog = AddAssetDialog(self.root, self.data_manager)
            self.root.wait_window(dialog.dialog)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open add asset dialog: {str(e)}")
    
    def view_assets(self):
        """Open window to view all assets."""
        self.show_assets_window()
    
    def update_asset_dialog(self):
        """Open dialog to update existing asset data."""
        assets = self.data_manager.get_asset_list()
        if not assets:
            messagebox.showinfo("No Assets", "No assets found. Add some assets first.")
            return
        
        # Create selection dialog
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Select Asset to Update")
        selection_window.geometry("400x300")
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        ttk.Label(selection_window, text="Select asset to update:", 
                 font=('Arial', 12)).pack(pady=10)
        
        # Listbox with assets
        listbox_frame = ttk.Frame(selection_window)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        listbox = tk.Listbox(listbox_frame)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        for symbol, asset_type in assets:
            listbox.insert(tk.END, f"{symbol} ({asset_type})")
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(selection_window)
        button_frame.pack(pady=10)
        
        def update_selected():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an asset to update.")
                return
            
            symbol, asset_type = assets[selection[0]]
            selection_window.destroy()
            
            # Show progress dialog and update in background
            self.update_asset_with_progress(symbol, asset_type)
        
        ttk.Button(button_frame, text="Update", command=update_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=selection_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def update_asset_with_progress(self, symbol: str, asset_type: str):
        """Update asset data with progress indicator."""
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Updating Asset")
        progress_window.geometry("300x100")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text=f"Updating {symbol}...").pack(pady=10)
        progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        def update_in_thread():
            try:
                success = self.data_manager.update_asset_data(symbol, asset_type)
                
                # Update UI in main thread
                def update_ui():
                    progress_window.destroy()
                    if success:
                        messagebox.showinfo("Success", f"Asset {symbol} updated successfully!")
                    else:
                        messagebox.showerror("Error", f"Failed to update asset {symbol}")
                
                self.root.after(0, update_ui)
                
            except Exception as e:
                def show_error():
                    progress_window.destroy()
                    messagebox.showerror("Error", f"Error updating asset: {str(e)}")
                
                self.root.after(0, show_error)
        
        threading.Thread(target=update_in_thread, daemon=True).start()
    
    def update_all_assets(self):
        """Update all tracked assets at once."""
        tracked_assets = self.data_manager.get_tracked_assets()
        
        # Count total assets
        total_assets = sum(len(assets) for assets in tracked_assets.values())
        
        if total_assets == 0:
            messagebox.showinfo("No Assets", "No assets found to update.")
            return
        
        # Confirm bulk update
        result = messagebox.askyesno("Confirm Bulk Update", 
                                   f"Update all {total_assets} tracked assets?\n\n"
                                   f"This may take several minutes and will download "
                                   f"fresh data for every asset.")
        
        if not result:
            return
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Updating All Assets")
        progress_window.geometry("400x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Progress widgets
        main_frame = ttk.Frame(progress_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Updating All Assets", font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        # Current asset label
        current_label = ttk.Label(main_frame, text="Preparing...")
        current_label.pack(pady=5)
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=total_assets)
        progress_bar.pack(fill=tk.X, pady=10)
        
        # Status label
        status_label = ttk.Label(main_frame, text=f"0 of {total_assets} assets updated")
        status_label.pack(pady=5)
        
        # Results
        self.update_results = {"success": 0, "failed": 0, "failed_assets": []}
        
        def update_in_thread():
            current_count = 0
            
            for asset_type, assets in tracked_assets.items():
                for symbol in assets.keys():
                    current_count += 1
                    
                    # Update UI in main thread
                    def update_ui(symbol=symbol, count=current_count, asset_type=asset_type):
                        current_label.config(text=f"Updating {symbol} ({asset_type})...")
                        progress_var.set(count)
                        status_label.config(text=f"{count} of {total_assets} assets processed")
                        progress_window.update()
                    
                    self.root.after(0, update_ui)
                    
                    # Update the asset
                    try:
                        success = self.data_manager.update_asset_data(symbol, asset_type)
                        if success:
                            self.update_results["success"] += 1
                        else:
                            self.update_results["failed"] += 1
                            self.update_results["failed_assets"].append(f"{symbol} ({asset_type})")
                    except Exception as e:
                        self.update_results["failed"] += 1
                        self.update_results["failed_assets"].append(f"{symbol} ({asset_type}): {str(e)}")
                    
                    # Small delay to prevent API rate limiting
                    import time
                    time.sleep(0.5)
            
            # Show completion in main thread
            def show_completion():
                progress_window.destroy()
                
                success_count = self.update_results["success"]
                failed_count = self.update_results["failed"]
                
                if failed_count == 0:
                    messagebox.showinfo("Update Complete", 
                                      f"Successfully updated all {success_count} assets!")
                else:
                    failed_list = "\n".join(self.update_results["failed_assets"][:10])
                    if len(self.update_results["failed_assets"]) > 10:
                        failed_list += f"\n... and {len(self.update_results['failed_assets']) - 10} more"
                    
                    messagebox.showwarning("Update Complete with Errors", 
                                         f"Updated {success_count} assets successfully.\n"
                                         f"Failed to update {failed_count} assets:\n\n{failed_list}")
            
            self.root.after(0, show_completion)
        
        # Cancel button
        def cancel_update():
            progress_window.destroy()
            messagebox.showinfo("Cancelled", "Asset update cancelled.")
        
        ttk.Button(main_frame, text="Cancel", command=cancel_update).pack(pady=10)
        
        # Start update in background thread
        import threading
        threading.Thread(target=update_in_thread, daemon=True).start()
    
    def update_all_assets(self):
        """Update all tracked assets at once."""
        tracked_assets = self.data_manager.get_tracked_assets()
        
        # Count total assets
        total_assets = sum(len(assets) for assets in tracked_assets.values())
        
        if total_assets == 0:
            messagebox.showinfo("No Assets", "No assets found to update.")
            return
        
        # Confirm bulk update
        result = messagebox.askyesno("Confirm Bulk Update", 
                                   f"Update all {total_assets} tracked assets?\n\n"
                                   f"This may take several minutes and will download "
                                   f"fresh data for every asset.")
        
        if not result:
            return
        
        # Create progress window
        progress_window = tk.Toplevel(self.root)
        progress_window.title("Updating All Assets")
        progress_window.geometry("400x200")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Progress widgets
        main_frame = ttk.Frame(progress_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Updating All Assets", font=('Arial', 14, 'bold')).pack(pady=(0, 10))
        
        # Current asset label
        current_label = ttk.Label(main_frame, text="Preparing...")
        current_label.pack(pady=5)
        
        # Progress bar
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=total_assets)
        progress_bar.pack(fill=tk.X, pady=10)
        
        # Status label
        status_label = ttk.Label(main_frame, text=f"0 of {total_assets} assets updated")
        status_label.pack(pady=5)
        
        # Results
        self.update_results = {"success": 0, "failed": 0, "failed_assets": []}
        
        def update_in_thread():
            current_count = 0
            
            for asset_type, assets in tracked_assets.items():
                for symbol in assets.keys():
                    current_count += 1
                    
                    # Update UI in main thread
                    def update_ui(symbol=symbol, count=current_count, asset_type=asset_type):
                        current_label.config(text=f"Updating {symbol} ({asset_type})...")
                        progress_var.set(count)
                        status_label.config(text=f"{count} of {total_assets} assets processed")
                        progress_window.update()
                    
                    self.root.after(0, update_ui)
                    
                    # Update the asset
                    try:
                        success = self.data_manager.update_asset_data(symbol, asset_type)
                        if success:
                            self.update_results["success"] += 1
                        else:
                            self.update_results["failed"] += 1
                            self.update_results["failed_assets"].append(f"{symbol} ({asset_type})")
                    except Exception as e:
                        self.update_results["failed"] += 1
                        self.update_results["failed_assets"].append(f"{symbol} ({asset_type}): {str(e)}")
                    
                    # Small delay to prevent API rate limiting
                    import time
                    time.sleep(0.5)
            
            # Show completion in main thread
            def show_completion():
                progress_window.destroy()
                
                success_count = self.update_results["success"]
                failed_count = self.update_results["failed"]
                
                if failed_count == 0:
                    messagebox.showinfo("Update Complete", 
                                      f"Successfully updated all {success_count} assets!")
                else:
                    failed_list = "\n".join(self.update_results["failed_assets"][:10])
                    if len(self.update_results["failed_assets"]) > 10:
                        failed_list += f"\n... and {len(self.update_results['failed_assets']) - 10} more"
                    
                    messagebox.showwarning("Update Complete with Errors", 
                                         f"Updated {success_count} assets successfully.\n"
                                         f"Failed to update {failed_count} assets:\n\n{failed_list}")
            
            self.root.after(0, show_completion)
        
        # Cancel button
        def cancel_update():
            progress_window.destroy()
            messagebox.showinfo("Cancelled", "Asset update cancelled.")
        
        ttk.Button(main_frame, text="Cancel", command=cancel_update).pack(pady=10)
        
        # Start update in background thread
        import threading
        threading.Thread(target=update_in_thread, daemon=True).start()
    
    def open_project_dialog(self):
        """Open dialog to select and open a saved project."""
        projects = project_manager.get_saved_projects()
        if not projects:
            messagebox.showinfo("No Projects", "No saved projects found.")
            return
        
        # Create selection dialog
        selection_window = tk.Toplevel(self.root)
        selection_window.title("Open Project")
        selection_window.geometry("600x400")
        selection_window.transient(self.root)
        selection_window.grab_set()
        
        ttk.Label(selection_window, text="Select project to open:", 
                 font=('Arial', 12)).pack(pady=10)
        
        # Treeview with projects
        tree_frame = ttk.Frame(selection_window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        columns = ('name', 'type', 'modified')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        
        tree.heading('name', text='Project Name')
        tree.heading('type', text='Type')
        tree.heading('modified', text='Last Modified')
        
        tree.column('name', width=250)
        tree.column('type', width=100)
        tree.column('modified', width=200)
        
        for project in projects:
            tree.insert('', tk.END, values=(
                project['project_name'],
                project['project_type'],
                project['last_modified'][:19].replace('T', ' ')
            ))
        
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        button_frame = ttk.Frame(selection_window)
        button_frame.pack(pady=10)
        
        def open_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select a project to open.")
                return
            
            item = tree.item(selection[0])
            project_name = item['values'][0]
            project_type = item['values'][1]
            
            selection_window.destroy()
            self.open_project(project_name, project_type)
        
        ttk.Button(button_frame, text="Open", command=open_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=selection_window.destroy).pack(side=tk.LEFT, padx=5)
        
        # Double-click to open
        tree.bind('<Double-1>', lambda e: open_selected())
    
    def open_project(self, project_name: str, project_type: str):
        """Open a specific project."""
        try:
            project_data = project_manager.load_project(project_name)
            if not project_data:
                messagebox.showerror("Error", f"Could not load project: {project_name}")
                return
            
            if project_type == "graphing":
                graphing_window = GraphingWindow(self.root, self.data_manager, project_data)
                self.open_windows.append(graphing_window)
            else:
                messagebox.showwarning("Unsupported", f"Project type '{project_type}' not yet supported.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open project: {str(e)}")
    
    def open_selected_project(self):
        """Open the currently selected project from the recent list."""
        selection = self.recent_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a project to open.")
            return
        
        item = self.recent_tree.item(selection[0])
        project_name = item['values'][0]
        project_type = item['values'][1]
        
        self.open_project(project_name, project_type)
    
    def delete_selected_project(self):
        """Delete the currently selected project."""
        selection = self.recent_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a project to delete.")
            return
        
        item = self.recent_tree.item(selection[0])
        project_name = item['values'][0]
        
        # Confirm deletion
        result = messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete project '{project_name}'?\n\nThis action cannot be undone.")
        
        if result:
            if project_manager.delete_project(project_name):
                messagebox.showinfo("Success", f"Project '{project_name}' deleted successfully.")
                self.refresh_project_list()
            else:
                messagebox.showerror("Error", f"Failed to delete project '{project_name}'.")
    
    def refresh_project_list(self):
        """Refresh the list of recent projects."""
        # Clear existing items
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)
        
        # Load and display projects
        projects = project_manager.get_saved_projects()
        for project in projects:
            # Format the date for display
            modified_date = project['last_modified'][:19].replace('T', ' ')
            
            self.recent_tree.insert('', tk.END, values=(
                project['project_name'],
                project['project_type'],
                modified_date
            ))

    def show_assets_window(self):
        """Show window with all tracked assets."""
        assets_window = tk.Toplevel(self.root)
        assets_window.title("View Assets")
        assets_window.geometry("1100x600")  # Made wider for IPO column
        
        # Create main frame
        main_frame = ttk.Frame(assets_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="Tracked Assets", font=('Arial', 16, 'bold')).grid(row=0, column=0, pady=(0, 10))
        
        # Create notebook for different asset types
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        tracked_assets = self.data_manager.get_tracked_assets()
        
        # Store references to trees for refreshing
        self.asset_trees = {}
        self.asset_tree_types = {}  # Store asset type for each tree
        
        for asset_type, assets in tracked_assets.items():
            if not assets:  # Skip empty asset types
                continue
                
            # Create frame for this asset type
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=asset_type.title())
            
            # Create treeview for assets - added IPO date column
            if asset_type == "equities":
                columns = ('symbol', 'name', 'price', 'ipo_date', 'market_cap', 'last_update')
                column_widths = {'symbol': 80, 'name': 200, 'price': 100, 'ipo_date': 100, 'market_cap': 120, 'last_update': 150}
                headings = {'symbol': 'Symbol', 'name': 'Company Name', 'price': 'Latest Price', 
                           'ipo_date': 'IPO Date', 'market_cap': 'Market Cap', 'last_update': 'Last Updated'}
            else:
                columns = ('symbol', 'name', 'price', 'last_update')
                column_widths = {'symbol': 100, 'name': 300, 'price': 100, 'last_update': 150}
                headings = {'symbol': 'Symbol', 'name': 'Company Name', 'price': 'Latest Price', 'last_update': 'Last Updated'}
            
            tree = ttk.Treeview(frame, columns=columns, show='headings')
            
            # Set up columns
            for col in columns:
                tree.heading(col, text=headings[col])
                tree.column(col, width=column_widths[col])
            
            # Add assets to tree
            for symbol, data in assets.items():
                if asset_type == "equities":
                    # Format IPO date
                    ipo_date = data.get('ipo_date', 'Unknown')
                    if ipo_date and ipo_date != 'Unknown':
                        try:
                            ipo_formatted = pd.to_datetime(ipo_date).strftime('%Y-%m-%d')
                        except:
                            ipo_formatted = str(ipo_date)
                    else:
                        ipo_formatted = 'Unknown'
                    
                    # Format market cap
                    market_cap = data.get('latest_market_cap')
                    if market_cap:
                        market_cap_billions = market_cap / 1e9
                        market_cap_str = f"${market_cap_billions:.2f}B"
                    else:
                        market_cap_str = 'Unknown'
                    
                    tree.insert('', tk.END, values=(
                        symbol,
                        data.get('company_name', 'Unknown'),
                        f"${data.get('latest_price', 'N/A')}",
                        ipo_formatted,
                        market_cap_str,
                        data.get('last_data_pull', 'Unknown')[:19].replace('T', ' ')
                    ))
                else:
                    # Non-equity assets (no IPO date or market cap)
                    tree.insert('', tk.END, values=(
                        symbol,
                        data.get('company_name', 'Unknown'),
                        f"${data.get('latest_price', 'N/A')}",
                        data.get('last_data_pull', 'Unknown')[:19].replace('T', ' ')
                    ))
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            
            # Add buttons for this asset type
            button_frame = ttk.Frame(frame)
            button_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0), sticky=(tk.W, tk.E))
            
            # Analyze button
            analyze_btn = ttk.Button(button_frame, text="Analyze Asset", 
                                   command=lambda t=tree, at=asset_type: self.analyze_selected_asset(t, at))
            analyze_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Update button
            update_btn = ttk.Button(button_frame, text="Update Selected", 
                                  command=lambda t=tree, at=asset_type: self.update_selected_asset(t, at))
            update_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Remove button
            remove_btn = ttk.Button(button_frame, text="Remove Selected", 
                                  command=lambda t=tree, at=asset_type, aw=assets_window: self.remove_selected_asset(t, at, aw))
            remove_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            # Refresh button
            refresh_btn = ttk.Button(button_frame, text="Refresh View", 
                                   command=lambda aw=assets_window: self.refresh_assets_window(aw))
            refresh_btn.pack(side=tk.RIGHT)
            
            # Double-click to analyze
            tree.bind('<Double-1>', lambda e, t=tree, at=asset_type: self.analyze_selected_asset(t, at))
            
            frame.columnconfigure(0, weight=1)
            frame.rowconfigure(0, weight=1)
            
            # Store tree reference and asset type
            self.asset_trees[asset_type] = tree
            self.asset_tree_types[tree] = asset_type
        
        # Configure grid weights
        assets_window.columnconfigure(0, weight=1)
        assets_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

    def analyze_selected_asset(self, tree, asset_type):
        """Open analysis window for the selected asset."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an asset to analyze.")
            return
        
        item = tree.item(selection[0])
        symbol = item['values'][0]
        
        try:
            from src.gui.asset_analysis_window import AssetAnalysisWindow
            analysis_window = AssetAnalysisWindow(self.root, self.data_manager, symbol, asset_type)
            self.open_windows.append(analysis_window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open analysis window: {str(e)}")
    
    def update_selected_asset(self, tree, asset_type):
        """Update the selected asset's data."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an asset to update.")
            return
        
        item = tree.item(selection[0])
        symbol = item['values'][0]
        
        self.update_asset_with_progress(symbol, asset_type)
        """Update the selected asset's data."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an asset to update.")
            return
        
        item = tree.item(selection[0])
        symbol = item['values'][0]
        
        self.update_asset_with_progress(symbol, asset_type)
    
    def remove_selected_asset(self, tree, asset_type, assets_window):
        """Remove the selected asset from tracking."""
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an asset to remove.")
            return
        
        item = tree.item(selection[0])
        symbol = item['values'][0]
        company_name = item['values'][1]
        
        # Confirm removal
        result = messagebox.askyesno(
            "Confirm Removal", 
            f"Are you sure you want to remove {symbol} ({company_name})?\n\n"
            f"This will delete all stored data for this asset and cannot be undone."
        )
        
        if result:
            if self.data_manager.remove_asset_from_tracking(symbol, asset_type):
                messagebox.showinfo("Success", f"Asset {symbol} removed successfully!")
                # Refresh the assets window
                self.refresh_assets_window(assets_window)
            else:
                messagebox.showerror("Error", f"Failed to remove asset {symbol}.")
    
    def refresh_assets_window(self, assets_window):
        """Refresh the assets window by closing and reopening it."""
        assets_window.destroy()
        self.show_assets_window()
    
    def on_closing(self):
        """Handle application closing."""
        # Close all open windows
        for window in self.open_windows:
            try:
                if hasattr(window, 'window') and window.window.winfo_exists():
                    window.window.destroy()
            except:
                pass
        
        # Ensure the application actually exits
        try:
            self.root.quit()  # Stop the mainloop
            self.root.destroy()  # Destroy the window
        except:
            pass
        
        # Force exit if needed
        import sys
        sys.exit(0)
    
    def run(self):
        """Start the application."""
        self.root.mainloop()
