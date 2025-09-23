import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from src.data_management.data_manager import DataManager
from src.projects.project_manager import graphing_project_manager


class GraphingWindow:
    """Window for creating and managing graphing projects."""
    
    def __init__(self, parent, data_manager: DataManager, project_data: Optional[Dict] = None):
        self.parent = parent
        self.data_manager = data_manager
        self.project_data = project_data
        
        # Initialize variables
        self.selected_assets = []
        self.chart_config = {
            "chart_types": ["line"],
            "include_weekends": False,
            "resolution": "daily"
        }
        self.date_config = {
            "time_range": "1y"
        }
        self.exclusions = {
            "date_ranges": [],
            "specific_dates": []
        }
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title("Graphing Project")
        self.window.geometry("1200x800")
        
        # Set up GUI first
        self.setup_gui()
        
        # Load project data if provided (after GUI is set up)
        if project_data:
            self.load_project_data(project_data)
            self.window.title(f"Graphing Project - {project_data.get('project_name', 'Untitled')}")
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Set up the graphing window GUI."""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel for controls
        left_panel = ttk.Frame(main_paned, width=350)
        main_paned.add(left_panel, weight=0)
        
        # Right panel for chart
        right_panel = ttk.Frame(main_paned)
        main_paned.add(right_panel, weight=1)
        
        self.setup_left_panel(left_panel)
        self.setup_right_panel(right_panel)
    
    def setup_left_panel(self, parent):
        """Set up the left control panel."""
        # Create scrollable frame
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure canvas scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def configure_canvas_width(event):
            # Make the canvas content width match the canvas width minus scrollbar
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_width)
        
        # Create window in canvas and store reference
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas - always-active scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        # Bind mousewheel to the entire left panel area
        def bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child)
        
        # Bind to parent, canvas, scrollable_frame and all children
        parent.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        # We'll bind to scrollable_frame and its children after they're created
        def bind_all_children():
            bind_mousewheel_recursive(scrollable_frame)
        
        # Call after all widgets are created
        parent.after(100, bind_all_children)
        
        # Asset Selection Section
        asset_frame = ttk.LabelFrame(scrollable_frame, text="Asset Selection", padding="10")
        asset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Search and add assets
        search_frame = ttk.Frame(asset_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search Assets:").pack(anchor=tk.W)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, pady=(2, 5))
        search_entry.bind('<KeyRelease>', self.filter_assets)
        
        # Available assets listbox
        ttk.Label(asset_frame, text="Available Assets:").pack(anchor=tk.W)
        
        listbox_frame = ttk.Frame(asset_frame)
        listbox_frame.pack(fill=tk.X, pady=(2, 5))
        
        self.asset_listbox = tk.Listbox(listbox_frame, height=6)
        asset_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.asset_listbox.yview)
        self.asset_listbox.configure(yscrollcommand=asset_scrollbar.set)
        
        self.asset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        asset_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate asset list
        self.populate_asset_list()
        
        # Add/Remove buttons
        button_frame = ttk.Frame(asset_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Add to Chart", command=self.add_asset_to_chart).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_asset_from_chart).pack(side=tk.LEFT)
        
        # Selected assets
        ttk.Label(asset_frame, text="Selected Assets:").pack(anchor=tk.W, pady=(10, 0))
        
        selected_frame = ttk.Frame(asset_frame)
        selected_frame.pack(fill=tk.X, pady=(2, 0))
        
        self.selected_listbox = tk.Listbox(selected_frame, height=4)
        selected_scrollbar = ttk.Scrollbar(selected_frame, orient=tk.VERTICAL, command=self.selected_listbox.yview)
        self.selected_listbox.configure(yscrollcommand=selected_scrollbar.set)
        
        self.selected_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        selected_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Chart Configuration Section
        chart_frame = ttk.LabelFrame(scrollable_frame, text="Chart Configuration", padding="10")
        chart_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Chart type selection
        ttk.Label(chart_frame, text="Chart Types:").pack(anchor=tk.W)
        
        self.chart_types = {
            "line": tk.BooleanVar(value=True),
            "bar": tk.BooleanVar(),
            "candlestick": tk.BooleanVar()
        }
        
        for chart_type, var in self.chart_types.items():
            ttk.Checkbutton(chart_frame, text=chart_type.title(), variable=var,
                           command=self.update_chart).pack(anchor=tk.W)
        
        # Percent change option
        self.percent_change_var = tk.BooleanVar()
        ttk.Checkbutton(chart_frame, text="Show as Percent Change", variable=self.percent_change_var,
                       command=self.update_chart).pack(anchor=tk.W, pady=(10, 0))
        
        # Price highlighter option
        self.price_highlighter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(chart_frame, text="Enable Price Highlighter", variable=self.price_highlighter_var,
                       command=self.toggle_price_highlighter).pack(anchor=tk.W, pady=(5, 0))
        
        # Financial quarters option
        self.show_quarters_var = tk.BooleanVar()
        ttk.Checkbutton(chart_frame, text="Show Financial Quarters", variable=self.show_quarters_var,
                       command=self.update_chart).pack(anchor=tk.W, pady=(5, 0))
        
        # Resolution selection
        ttk.Label(chart_frame, text="Resolution:").pack(anchor=tk.W, pady=(10, 0))
        
        self.resolution_var = tk.StringVar(value="daily")
        resolution_frame = ttk.Frame(chart_frame)
        resolution_frame.pack(fill=tk.X, pady=(2, 0))
        
        resolutions = [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]
        for text, value in resolutions:
            ttk.Radiobutton(resolution_frame, text=text, variable=self.resolution_var,
                           value=value, command=self.update_chart).pack(anchor=tk.W)
        
        # Include weekends
        self.include_weekends_var = tk.BooleanVar()
        ttk.Checkbutton(chart_frame, text="Include Weekends", variable=self.include_weekends_var,
                       command=self.update_chart).pack(anchor=tk.W, pady=(5, 0))
        
        # Date Range Section
        date_frame = ttk.LabelFrame(scrollable_frame, text="Date Range", padding="10")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Time range selection
        ttk.Label(date_frame, text="Time Range:").pack(anchor=tk.W)
        
        self.time_range_var = tk.StringVar(value="1y")
        time_range_combo = ttk.Combobox(date_frame, textvariable=self.time_range_var, 
                                      state="readonly", width=15)
        time_range_combo['values'] = ("1d", "1w", "1m", "1y", "5y", "all", "custom")
        time_range_combo.pack(fill=tk.X, pady=(2, 5))
        time_range_combo.bind('<<ComboboxSelected>>', self.on_time_range_change)
        
        # Custom date range (initially hidden)
        self.custom_date_frame = ttk.Frame(date_frame)
        
        ttk.Label(self.custom_date_frame, text="Start Date:").pack(anchor=tk.W)
        self.start_date_var = tk.StringVar()
        ttk.Entry(self.custom_date_frame, textvariable=self.start_date_var, width=15).pack(fill=tk.X, pady=(2, 5))
        
        ttk.Label(self.custom_date_frame, text="End Date:").pack(anchor=tk.W)
        self.end_date_var = tk.StringVar()
        ttk.Entry(self.custom_date_frame, textvariable=self.end_date_var, width=15).pack(fill=tk.X, pady=(2, 5))
        
        # Date Exclusions Section
        exclusion_frame = ttk.LabelFrame(scrollable_frame, text="Date Exclusions", padding="10")
        exclusion_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(exclusion_frame, text="Exclude outlier events:").pack(anchor=tk.W)
        
        # Exclusion list
        excl_list_frame = ttk.Frame(exclusion_frame)
        excl_list_frame.pack(fill=tk.X, pady=(2, 5))
        
        self.exclusion_listbox = tk.Listbox(excl_list_frame, height=3)
        excl_scrollbar = ttk.Scrollbar(excl_list_frame, orient=tk.VERTICAL, command=self.exclusion_listbox.yview)
        self.exclusion_listbox.configure(yscrollcommand=excl_scrollbar.set)
        
        self.exclusion_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        excl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Exclusion buttons
        excl_button_frame = ttk.Frame(exclusion_frame)
        excl_button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(excl_button_frame, text="Add Date", command=self.add_date_exclusion).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(excl_button_frame, text="Add Range", command=self.add_range_exclusion).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(excl_button_frame, text="Remove", command=self.remove_exclusion).pack(side=tk.LEFT)
        
        # Control Buttons Section
        control_frame = ttk.LabelFrame(scrollable_frame, text="Controls", padding="10")
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Update Chart", command=self.update_chart).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Save Project", command=self.save_project).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Save Project As...", command=self.save_project_as).pack(fill=tk.X, pady=2)
        ttk.Button(control_frame, text="Export Chart", command=self.export_chart).pack(fill=tk.X, pady=2)
    
    def setup_right_panel(self, parent):
        """Set up the right panel with the chart."""
        # Create matplotlib figure
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.tight_layout()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add toolbar
        toolbar = NavigationToolbar2Tk(self.canvas, parent)
        toolbar.update()
        
        # Initialize crosshair variables
        self.crosshair_v = None
        self.price_info_text = None  # Text box in corner for price info
        self.mouse_move_connected = False
        self.last_mouse_time = 0  # For performance throttling
        
        # Initial empty chart
        self.ax.set_title("Select assets to display chart")
        self.ax.set_xlabel("Date")
        self.ax.set_ylabel("Price")
        self.canvas.draw()
    
    def populate_asset_list(self):
        """Populate the asset listbox with available assets."""
        self.asset_listbox.delete(0, tk.END)
        
        assets = self.data_manager.get_asset_list()
        self.all_assets = assets
        
        for symbol, asset_type in assets:
            display_text = f"{symbol} ({asset_type})"
            self.asset_listbox.insert(tk.END, display_text)
    
    def filter_assets(self, event=None):
        """Filter assets based on search term."""
        search_term = self.search_var.get().lower()
        
        self.asset_listbox.delete(0, tk.END)
        
        for symbol, asset_type in self.all_assets:
            if search_term in symbol.lower() or search_term in asset_type.lower():
                display_text = f"{symbol} ({asset_type})"
                self.asset_listbox.insert(tk.END, display_text)
    
    def add_asset_to_chart(self):
        """Add selected asset to chart."""
        selection = self.asset_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an asset to add.")
            return
        
        index = selection[0]
        
        # Get the actual asset from filtered list
        filtered_assets = []
        search_term = self.search_var.get().lower()
        
        for symbol, asset_type in self.all_assets:
            if search_term in symbol.lower() or search_term in asset_type.lower():
                filtered_assets.append((symbol, asset_type))
        
        if index >= len(filtered_assets):
            return
        
        symbol, asset_type = filtered_assets[index]
        
        # Check if already selected
        for selected_symbol, selected_type in self.selected_assets:
            if selected_symbol == symbol and selected_type == asset_type:
                messagebox.showinfo("Already Selected", f"{symbol} is already in the chart.")
                return
        
        # Add to selected list
        self.selected_assets.append((symbol, asset_type))
        self.update_selected_listbox()
        self.update_chart()
    
    def remove_asset_from_chart(self):
        """Remove selected asset from chart."""
        selection = self.selected_listbox.curselection()
        print(f"Debug: Selection = {selection}")  # Debug info
        print(f"Debug: Selected assets = {self.selected_assets}")  # Debug info
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select an asset to remove from the Selected Assets list.")
            return
        
        index = selection[0]
        print(f"Debug: Selected index = {index}")  # Debug info
        
        if index < len(self.selected_assets):
            removed_asset = self.selected_assets.pop(index)
            print(f"Debug: Removed asset = {removed_asset}")  # Debug info
            self.update_selected_listbox()
            self.update_chart()
            messagebox.showinfo("Asset Removed", f"Removed {removed_asset[0]} from chart")
        else:
            print(f"Debug: Index {index} out of range for {len(self.selected_assets)} assets")
            messagebox.showerror("Error", "Invalid selection index")
    
    def update_selected_listbox(self):
        """Update the selected assets listbox."""
        self.selected_listbox.delete(0, tk.END)
        
        for symbol, asset_type in self.selected_assets:
            display_text = f"{symbol} ({asset_type})"
            self.selected_listbox.insert(tk.END, display_text)
        
        print(f"Debug: Updated selected listbox with {len(self.selected_assets)} assets")  # Debug info
    
    def on_time_range_change(self, event=None):
        """Handle time range selection change."""
        if self.time_range_var.get() == "custom":
            self.custom_date_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.custom_date_frame.pack_forget()
        
        self.update_chart()
    
    def update_chart(self):
        """Update the chart display."""
        if not self.selected_assets:
            self.ax.clear()
            self.ax.set_title("Select assets to display chart")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price")
            self.canvas.draw()
            return
        
        try:
            self.ax.clear()
            
            # Clear previous crosshair elements
            self.crosshair_v = None
            self.price_info_text = None
            
            # Get selected chart types
            selected_chart_types = [chart_type for chart_type, var in self.chart_types.items() if var.get()]
            
            if not selected_chart_types:
                selected_chart_types = ["line"]  # Default to line if none selected
            
            # Store processed data for crosshair functionality
            self.chart_data = {}
            
            # Determine if showing percent change
            show_percent_change = self.percent_change_var.get()
            
            # Plot each asset
            for symbol, asset_type in self.selected_assets:
                asset_data = self.data_manager.load_asset_data(symbol, asset_type)
                if not asset_data:
                    continue
                
                # Convert data to DataFrame
                df = pd.DataFrame(asset_data['historical_data'])
                df['date'] = pd.to_datetime(df['date'], utc=True)
                df.set_index('date', inplace=True)
                
                # Convert to local timezone and remove timezone info for plotting
                df.index = df.index.tz_convert(None)
                
                # Apply date filtering
                df = self.apply_date_filters(df)
                
                if df.empty:
                    continue
                
                # Apply resolution
                df = self.apply_resolution(df)
                
                # Calculate percent change if requested
                if show_percent_change:
                    # Calculate percent change from first value
                    first_price = df['close'].iloc[0]
                    df_plot = df.copy()
                    for col in ['open', 'high', 'low', 'close']:
                        df_plot[col] = ((df[col] - first_price) / first_price) * 100
                else:
                    df_plot = df
                
                # Store data for crosshair
                self.chart_data[symbol] = {
                    'data': df_plot,
                    'original_data': df,
                    'asset_type': asset_type,
                    'show_percent': show_percent_change
                }
                
                # Plot based on selected chart types
                if "line" in selected_chart_types:
                    line, = self.ax.plot(df_plot.index, df_plot['close'], 
                                        label=f"{symbol} (Line)", alpha=0.8, linewidth=2)
                    # Store line reference for crosshair
                    self.chart_data[symbol]['line'] = line
                
                if "bar" in selected_chart_types:
                    self.ax.bar(df_plot.index, df_plot['close'], alpha=0.6, 
                               label=f"{symbol} (Bar)", width=1)
                
                # Note: Candlestick charts would require mplfinance library for proper implementation
                if "candlestick" in selected_chart_types:
                    # Simple OHLC representation
                    for i, (date, row) in enumerate(df_plot.iterrows()):
                        color = 'green' if row['close'] >= row['open'] else 'red'
                        self.ax.plot([date, date], [row['low'], row['high']], color=color, alpha=0.6)
            
            # Set chart title and labels
            if show_percent_change:
                self.ax.set_title("Asset Performance (Percent Change)")
                self.ax.set_ylabel("Percent Change (%)")
                # Add a horizontal line at 0%
                self.ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            else:
                self.ax.set_title("Asset Price Chart")
                self.ax.set_ylabel("Price ($)")
            
            self.ax.set_xlabel("Date")
            self.ax.legend()
            self.ax.grid(True, alpha=0.3)
            
            # Add financial quarters if enabled
            if self.show_quarters_var.get():
                self.add_financial_quarters()
            
            # Rotate x-axis labels for better readability
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.fig.tight_layout()
            
            # Enable price highlighter if option is checked
            self.toggle_price_highlighter()
            
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Chart Error", f"Error updating chart: {str(e)}")
    
    def add_financial_quarters(self):
        """Add vertical lines and labels for financial quarters."""
        if not self.chart_data:
            return
        
        # Get the date range from the chart data
        all_dates = []
        for data_info in self.chart_data.values():
            if not data_info['data'].empty:
                all_dates.extend(data_info['data'].index.tolist())
        
        if not all_dates:
            return
        
        start_date = min(all_dates)
        end_date = max(all_dates)
        
        # Generate quarter dates
        quarter_dates = self.generate_quarter_dates(start_date, end_date)
        
        # Add vertical lines for quarters
        for date, quarter_label in quarter_dates:
            self.ax.axvline(date, color='purple', linestyle=':', alpha=0.7, linewidth=1.5)
            
            # Add quarter label at the top of the chart
            y_max = self.ax.get_ylim()[1]
            self.ax.text(date, y_max * 0.95, quarter_label, 
                        rotation=90, verticalalignment='top', 
                        fontsize=9, color='purple', alpha=0.8)
    
    def generate_quarter_dates(self, start_date, end_date):
        """Generate financial quarter dates within the given range."""
        quarters = []
        
        # Start from the first quarter that includes or comes after start_date
        year = start_date.year
        
        # Quarter end dates (standard calendar quarters)
        quarter_ends = {
            1: (3, 31),   # Q1 ends March 31
            2: (6, 30),   # Q2 ends June 30
            3: (9, 30),   # Q3 ends September 30
            4: (12, 31)   # Q4 ends December 31
        }
        
        # Generate quarters from start year to end year + 1
        for y in range(year, end_date.year + 2):
            for q in range(1, 5):
                month, day = quarter_ends[q]
                quarter_date = pd.Timestamp(year=y, month=month, day=day)
                
                # Only include quarters within our date range
                if start_date <= quarter_date <= end_date:
                    quarter_label = f"Q{q} {y}"
                    quarters.append((quarter_date, quarter_label))
        
        return quarters
    
    def toggle_price_highlighter(self):
        """Toggle the price highlighter on/off."""
        if self.price_highlighter_var.get() and self.selected_assets:
            self.enable_price_highlighter()
        else:
            self.disable_price_highlighter()
    
    def enable_price_highlighter(self):
        """Enable the mouse-following price highlighter."""
        if not self.mouse_move_connected:
            self.mouse_move_cid = self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            self.mouse_move_connected = True
    
    def disable_price_highlighter(self):
        """Disable the price highlighter."""
        if self.mouse_move_connected:
            self.canvas.mpl_disconnect(self.mouse_move_cid)
            self.mouse_move_connected = False
            # Clear existing crosshair
            if self.crosshair_v:
                self.crosshair_v.remove()
                self.crosshair_v = None
            if self.price_info_text:
                self.price_info_text.remove()
                self.price_info_text = None
            self.canvas.draw()
    
    def on_mouse_move(self, event):
        """Handle mouse movement for price highlighter."""
        if event.inaxes != self.ax or not self.chart_data:
            return
        
        # Performance throttling - only update every 50ms
        import time
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - self.last_mouse_time < 50:
            return
        self.last_mouse_time = current_time
        
        try:
            # Clear previous crosshair and info
            if self.crosshair_v:
                self.crosshair_v.remove()
            if self.price_info_text:
                self.price_info_text.remove()
            
            # Get mouse x position (date)
            mouse_date = pd.to_datetime(event.xdata, origin='unix', unit='D')
            
            # Draw vertical crosshair line
            self.crosshair_v = self.ax.axvline(event.xdata, color='red', alpha=0.7, linestyle='--')
            
            # Collect price information for all assets
            price_info_lines = []
            
            for symbol, data_info in self.chart_data.items():
                df = data_info['data']
                if df.empty:
                    continue
                
                # Find closest date
                closest_idx = df.index.get_indexer([mouse_date], method='nearest')[0]
                if 0 <= closest_idx < len(df):
                    closest_date = df.index[closest_idx]
                    closest_price = df['close'].iloc[closest_idx]
                    
                    # Format date string
                    date_str = closest_date.strftime('%Y-%m-%d')
                    
                    # Get original price for display
                    if data_info['show_percent']:
                        original_price = data_info['original_data']['close'].iloc[closest_idx]
                        price_line = f"{symbol}: {closest_price:.2f}% (${original_price:.2f})"
                    else:
                        price_line = f"{symbol}: ${closest_price:.2f}"
                    
                    price_info_lines.append(price_line)
            
            # Create info box in top-right corner
            if price_info_lines:
                # Add date at the top
                info_text = f"Date: {closest_date.strftime('%Y-%m-%d')}\n" + "\n".join(price_info_lines)
                
                # Position in top-right corner
                self.price_info_text = self.ax.text(
                    0.98, 0.98, info_text,
                    transform=self.ax.transAxes,
                    fontsize=10,
                    verticalalignment='top',
                    horizontalalignment='right',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9, edgecolor='black'),
                    family='monospace'  # Monospace font for better alignment
                )
            
            # Redraw canvas (less frequently for performance)
            self.canvas.draw_idle()  # Use draw_idle() instead of draw() for better performance
            
        except Exception as e:
            # Silently handle errors to avoid disrupting mouse movement
            pass
    
    def adjust_annotation_positions(self):
        """This method is no longer needed with corner display."""
        pass
    
    def apply_date_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply date range and exclusion filters to DataFrame."""
        # Apply time range filter
        time_range = self.time_range_var.get()
        end_date = pd.Timestamp.now().tz_localize(None)  # Make timezone-naive
        
        if time_range == "custom":
            try:
                start_str = self.start_date_var.get()
                end_str = self.end_date_var.get()
                if start_str:
                    start_date = pd.to_datetime(start_str).tz_localize(None)
                    df = df[df.index >= start_date]
                if end_str:
                    end_date = pd.to_datetime(end_str).tz_localize(None)
                    df = df[df.index <= end_date]
            except (ValueError, TypeError):
                pass  # Invalid date format, skip custom filtering
        elif time_range != "all":
            if time_range == "1d":
                start_date = end_date - pd.Timedelta(days=1)
            elif time_range == "1w":
                start_date = end_date - pd.Timedelta(weeks=1)
            elif time_range == "1m":
                start_date = end_date - pd.Timedelta(days=30)
            elif time_range == "1y":
                start_date = end_date - pd.Timedelta(days=365)
            elif time_range == "5y":
                start_date = end_date - pd.Timedelta(days=1825)
            else:
                start_date = df.index.min()
            
            df = df[df.index >= start_date]
        
        # Apply exclusions
        for exclusion in self.exclusions.get("specific_dates", []):
            try:
                exclude_date = pd.to_datetime(exclusion["date"]).tz_localize(None)
                df = df[df.index.date != exclude_date.date()]
            except (ValueError, TypeError):
                continue
        
        for exclusion in self.exclusions.get("date_ranges", []):
            try:
                start_excl = pd.to_datetime(exclusion["start"]).tz_localize(None)
                end_excl = pd.to_datetime(exclusion["end"]).tz_localize(None)
                df = df[~((df.index >= start_excl) & (df.index <= end_excl))]
            except (ValueError, TypeError):
                continue
        
        # Filter weekends if option is disabled
        if not self.include_weekends_var.get():
            df = df[df.index.dayofweek < 5]  # Monday=0, Sunday=6
        
        return df
    
    def apply_resolution(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply resolution (daily, weekly, monthly) to DataFrame."""
        resolution = self.resolution_var.get()
        
        if resolution == "weekly":
            df = df.resample('W').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif resolution == "monthly":
            df = df.resample('M').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        
        return df
    
    def add_date_exclusion(self):
        """Add a specific date exclusion."""
        date_str = simpledialog.askstring("Add Date Exclusion", "Enter date to exclude (YYYY-MM-DD):")
        if not date_str:
            return
        
        try:
            # Validate date format and make timezone-naive
            pd.to_datetime(date_str).tz_localize(None)
            reason = simpledialog.askstring("Exclusion Reason", "Enter reason for exclusion (optional):") or "User defined"
            
            exclusion = {"date": date_str, "reason": reason}
            self.exclusions["specific_dates"].append(exclusion)
            
            self.update_exclusion_listbox()
            self.update_chart()
            
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
    
    def add_range_exclusion(self):
        """Add a date range exclusion."""
        start_date = simpledialog.askstring("Add Range Exclusion", "Enter start date (YYYY-MM-DD):")
        if not start_date:
            return
        
        end_date = simpledialog.askstring("Add Range Exclusion", "Enter end date (YYYY-MM-DD):")
        if not end_date:
            return
        
        try:
            # Validate date formats and make timezone-naive
            pd.to_datetime(start_date).tz_localize(None)
            pd.to_datetime(end_date).tz_localize(None)
            
            reason = simpledialog.askstring("Exclusion Reason", "Enter reason for exclusion (optional):") or "User defined"
            
            exclusion = {"start": start_date, "end": end_date, "reason": reason}
            self.exclusions["date_ranges"].append(exclusion)
            
            self.update_exclusion_listbox()
            self.update_chart()
            
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Date", "Please enter valid dates in YYYY-MM-DD format.")
    
    def remove_exclusion(self):
        """Remove selected exclusion."""
        selection = self.exclusion_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an exclusion to remove.")
            return
        
        index = selection[0]
        
        # Calculate which exclusion to remove
        specific_dates_count = len(self.exclusions["specific_dates"])
        
        if index < specific_dates_count:
            self.exclusions["specific_dates"].pop(index)
        else:
            range_index = index - specific_dates_count
            if range_index < len(self.exclusions["date_ranges"]):
                self.exclusions["date_ranges"].pop(range_index)
        
        self.update_exclusion_listbox()
        self.update_chart()
    
    def update_exclusion_listbox(self):
        """Update the exclusion listbox."""
        self.exclusion_listbox.delete(0, tk.END)
        
        # Add specific dates
        for exclusion in self.exclusions["specific_dates"]:
            display_text = f"Date: {exclusion['date']} - {exclusion['reason']}"
            self.exclusion_listbox.insert(tk.END, display_text)
        
        # Add date ranges
        for exclusion in self.exclusions["date_ranges"]:
            display_text = f"Range: {exclusion['start']} to {exclusion['end']} - {exclusion['reason']}"
            self.exclusion_listbox.insert(tk.END, display_text)
    
    def save_project(self):
        """Save the current project."""
        if self.project_data and self.project_data.get("project_name"):
            project_name = self.project_data["project_name"]
        else:
            project_name = simpledialog.askstring("Save Project", "Enter project name:")
            if not project_name:
                return
        
        self.save_project_with_name(project_name)
    
    def save_project_as(self):
        """Save the current project with a new name."""
        project_name = simpledialog.askstring("Save Project As", "Enter project name:")
        if not project_name:
            return
        
        self.save_project_with_name(project_name)
    
    def save_project_with_name(self, project_name: str):
        """Save project with specified name."""
        try:
            # Prepare asset data
            assets_data = []
            for symbol, asset_type in self.selected_assets:
                assets_data.append({"symbol": symbol, "asset_type": asset_type})
            
            # Prepare chart config
            chart_config = {
                "chart_types": [chart_type for chart_type, var in self.chart_types.items() if var.get()],
                "include_weekends": self.include_weekends_var.get(),
                "resolution": self.resolution_var.get(),
                "show_percent_change": self.percent_change_var.get(),
                "enable_price_highlighter": self.price_highlighter_var.get(),
                "show_quarters": self.show_quarters_var.get()
            }
            
            # Prepare date config
            date_config = {
                "time_range": self.time_range_var.get(),
                "custom_start": self.start_date_var.get() if self.time_range_var.get() == "custom" else None,
                "custom_end": self.end_date_var.get() if self.time_range_var.get() == "custom" else None
            }
            
            # Create project
            project_data = graphing_project_manager.create_graphing_project(
                project_name, assets_data, chart_config, date_config, self.exclusions
            )
            
            # Save project
            if graphing_project_manager.save_project(project_data, project_name):
                self.project_data = project_data
                self.window.title(f"Graphing Project - {project_name}")
                messagebox.showinfo("Success", f"Project '{project_name}' saved successfully!")
            else:
                messagebox.showerror("Error", "Failed to save project.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error saving project: {str(e)}")
    
    def export_chart(self):
        """Export chart as image."""
        if not self.selected_assets:
            messagebox.showwarning("No Data", "No assets selected to export.")
            return
        
        from tkinter import filedialog
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.fig.savefig(filename, dpi=300, bbox_inches='tight')
                messagebox.showinfo("Success", f"Chart exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export chart: {str(e)}")
    
    def load_project_data(self, project_data: Dict):
        """Load project data into the interface."""
        self.project_data = project_data
        config = project_data.get("config", {})
        
        # Load assets
        assets = config.get("assets", [])
        for asset in assets:
            self.selected_assets.append((asset["symbol"], asset["asset_type"]))
        
        # Update the selected assets listbox after loading
        self.update_selected_listbox()
        
        # Load chart config
        chart_config = config.get("chart_config", {})
        chart_types = chart_config.get("chart_types", ["line"])
        
        # Reset all chart types first
        for var in self.chart_types.values():
            var.set(False)
        
        # Set selected chart types
        for chart_type in chart_types:
            if chart_type in self.chart_types:
                self.chart_types[chart_type].set(True)
        
        # Load other configurations
        if hasattr(self, 'include_weekends_var'):
            self.include_weekends_var.set(chart_config.get("include_weekends", False))
        if hasattr(self, 'resolution_var'):
            self.resolution_var.set(chart_config.get("resolution", "daily"))
        if hasattr(self, 'percent_change_var'):
            self.percent_change_var.set(chart_config.get("show_percent_change", False))
        if hasattr(self, 'price_highlighter_var'):
            self.price_highlighter_var.set(chart_config.get("enable_price_highlighter", True))
        if hasattr(self, 'show_quarters_var'):
            self.show_quarters_var.set(chart_config.get("show_quarters", False))
        
        # Load date config
        date_config = config.get("date_config", {})
        if hasattr(self, 'time_range_var'):
            self.time_range_var.set(date_config.get("time_range", "1y"))
        
        # Load custom dates if applicable
        if date_config.get("time_range") == "custom":
            if hasattr(self, 'start_date_var') and date_config.get("custom_start"):
                self.start_date_var.set(date_config.get("custom_start"))
            if hasattr(self, 'end_date_var') and date_config.get("custom_end"):
                self.end_date_var.set(date_config.get("custom_end"))
        
        # Load exclusions
        self.exclusions = config.get("exclusions", {"date_ranges": [], "specific_dates": []})
        self.update_exclusion_listbox()
        
        # Update the chart with loaded data
        self.update_chart()
    
    def on_closing(self):
        """Handle window closing."""
        if self.selected_assets or (self.project_data and self.project_data.get("project_name")):
            result = messagebox.askyesnocancel("Save Project", "Do you want to save the project before closing?")
            
            if result is True:  # Yes, save
                self.save_project()
                self.cleanup_and_close()
            elif result is False:  # No, don't save
                self.cleanup_and_close()
            # Cancel - do nothing
        else:
            self.cleanup_and_close()
    
    def cleanup_and_close(self):
        """Clean up matplotlib and close window."""
        try:
            # Clear the matplotlib figure
            self.fig.clear()
            plt.close(self.fig)
            
            # Destroy the window
            self.window.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Force close if there's an error
            try:
                self.window.destroy()
            except:
                pass
        """Handle window closing."""
        if self.selected_assets or (self.project_data and self.project_data.get("project_name")):
            result = messagebox.askyesnocancel("Save Project", "Do you want to save the project before closing?")
            
            if result is True:  # Yes, save
                self.save_project()
                self.cleanup_and_close()
            elif result is False:  # No, don't save
                self.cleanup_and_close()
            # Cancel - do nothing
        else:
            self.cleanup_and_close()
    
    def cleanup_and_close(self):
        """Clean up matplotlib and close window."""
        try:
            # Clear the matplotlib figure
            self.fig.clear()
            plt.close(self.fig)
            
            # Destroy the window
            self.window.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Force close if there's an error
            try:
                self.window.destroy()
            except:
                pass
