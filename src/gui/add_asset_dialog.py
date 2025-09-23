import tkinter as tk
from tkinter import ttk, messagebox
import threading
from typing import Optional
from src.data_management.data_manager import DataManager


class AddAssetDialog:
    """Dialog for adding new assets to the system."""
    
    def __init__(self, parent, data_manager: DataManager):
        self.parent = parent
        self.data_manager = data_manager
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add New Asset")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_gui()
        
        # Focus on symbol entry
        self.symbol_entry.focus()
    
    def setup_gui(self):
        """Set up the dialog GUI."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        ttk.Label(main_frame, text="Add New Asset", font=('Arial', 14, 'bold')).grid(
            row=0, column=0, columnspan=2, pady=(0, 20)
        )
        
        # Symbol entry
        ttk.Label(main_frame, text="Asset Symbol:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.symbol_entry = ttk.Entry(main_frame, width=25)
        self.symbol_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Symbol examples
        examples_text = "Examples: AAPL, TSLA, BTC-USD, GC=F"
        ttk.Label(main_frame, text=examples_text, font=('Arial', 8), foreground='gray').grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0)
        )
        
        # Asset type selection
        ttk.Label(main_frame, text="Asset Type:").grid(row=3, column=0, sticky=tk.W, pady=(15, 5))
        
        self.asset_type = tk.StringVar(value="equities")
        asset_types = [
            ("Stocks/Equities", "equities"),
            ("Cryptocurrency", "crypto"),
            ("Commodities", "commodities"),
            ("Futures", "futures"),
            ("Bonds", "bonds")
        ]
        
        type_frame = ttk.Frame(main_frame)
        type_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=(15, 5), padx=(10, 0))
        
        for i, (display_name, value) in enumerate(asset_types):
            ttk.Radiobutton(type_frame, text=display_name, variable=self.asset_type, 
                           value=value).grid(row=i, column=0, sticky=tk.W, pady=2)
        
        # Data period selection
        ttk.Label(main_frame, text="Data Period:").grid(row=4, column=0, sticky=tk.W, pady=(15, 5))
        
        self.period = tk.StringVar(value="max")
        period_combo = ttk.Combobox(main_frame, textvariable=self.period, width=22, state="readonly")
        period_combo['values'] = ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        period_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(15, 5), padx=(10, 0))
        
        # Progress bar (initially hidden)
        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.grid(row=5, column=0, columnspan=2, pady=(20, 10), sticky=(tk.W, tk.E))
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.grid(row=0, column=0, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Initially hide progress
        self.progress_frame.grid_remove()
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        
        self.add_button = ttk.Button(button_frame, text="Add Asset", command=self.add_asset)
        self.add_button.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).grid(row=0, column=1)
        
        # Configure grid weights
        self.dialog.columnconfigure(0, weight=1)
        self.dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        self.progress_frame.columnconfigure(0, weight=1)
        
        # Bind Enter key to add asset
        self.dialog.bind('<Return>', lambda e: self.add_asset())
        
        # Handle dialog closing
        self.dialog.protocol("WM_DELETE_WINDOW", self.dialog.destroy)
    
    def add_asset(self):
        """Add the asset with validation."""
        symbol = self.symbol_entry.get().strip().upper()
        asset_type = self.asset_type.get()
        period = self.period.get()
        
        # Validation
        if not symbol:
            messagebox.showerror("Error", "Please enter an asset symbol.")
            self.symbol_entry.focus()
            return
        
        # Check if asset already exists
        if self.data_manager.asset_exists(symbol, asset_type):
            result = messagebox.askyesno(
                "Asset Exists", 
                f"Asset {symbol} already exists in {asset_type}. Do you want to update it instead?"
            )
            if result:
                self.update_existing_asset(symbol, asset_type)
                return
            else:
                return
        
        # Show progress and disable button
        self.show_progress(f"Downloading data for {symbol}...")
        self.add_button.config(state='disabled')
        
        # Download in background thread
        threading.Thread(target=self.download_asset, args=(symbol, asset_type, period), daemon=True).start()
    
    def download_asset(self, symbol: str, asset_type: str, period: str):
        """Download asset data in background thread."""
        try:
            success = self.data_manager.add_asset_to_tracking(symbol, asset_type)
            
            # Update UI in main thread
            self.dialog.after(0, lambda: self.download_complete(success, symbol))
            
        except Exception as e:
            self.dialog.after(0, lambda: self.download_error(str(e)))
    
    def update_existing_asset(self, symbol: str, asset_type: str):
        """Update existing asset data."""
        self.show_progress(f"Updating data for {symbol}...")
        self.add_button.config(state='disabled')
        
        def update_in_thread():
            try:
                success = self.data_manager.update_asset_data(symbol, asset_type)
                self.dialog.after(0, lambda: self.download_complete(success, symbol, is_update=True))
            except Exception as e:
                self.dialog.after(0, lambda: self.download_error(str(e)))
        
        threading.Thread(target=update_in_thread, daemon=True).start()
    
    def download_complete(self, success: bool, symbol: str, is_update: bool = False):
        """Handle download completion."""
        self.hide_progress()
        self.add_button.config(state='normal')
        
        action = "updated" if is_update else "added"
        
        if success:
            messagebox.showinfo("Success", f"Asset {symbol} {action} successfully!")
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", f"Failed to {action.rstrip('d')} asset {symbol}. Please check the symbol and try again.")
            self.symbol_entry.focus()
    
    def download_error(self, error_message: str):
        """Handle download error."""
        self.hide_progress()
        self.add_button.config(state='normal')
        
        messagebox.showerror("Error", f"Error downloading asset data:\n{error_message}")
        self.symbol_entry.focus()
    
    def show_progress(self, message: str):
        """Show progress bar with message."""
        self.progress_label.config(text=message)
        self.progress_frame.grid()
        self.progress_bar.start()
    
    def hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.stop()
        self.progress_frame.grid_remove()
