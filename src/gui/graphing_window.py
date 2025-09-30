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
        
        # Track if changes have been made
        self.has_unsaved_changes = False
        self.initial_config_hash = None
        
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
            # Mark as no changes after loading
            self.has_unsaved_changes = False
            self.initial_config_hash = self._get_config_hash()
        else:
            # New project starts with changes
            self.has_unsaved_changes = True
            self.initial_config_hash = self._get_config_hash()
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _get_config_hash(self) -> str:
        """Get a hash of the current configuration for change detection."""
        import hashlib
        import json
        
        config = {
            'assets': [(s, t) for s, t in self.selected_assets],
            'chart_types': [ct for ct, var in self.chart_types.items() if var.get()],
            'percent_change': self.percent_change_var.get(),
            'price_highlighter': self.price_highlighter_var.get(),
            'show_quarters': self.show_quarters_var.get(),
            'resolution': self.resolution_var.get(),
            'include_weekends': self.include_weekends_var.get(),
            'time_range': self.time_range_var.get(),
            'custom_start': self.start_date_var.get() if self.time_range_var.get() == "custom" else None,
            'custom_end': self.end_date_var.get() if self.time_range_var.get() == "custom" else None,
            'exclusions': {
                'date_ranges': self.exclusions.get("date_ranges", []),
                'specific_dates': self.exclusions.get("specific_dates", [])
            }
        }
        
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def _mark_changes(self):
        """Mark that changes have been made to the configuration."""
        current_hash = self._get_config_hash()
        self.has_unsaved_changes = (current_hash != self.initial_config_hash)
        
        # Update window title to show unsaved changes
        title = self.window.title()
        if self.has_unsaved_changes and not title.endswith('*'):
            self.window.title(title + '*')
        elif not self.has_unsaved_changes and title.endswith('*'):
            self.window.title(title[:-1])
    
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
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", configure_scroll_region)
        canvas.bind("<Configure>", configure_canvas_width)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def bind_mousewheel_recursive(widget):
            widget.bind("<MouseWheel>", _on_mousewheel)
            widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
            for child in widget.winfo_children():
                bind_mousewheel_recursive(child)
        
        parent.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<MouseWheel>", _on_mousewheel)
        canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
        
        def bind_all_children():
            bind_mousewheel_recursive(scrollable_frame)
        
        parent.after(100, bind_all_children)
        
        # Asset Selection Section
        asset_frame = ttk.LabelFrame(scrollable_frame, text="Asset Selection", padding="10")
        asset_frame.pack(fill=tk.X, padx=5, pady=5)
        
        search_frame = ttk.Frame(asset_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search Assets:").pack(anchor=tk.W)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, pady=(2, 5))
        search_entry.bind('<KeyRelease>', self.filter_assets)
        
        ttk.Label(asset_frame, text="Available Assets:").pack(anchor=tk.W)
        
        listbox_frame = ttk.Frame(asset_frame)
        listbox_frame.pack(fill=tk.X, pady=(2, 5))
        
        self.asset_listbox = tk.Listbox(listbox_frame, height=6)
        asset_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.asset_listbox.yview)
        self.asset_listbox.configure(yscrollcommand=asset_scrollbar.set)
        
        self.asset_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        asset_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.populate_asset_list()
        
        button_frame = ttk.Frame(asset_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Add to Chart", command=self.add_asset_to_chart).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_asset_from_chart).pack(side=tk.LEFT)
        
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
        
        ttk.Label(chart_frame, text="Chart Types:").pack(anchor=tk.W)
        
        self.chart_types = {
            "line": tk.BooleanVar(value=True),
            "bar": tk.BooleanVar(),
            "candlestick": tk.BooleanVar()
        }
        
        for chart_type, var in self.chart_types.items():
            var.trace_add('write', lambda *args: self._mark_changes())
            ttk.Checkbutton(chart_frame, text=chart_type.title(), variable=var,
                           command=self.update_chart).pack(anchor=tk.W)
        
        self.percent_change_var = tk.BooleanVar()
        self.percent_change_var.trace_add('write', lambda *args: self._mark_changes())
        ttk.Checkbutton(chart_frame, text="Show as Percent Change", variable=self.percent_change_var,
                       command=self.update_chart).pack(anchor=tk.W, pady=(10, 0))
        
        self.price_highlighter_var = tk.BooleanVar(value=True)
        self.price_highlighter_var.trace_add('write', lambda *args: self._mark_changes())
        ttk.Checkbutton(chart_frame, text="Enable Price Highlighter", variable=self.price_highlighter_var,
                       command=self.toggle_price_highlighter).pack(anchor=tk.W, pady=(5, 0))
        
        self.show_quarters_var = tk.BooleanVar()
        self.show_quarters_var.trace_add('write', lambda *args: self._mark_changes())
        ttk.Checkbutton(chart_frame, text="Show Financial Quarters", variable=self.show_quarters_var,
                       command=self.update_chart).pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Label(chart_frame, text="Resolution:").pack(anchor=tk.W, pady=(10, 0))
        
        self.resolution_var = tk.StringVar(value="daily")
        self.resolution_var.trace_add('write', lambda *args: self._mark_changes())
        resolution_frame = ttk.Frame(chart_frame)
        resolution_frame.pack(fill=tk.X, pady=(2, 0))
        
        resolutions = [("Daily", "daily"), ("Weekly", "weekly"), ("Monthly", "monthly")]
        for text, value in resolutions:
            ttk.Radiobutton(resolution_frame, text=text, variable=self.resolution_var,
                           value=value, command=self.update_chart).pack(anchor=tk.W)
        
        self.include_weekends_var = tk.BooleanVar()
        self.include_weekends_var.trace_add('write', lambda *args: self._mark_changes())
        ttk.Checkbutton(chart_frame, text="Include Weekends", variable=self.include_weekends_var,
                       command=self.update_chart).pack(anchor=tk.W, pady=(5, 0))
        
        # Date Range Section
        date_frame = ttk.LabelFrame(scrollable_frame, text="Date Range", padding="10")
        date_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(date_frame, text="Time Range:").pack(anchor=tk.W)
        
        self.time_range_var = tk.StringVar(value="1y")
        self.time_range_var.trace_add('write', lambda *args: self._mark_changes())
        time_range_combo = ttk.Combobox(date_frame, textvariable=self.time_range_var, 
                                      state="readonly", width=15)
        time_range_combo['values'] = ("1d", "1w", "1m", "1y", "5y", "all", "custom")
        time_range_combo.pack(fill=tk.X, pady=(2, 5))
        time_range_combo.bind('<<ComboboxSelected>>', self.on_time_range_change)
        
        self.custom_date_frame = ttk.Frame(date_frame)
        
        ttk.Label(self.custom_date_frame, text="Start Date:").pack(anchor=tk.W)
        self.start_date_var = tk.StringVar()
        self.start_date_var.trace_add('write', lambda *args: self._mark_changes())
        ttk.Entry(self.custom_date_frame, textvariable=self.start_date_var, width=15).pack(fill=tk.X, pady=(2, 5))
        
        ttk.Label(self.custom_date_frame, text="End Date:").pack(anchor=tk.W)
        self.end_date_var = tk.StringVar()
        self.end_date_var.trace_add('write', lambda *args: self._mark_changes())
        ttk.Entry(self.custom_date_frame, textvariable=self.end_date_var, width=15).pack(fill=tk.X, pady=(2, 5))
        
        # Date Exclusions Section
        exclusion_frame = ttk.LabelFrame(scrollable_frame, text="Date Exclusions", padding="10")
        exclusion_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(exclusion_frame, text="Exclude outlier events:").pack(anchor=tk.W)
        
        excl_list_frame = ttk.Frame(exclusion_frame)
        excl_list_frame.pack(fill=tk.X, pady=(2, 5))
        
        self.exclusion_listbox = tk.Listbox(excl_list_frame, height=3)
        excl_scrollbar = ttk.Scrollbar(excl_list_frame, orient=tk.VERTICAL, command=self.exclusion_listbox.yview)
        self.exclusion_listbox.configure(yscrollcommand=excl_scrollbar.set)
        
        self.exclusion_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        excl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
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
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        toolbar = NavigationToolbar2Tk(self.canvas, parent)
        toolbar.update()
        
        self.crosshair_v = None
        self.price_info_text = None
        self.mouse_move_connected = False
        self.last_mouse_time = 0
        
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
        
        filtered_assets = []
        search_term = self.search_var.get().lower()
        
        for symbol, asset_type in self.all_assets:
            if search_term in symbol.lower() or search_term in asset_type.lower():
                filtered_assets.append((symbol, asset_type))
        
        if index >= len(filtered_assets):
            return
        
        symbol, asset_type = filtered_assets[index]
        
        for selected_symbol, selected_type in self.selected_assets:
            if selected_symbol == symbol and selected_type == asset_type:
                messagebox.showinfo("Already Selected", f"{symbol} is already in the chart.")
                return
        
        self.selected_assets.append((symbol, asset_type))
        self.update_selected_listbox()
        self._mark_changes()
        self.update_chart()
    
    def remove_asset_from_chart(self):
        """Remove selected asset from chart."""
        selection = self.selected_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("No Selection", "Please select an asset to remove from the Selected Assets list.")
            return
        
        index = selection[0]
        
        if index < len(self.selected_assets):
            removed_asset = self.selected_assets.pop(index)
            self.update_selected_listbox()
            self._mark_changes()
            self.update_chart()
            messagebox.showinfo("Asset Removed", f"Removed {removed_asset[0]} from chart")
        else:
            messagebox.showerror("Error", "Invalid selection index")
    
    def update_selected_listbox(self):
        """Update the selected assets listbox."""
        self.selected_listbox.delete(0, tk.END)
        
        for symbol, asset_type in self.selected_assets:
            display_text = f"{symbol} ({asset_type})"
            self.selected_listbox.insert(tk.END, display_text)
    
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
            
            self.crosshair_v = None
            self.price_info_text = None
            
            selected_chart_types = [chart_type for chart_type, var in self.chart_types.items() if var.get()]
            
            if not selected_chart_types:
                selected_chart_types = ["line"]
            
            self.chart_data = {}
            
            show_percent_change = self.percent_change_var.get()
            
            for symbol, asset_type in self.selected_assets:
                asset_data = self.data_manager.load_asset_data(symbol, asset_type)
                if not asset_data:
                    continue
                
                df = pd.DataFrame(asset_data['historical_data'])
                df['date'] = pd.to_datetime(df['date'], utc=True)
                df.set_index('date', inplace=True)
                
                df.index = df.index.tz_convert(None)
                
                df = self.apply_date_filters(df)
                
                if df.empty:
                    continue
                
                df = self.apply_resolution(df)
                
                if show_percent_change:
                    first_price = df['close'].iloc[0]
                    df_plot = df.copy()
                    for col in ['open', 'high', 'low', 'close']:
                        df_plot[col] = ((df[col] - first_price) / first_price) * 100
                else:
                    df_plot = df
                
                self.chart_data[symbol] = {
                    'data': df_plot,
                    'original_data': df,
                    'asset_type': asset_type,
                    'show_percent': show_percent_change
                }
                
                if "line" in selected_chart_types:
                    line, = self.ax.plot(df_plot.index, df_plot['close'], 
                                        label=f"{symbol} (Line)", alpha=0.8, linewidth=2)
                    self.chart_data[symbol]['line'] = line
                
                if "bar" in selected_chart_types:
                    self.ax.bar(df_plot.index, df_plot['close'], alpha=0.6, 
                               label=f"{symbol} (Bar)", width=1)
                
                if "candlestick" in selected_chart_types:
                    for i, (date, row) in enumerate(df_plot.iterrows()):
                        color = 'green' if row['close'] >= row['open'] else 'red'
                        self.ax.plot([date, date], [row['low'], row['high']], color=color, alpha=0.6)
            
            if show_percent_change:
                self.ax.set_title("Asset Performance (Percent Change)")
                self.ax.set_ylabel("Percent Change (%)")
                self.ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            else:
                self.ax.set_title("Asset Price Chart")
                self.ax.set_ylabel("Price ($)")
            
            self.ax.set_xlabel("Date")
            self.ax.legend()
            self.ax.grid(True, alpha=0.3)
            
            if self.show_quarters_var.get():
                self.add_financial_quarters()
            
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
            
            self.fig.tight_layout()
            
            self.toggle_price_highlighter()
            
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("Chart Error", f"Error updating chart: {str(e)}")
    
    def add_financial_quarters(self):
        """Add vertical lines and labels for financial quarters."""
        if not self.chart_data:
            return
        
        all_dates = []
        for data_info in self.chart_data.values():
            if not data_info['data'].empty:
                all_dates.extend(data_info['data'].index.tolist())
        
        if not all_dates:
            return
        
        start_date = min(all_dates)
        end_date = max(all_dates)
        
        quarter_dates = self.generate_quarter_dates(start_date, end_date)
        
        for date, quarter_label in quarter_dates:
            self.ax.axvline(date, color='purple', linestyle=':', alpha=0.7, linewidth=1.5)
            
            y_max = self.ax.get_ylim()[1]
            self.ax.text(date, y_max * 0.95, quarter_label, 
                        rotation=90, verticalalignment='top', 
                        fontsize=9, color='purple', alpha=0.8)
    
    def generate_quarter_dates(self, start_date, end_date):
        """Generate financial quarter dates within the given range."""
        quarters = []
        
        year = start_date.year
        
        quarter_ends = {
            1: (3, 31),
            2: (6, 30),
            3: (9, 30),
            4: (12, 31)
        }
        
        for y in range(year, end_date.year + 2):
            for q in range(1, 5):
                month, day = quarter_ends[q]
                quarter_date = pd.Timestamp(year=y, month=month, day=day)
                
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
        
        import time
        current_time = time.time() * 1000
        if current_time - self.last_mouse_time < 50:
            return
        self.last_mouse_time = current_time
        
        try:
            if self.crosshair_v:
                self.crosshair_v.remove()
            if self.price_info_text:
                self.price_info_text.remove()
            
            mouse_date = pd.to_datetime(event.xdata, origin='unix', unit='D')
            
            self.crosshair_v = self.ax.axvline(event.xdata, color='red', alpha=0.7, linestyle='--')
            
            price_info_lines = []
            
            for symbol, data_info in self.chart_data.items():
                df = data_info['data']
                if df.empty:
                    continue
                
                closest_idx = df.index.get_indexer([mouse_date], method='nearest')[0]
                if 0 <= closest_idx < len(df):
                    closest_date = df.index[closest_idx]
                    closest_price = df['close'].iloc[closest_idx]
                    
                    if data_info['show_percent']:
                        original_price = data_info['original_data']['close'].iloc[closest_idx]
                        price_line = f"{symbol}: {closest_price:.2f}% (${original_price:.2f})"
                    else:
                        price_line = f"{symbol}: ${closest_price:.2f}"
                    
                    price_info_lines.append(price_line)
            
            if price_info_lines:
                info_text = f"Date: {closest_date.strftime('%Y-%m-%d')}\n" + "\n".join(price_info_lines)
                
                self.price_info_text = self.ax.text(
                    0.98, 0.98, info_text,
                    transform=self.ax.transAxes,
                    fontsize=10,
                    verticalalignment='top',
                    horizontalalignment='right',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9, edgecolor='black'),
                    family='monospace'
                )
            
            self.canvas.draw_idle()
            
        except Exception as e:
            pass
    
    def apply_date_filters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply date range and exclusion filters to DataFrame."""
        time_range = self.time_range_var.get()
        end_date = pd.Timestamp.now().tz_localize(None)
        
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
                pass
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
        
        if not self.include_weekends_var.get():
            df = df[df.index.dayofweek < 5]
        
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
            pd.to_datetime(date_str).tz_localize(None)
            reason = simpledialog.askstring("Exclusion Reason", "Enter reason for exclusion (optional):") or "User defined"
            
            exclusion = {"date": date_str, "reason": reason}
            self.exclusions["specific_dates"].append(exclusion)
            
            self.update_exclusion_listbox()
            self._mark_changes()
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
            pd.to_datetime(start_date).tz_localize(None)
            pd.to_datetime(end_date).tz_localize(None)
            
            reason = simpledialog.askstring("Exclusion Reason", "Enter reason for exclusion (optional):") or "User defined"
            
            exclusion = {"start": start_date, "end": end_date, "reason": reason}
            self.exclusions["date_ranges"].append(exclusion)
            
            self.update_exclusion_listbox()
            self._mark_changes()
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
        
        specific_dates_count = len(self.exclusions["specific_dates"])
        
        if index < specific_dates_count:
            self.exclusions["specific_dates"].pop(index)
        else:
            range_index = index - specific_dates_count
            if range_index < len(self.exclusions["date_ranges"]):
                self.exclusions["date_ranges"].pop(range_index)
        
        self.update_exclusion_listbox()
        self._mark_changes()
        self.update_chart()
    
    def update_exclusion_listbox(self):
        """Update the exclusion listbox."""
        self.exclusion_listbox.delete(0, tk.END)
        
        for exclusion in self.exclusions["specific_dates"]:
            display_text = f"Date: {exclusion['date']} - {exclusion['reason']}"
            self.exclusion_listbox.insert(tk.END, display_text)
        
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
            assets_data = []
            for symbol, asset_type in self.selected_assets:
                assets_data.append({"symbol": symbol, "asset_type": asset_type})
            
            chart_config = {
                "chart_types": [chart_type for chart_type, var in self.chart_types.items() if var.get()],
                "include_weekends": self.include_weekends_var.get(),
                "resolution": self.resolution_var.get(),
                "show_percent_change": self.percent_change_var.get(),
                "enable_price_highlighter": self.price_highlighter_var.get(),
                "show_quarters": self.show_quarters_var.get()
            }
            
            date_config = {
                "time_range": self.time_range_var.get(),
                "custom_start": self.start_date_var.get() if self.time_range_var.get() == "custom" else None,
                "custom_end": self.end_date_var.get() if self.time_range_var.get() == "custom" else None
            }
            
            project_data = graphing_project_manager.create_graphing_project(
                project_name, assets_data, chart_config, date_config, self.exclusions
            )
            
            if graphing_project_manager.save_project(project_data, project_name):
                self.project_data = project_data
                
                self.window.title(f"Graphing Project - {project_name}")
                
                self.has_unsaved_changes = False
                self.initial_config_hash = self._get_config_hash()
                
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
        
        assets = config.get("assets", [])
        for asset in assets:
            self.selected_assets.append((asset["symbol"], asset["asset_type"]))
        
        self.update_selected_listbox()
        
        chart_config = config.get("chart_config", {})
        chart_types = chart_config.get("chart_types", ["line"])
        
        for var in self.chart_types.values():
            var.set(False)
        
        for chart_type in chart_types:
            if chart_type in self.chart_types:
                self.chart_types[chart_type].set(True)
        
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
        
        date_config = config.get("date_config", {})
        if hasattr(self, 'time_range_var'):
            self.time_range_var.set(date_config.get("time_range", "1y"))
        
        if date_config.get("time_range") == "custom":
            if hasattr(self, 'start_date_var') and date_config.get("custom_start"):
                self.start_date_var.set(date_config.get("custom_start"))
            if hasattr(self, 'end_date_var') and date_config.get("custom_end"):
                self.end_date_var.set(date_config.get("custom_end"))
        
        self.exclusions = config.get("exclusions", {"date_ranges": [], "specific_dates": []})
        self.update_exclusion_listbox()
        
        self.update_chart()
    
    def on_closing(self):
        """Handle window closing."""
        if self.has_unsaved_changes:
            result = messagebox.askyesnocancel("Save Project", "Do you want to save the project before closing?")
            
            if result is True:
                self.save_project()
                self.cleanup_and_close()
            elif result is False:
                self.cleanup_and_close()
        else:
            self.cleanup_and_close()
    
    def cleanup_and_close(self):
        """Clean up matplotlib and close window."""
        try:
            self.fig.clear()
            plt.close(self.fig)
            self.window.destroy()
        except Exception as e:
            print(f"Error during cleanup: {e}")
            try:
                self.window.destroy()
            except:
                pass
