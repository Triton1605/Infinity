import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
from src.data_management.data_manager import DataManager
from utils.filepath_manager import filepath_manager


class AssetAnalysisWindow:
    """Window for detailed asset analysis including event tracking and pattern matching."""
    
    def __init__(self, parent, data_manager: DataManager, symbol: str, asset_type: str):
        self.parent = parent
        self.data_manager = data_manager
        self.symbol = symbol
        self.asset_type = asset_type
        self.is_closing = False  # Track if window is being closed
        
        # Load asset data
        self.asset_data = data_manager.load_asset_data(symbol, asset_type)
        if not self.asset_data:
            messagebox.showerror("Error", f"Could not load data for {symbol}")
            return
        
        # Initialize events
        self.events = self.load_events()
        self.selected_event = None
        
        # NEW: Initialize zoom and pan variables
        self.zoom_enabled = True
        self.pan_enabled = True
        self.is_panning = False
        self.pan_start = None
        self.zoom_scale = 1.0
        
        # NEW: Initialize crosshair variables for enhanced highlighter
        self.crosshair_v = None
        self.crosshair_h = None
        self.price_info_text = None
        self.mouse_move_connected = False
        self.last_mouse_time = 0
        self.highlighter_enabled = True
        
        # NEW: Initialize date range variables
        self.current_date_range = "all"
        self.custom_start_date = None
        self.custom_end_date = None
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Asset Analysis - {symbol}")
        self.window.geometry("1200x800")  # Reasonable default size
        
        # Initialize widgets to None to track their state
        self.tree = None
        self.events_listbox = None
        self.exclusion_ranges_listbox = None
        
        self.setup_gui()
        self.load_chart_data()
        self.update_chart()
        
        # Handle window closing - use lambda to avoid command name issues
        self.window.protocol("WM_DELETE_WINDOW", lambda: self.on_closing())
    
    def setup_gui(self):
        """Set up the analysis window GUI."""
        try:
            # Create main paned window - simple and standard
            main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
            main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Left panel for controls
            left_panel = ttk.Frame(main_paned)
            main_paned.add(left_panel)
            
            # Right panel for chart
            right_panel = ttk.Frame(main_paned)
            main_paned.add(right_panel)
            
            self.setup_left_panel(left_panel)
            self.setup_right_panel(right_panel)
        except Exception as e:
            print(f"Error setting up GUI: {e}")
            messagebox.showerror("GUI Error", f"Error setting up interface: {str(e)}")
    
    def setup_left_panel(self, parent):
        """Set up the left control panel."""
        try:
            # Create canvas and scrollbar for scrolling
            canvas = tk.Canvas(parent)
            scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            # Configure canvas scrolling
            def configure_scroll_region(event):
                if not self.is_closing:
                    canvas.configure(scrollregion=canvas.bbox("all"))
            
            def configure_canvas_width(event):
                if not self.is_closing:
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
            
            # Bind mousewheel to canvas - simpler approach for always-active scrolling
            def _on_mousewheel(event):
                if not self.is_closing:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            
            # Bind mousewheel to the entire left panel area
            def bind_mousewheel_recursive(widget):
                try:
                    widget.bind("<MouseWheel>", _on_mousewheel)
                    widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units") if not self.is_closing else None)
                    widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units") if not self.is_closing else None)
                    for child in widget.winfo_children():
                        bind_mousewheel_recursive(child)
                except tk.TclError:
                    pass  # Widget may have been destroyed
            
            # Bind to parent, canvas, scrollable_frame and all children
            parent.bind("<MouseWheel>", _on_mousewheel)
            canvas.bind("<MouseWheel>", _on_mousewheel)
            canvas.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units") if not self.is_closing else None)
            canvas.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units") if not self.is_closing else None)
            
            # We'll bind to scrollable_frame and its children after they're created
            def bind_all_children():
                if not self.is_closing:
                    bind_mousewheel_recursive(scrollable_frame)
            
            # Call after all widgets are created
            parent.after(100, bind_all_children)
            
            # Asset info section
            info_frame = ttk.LabelFrame(scrollable_frame, text="Asset Information", padding="10")
            info_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(info_frame, text=f"Symbol: {self.symbol}", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Type: {self.asset_type.title()}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Company: {self.asset_data.get('company_name', 'Unknown')}").pack(anchor=tk.W)
            ttk.Label(info_frame, text=f"Latest Price: ${self.asset_data.get('latest_price', 'N/A')}").pack(anchor=tk.W)
            
            # NEW: Chart Controls Section
            chart_controls_frame = ttk.LabelFrame(scrollable_frame, text="Chart Controls", padding="10")
            chart_controls_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Date range selection
            ttk.Label(chart_controls_frame, text="Date Range:").pack(anchor=tk.W)
            
            self.date_range_var = tk.StringVar(value="all")
            date_combo = ttk.Combobox(chart_controls_frame, textvariable=self.date_range_var, 
                                     state="readonly", width=25)
            date_combo['values'] = ("1d", "1w", "1m", "3m", "6m", "1y", "2y", "5y", "all", "custom")
            date_combo.pack(fill=tk.X, pady=(2, 5))
            date_combo.bind('<<ComboboxSelected>>', self.on_date_range_change)
            
            # Custom date range (initially hidden)
            self.custom_date_frame = ttk.Frame(chart_controls_frame)
            
            ttk.Label(self.custom_date_frame, text="Start Date (YYYY-MM-DD):").pack(anchor=tk.W)
            self.start_date_var = tk.StringVar()
            start_entry = ttk.Entry(self.custom_date_frame, textvariable=self.start_date_var)
            start_entry.pack(fill=tk.X, pady=(2, 5))
            start_entry.bind('<KeyRelease>', self.on_custom_date_change)
            
            ttk.Label(self.custom_date_frame, text="End Date (YYYY-MM-DD):").pack(anchor=tk.W)
            self.end_date_var = tk.StringVar()
            end_entry = ttk.Entry(self.custom_date_frame, textvariable=self.end_date_var)
            end_entry.pack(fill=tk.X, pady=(2, 5))
            end_entry.bind('<KeyRelease>', self.on_custom_date_change)
            
            # Chart options
            options_frame = ttk.Frame(chart_controls_frame)
            options_frame.pack(fill=tk.X, pady=(10, 0))
            
            # Price highlighter toggle
            self.highlighter_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(options_frame, text="Enable Price Highlighter", 
                           variable=self.highlighter_var,
                           command=self.toggle_highlighter).pack(anchor=tk.W)
            
            # Zoom controls
            zoom_frame = ttk.Frame(chart_controls_frame)
            zoom_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Label(zoom_frame, text="Zoom Controls:").pack(anchor=tk.W)
            
            zoom_buttons_frame = ttk.Frame(zoom_frame)
            zoom_buttons_frame.pack(fill=tk.X, pady=(5, 0))
            
            ttk.Button(zoom_buttons_frame, text="Zoom In", 
                      command=self.zoom_in, width=12).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(zoom_buttons_frame, text="Zoom Out", 
                      command=self.zoom_out, width=12).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(zoom_buttons_frame, text="Reset View", 
                      command=self.reset_zoom, width=12).pack(side=tk.LEFT)
            
            # Events section
            events_frame = ttk.LabelFrame(scrollable_frame, text="Significant Events", padding="10")
            events_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Events listbox
            ttk.Label(events_frame, text="Events:").pack(anchor=tk.W)
            
            listbox_frame = ttk.Frame(events_frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
            
            self.events_listbox = tk.Listbox(listbox_frame, height=6)  # Fixed height
            events_scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.events_listbox.yview)
            self.events_listbox.configure(yscrollcommand=events_scrollbar.set)
            
            self.events_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            events_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Bind event selection with error handling
            self.events_listbox.bind('<<ListboxSelect>>', self.safe_on_event_select)
            
            # Event buttons
            event_buttons_frame = ttk.Frame(events_frame)
            event_buttons_frame.pack(fill=tk.X, pady=5)
            
            ttk.Button(event_buttons_frame, text="Add Event", command=self.safe_add_event).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(event_buttons_frame, text="Add Range Event", command=self.safe_add_range_event).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(event_buttons_frame, text="Edit Event", command=self.safe_edit_event).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(event_buttons_frame, text="Delete Event", command=self.safe_delete_event).pack(side=tk.LEFT)
            
            # Analysis section
            analysis_frame = ttk.LabelFrame(scrollable_frame, text="Event Analysis", padding="10")
            analysis_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Time span selection
            ttk.Label(analysis_frame, text="Analyze impact after event:").pack(anchor=tk.W)
            
            timespan_frame = ttk.Frame(analysis_frame)
            timespan_frame.pack(fill=tk.X, pady=(5, 10))
            
            self.timespan_var = tk.StringVar(value="1w")
            timespan_combo = ttk.Combobox(timespan_frame, textvariable=self.timespan_var, 
                                         state="readonly", width=10)
            timespan_combo['values'] = ("1d", "3d", "1w", "2w", "1m", "3m", "6m")
            timespan_combo.pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(timespan_frame, text="Analyze Selected Event", 
                      command=self.safe_analyze_selected_event).pack(side=tk.LEFT)
            
            ttk.Button(timespan_frame, text="Compare Multiple Events", 
                      command=self.safe_compare_multiple_events).pack(side=tk.LEFT, padx=(10, 0))
            
            # Analysis results
            self.analysis_text = tk.Text(analysis_frame, height=6, wrap=tk.WORD)  # Fixed height
            analysis_scroll = ttk.Scrollbar(analysis_frame, orient=tk.VERTICAL, command=self.analysis_text.yview)
            self.analysis_text.configure(yscrollcommand=analysis_scroll.set)
            
            self.analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=(5, 0))
            analysis_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=(5, 0))
            
            # Pattern matching section
            pattern_frame = ttk.LabelFrame(scrollable_frame, text="Pattern Matching", padding="10")
            pattern_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Precision slider
            ttk.Label(pattern_frame, text="Search Precision:").pack(anchor=tk.W)
            
            precision_frame = ttk.Frame(pattern_frame)
            precision_frame.pack(fill=tk.X, pady=(5, 10))
            
            ttk.Label(precision_frame, text="Loose").pack(side=tk.LEFT)
            self.precision_var = tk.DoubleVar(value=0.80)
            self.precision_scale = tk.Scale(precision_frame, from_=0.01, to=1.00, 
                                           resolution=0.01, orient=tk.HORIZONTAL,
                                           variable=self.precision_var)
            self.precision_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
            ttk.Label(precision_frame, text="Exact").pack(side=tk.LEFT)
            
            # Search options
            search_options_frame = ttk.Frame(pattern_frame)
            search_options_frame.pack(fill=tk.X, pady=5)
            
            self.price_based_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(search_options_frame, text="Price-based search", 
                           variable=self.price_based_var).pack(anchor=tk.W)
            
            # Event context matching
            context_frame = ttk.LabelFrame(pattern_frame, text="Event Context Matching", padding="5")
            context_frame.pack(fill=tk.X, pady=(5, 10))
            
            # Enable context matching
            self.context_matching_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(context_frame, text="Match similar behavior before/after events", 
                           variable=self.context_matching_var,
                           command=self.toggle_context_controls).pack(anchor=tk.W)
            
            # Context controls
            self.context_controls = ttk.Frame(context_frame)
            self.context_controls.pack(fill=tk.X, pady=(5, 0))
            
            # Days before event
            before_frame = ttk.Frame(self.context_controls)
            before_frame.pack(fill=tk.X, pady=2)
            ttk.Label(before_frame, text="Days before event:").pack(side=tk.LEFT)
            self.days_before_var = tk.StringVar()
            self.days_before_entry = ttk.Entry(before_frame, textvariable=self.days_before_var, width=8)
            self.days_before_entry.pack(side=tk.LEFT, padx=(10, 5))
            ttk.Label(before_frame, text="(leave empty to ignore)", 
                     font=('Arial', 8), foreground='gray').pack(side=tk.LEFT)
            
            # Days after event
            after_frame = ttk.Frame(self.context_controls)
            after_frame.pack(fill=tk.X, pady=2)
            ttk.Label(after_frame, text="Days after event:").pack(side=tk.LEFT)
            self.days_after_var = tk.StringVar()
            self.days_after_entry = ttk.Entry(after_frame, textvariable=self.days_after_var, width=8)
            self.days_after_entry.pack(side=tk.LEFT, padx=(10, 5))
            ttk.Label(after_frame, text="(leave empty to ignore)", 
                     font=('Arial', 8), foreground='gray').pack(side=tk.LEFT)
            
            # Help text
            ttk.Label(self.context_controls, 
                     text="Match patterns where price behavior before/after the event is also similar",
                     font=('Arial', 8), foreground='blue').pack(anchor=tk.W, pady=(5, 0))
            
            # Price-based sentiment analysis
            sentiment_frame = ttk.LabelFrame(pattern_frame, text="Price-Based Sentiment Analysis", padding="5")
            sentiment_frame.pack(fill=tk.X, pady=(5, 10))
            
            # Enable sentiment analysis
            self.sentiment_analysis_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(sentiment_frame, text="Analyze market sentiment at similar price levels", 
                           variable=self.sentiment_analysis_var,
                           command=self.toggle_sentiment_controls).pack(anchor=tk.W)
            
            # Sentiment controls
            self.sentiment_controls = ttk.Frame(sentiment_frame)
            self.sentiment_controls.pack(fill=tk.X, pady=(5, 0))
            
            # Price tolerance
            tolerance_frame = ttk.Frame(self.sentiment_controls)
            tolerance_frame.pack(fill=tk.X, pady=2)
            ttk.Label(tolerance_frame, text="Price tolerance:").pack(side=tk.LEFT)
            self.price_tolerance_var = tk.StringVar(value="5")
            tolerance_entry = ttk.Entry(tolerance_frame, textvariable=self.price_tolerance_var, width=8)
            tolerance_entry.pack(side=tk.LEFT, padx=(10, 5))
            ttk.Label(tolerance_frame, text="% (±)", 
                     font=('Arial', 8), foreground='gray').pack(side=tk.LEFT)
            
            # Minimum occurrences
            min_occur_frame = ttk.Frame(self.sentiment_controls)
            min_occur_frame.pack(fill=tk.X, pady=2)
            ttk.Label(min_occur_frame, text="Min. occurrences:").pack(side=tk.LEFT)
            self.min_occurrences_var = tk.StringVar(value="3")
            min_occur_entry = ttk.Entry(min_occur_frame, textvariable=self.min_occurrences_var, width=8)
            min_occur_entry.pack(side=tk.LEFT, padx=(10, 5))
            ttk.Label(min_occur_frame, text="times at price level", 
                     font=('Arial', 8), foreground='gray').pack(side=tk.LEFT)
            
            # Help text
            ttk.Label(self.sentiment_controls, 
                     text="Find common market reactions when asset reaches similar price levels",
                     font=('Arial', 8), foreground='blue').pack(anchor=tk.W, pady=(5, 0))
            
            # Time frame selection
            time_frame_frame = ttk.LabelFrame(pattern_frame, text="Search Time Frame", padding="5")
            time_frame_frame.pack(fill=tk.X, pady=(10, 5))
            
            # Enable custom time frame
            self.custom_timeframe_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(time_frame_frame, text="Limit search to specific time period", 
                           variable=self.custom_timeframe_var,
                           command=self.toggle_timeframe_controls).pack(anchor=tk.W)
            
            # Time frame controls
            self.timeframe_controls = ttk.Frame(time_frame_frame)
            self.timeframe_controls.pack(fill=tk.X, pady=(5, 0))
            
            # Start date - stack vertically for better space usage
            ttk.Label(self.timeframe_controls, text="From:").pack(anchor=tk.W)
            self.search_start_var = tk.StringVar()
            start_entry_frame = ttk.Frame(self.timeframe_controls)
            start_entry_frame.pack(fill=tk.X, pady=(2, 5))
            self.search_start_entry = ttk.Entry(start_entry_frame, textvariable=self.search_start_var)
            self.search_start_entry.pack(fill=tk.X)
            
            # End date - stack vertically
            ttk.Label(self.timeframe_controls, text="To:").pack(anchor=tk.W)
            self.search_end_var = tk.StringVar()
            end_entry_frame = ttk.Frame(self.timeframe_controls)
            end_entry_frame.pack(fill=tk.X, pady=(2, 5))
            self.search_end_entry = ttk.Entry(end_entry_frame, textvariable=self.search_end_var)
            self.search_end_entry.pack(fill=tk.X)
            
            # Help text
            ttk.Label(self.timeframe_controls, text="Format: YYYY-MM-DD (leave empty for all data)", 
                     font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
            
            # Exclusion ranges
            exclusion_frame = ttk.LabelFrame(pattern_frame, text="Exclude Time Periods", padding="5")
            exclusion_frame.pack(fill=tk.X, pady=(5, 10))
            
            # Exclusion list
            excl_list_frame = ttk.Frame(exclusion_frame)
            excl_list_frame.pack(fill=tk.X, pady=(0, 5))
            
            self.exclusion_ranges_listbox = tk.Listbox(excl_list_frame, height=3)
            excl_scrollbar = ttk.Scrollbar(excl_list_frame, orient=tk.VERTICAL, 
                                          command=self.exclusion_ranges_listbox.yview)
            self.exclusion_ranges_listbox.configure(yscrollcommand=excl_scrollbar.set)
            
            self.exclusion_ranges_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            excl_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Exclusion buttons
            excl_button_frame = ttk.Frame(exclusion_frame)
            excl_button_frame.pack(fill=tk.X, pady=5)
            
            ttk.Button(excl_button_frame, text="Add Exclusion Range", 
                      command=self.safe_add_exclusion_range).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(excl_button_frame, text="Remove Selected", 
                      command=self.safe_remove_exclusion_range).pack(side=tk.LEFT)
            
            # Search button
            search_button_frame = ttk.Frame(pattern_frame)
            search_button_frame.pack(fill=tk.X, pady=(10, 0))
            
            ttk.Button(search_button_frame, text="Find Similar Patterns", 
                      command=self.safe_find_similar_patterns).pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(search_button_frame, text="Analyze Price Sentiment", 
                      command=self.safe_analyze_price_sentiment).pack(side=tk.LEFT)
            
            # Initialize exclusion ranges
            self.pattern_exclusion_ranges = []
            
            # Initially disable timeframe controls
            self.toggle_timeframe_controls()
            
            self.populate_events_list()
            
        except Exception as e:
            print(f"Error setting up left panel: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_right_panel(self, parent):
        """Set up the right panel with the chart."""
        try:
            # Create matplotlib figure
            self.fig, self.ax = plt.subplots(figsize=(12, 8))
            self.fig.tight_layout()
            
            # Create canvas
            self.canvas = FigureCanvasTkAgg(self.fig, parent)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # NEW: Connect mouse and key events for zoom and pan
            self.connect_chart_events()
            
            # Initial chart
            self.ax.set_title(f"{self.symbol} Price Chart")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price ($)")
            self.canvas.draw()
        except Exception as e:
            print(f"Error setting up chart: {e}")
    
    # NEW: Chart interaction methods
    def connect_chart_events(self):
        """Connect mouse and keyboard events for chart interaction."""
        try:
            # Mouse events
            self.canvas.mpl_connect('scroll_event', self.on_scroll)
            self.canvas.mpl_connect('button_press_event', self.on_button_press)
            self.canvas.mpl_connect('button_release_event', self.on_button_release)
            self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            
            # Keyboard events for focus
            self.canvas.get_tk_widget().bind("<Button-1>", lambda e: self.canvas.get_tk_widget().focus_set())
            
        except Exception as e:
            print(f"Error connecting chart events: {e}")
    
    def on_scroll(self, event):
        """Handle mouse wheel scrolling for zoom."""
        if not self.zoom_enabled or event.inaxes != self.ax:
            return
        
        try:
            # Get current axis limits
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # Calculate zoom factor
            zoom_factor = 1.1 if event.step < 0 else 0.9
            
            # Get mouse position in data coordinates
            if event.xdata is not None and event.ydata is not None:
                mouse_x = event.xdata
                mouse_y = event.ydata
                
                # Calculate new limits centered on mouse position
                x_range = xlim[1] - xlim[0]
                y_range = ylim[1] - ylim[0]
                
                new_x_range = x_range * zoom_factor
                new_y_range = y_range * zoom_factor
                
                # Calculate new limits
                x_center_offset = (mouse_x - xlim[0]) / x_range
                y_center_offset = (mouse_y - ylim[0]) / y_range
                
                new_xlim = [
                    mouse_x - new_x_range * x_center_offset,
                    mouse_x + new_x_range * (1 - x_center_offset)
                ]
                new_ylim = [
                    mouse_y - new_y_range * y_center_offset,
                    mouse_y + new_y_range * (1 - y_center_offset)
                ]
                
                # Apply limits
                self.ax.set_xlim(new_xlim)
                self.ax.set_ylim(new_ylim)
                
                # Update zoom scale
                self.zoom_scale *= zoom_factor
                
                self.canvas.draw_idle()
                
        except Exception as e:
            print(f"Error in scroll event: {e}")
    
    def on_button_press(self, event):
        """Handle mouse button press for panning."""
        if event.inaxes != self.ax:
            return
        
        if event.button == 1:  # Left mouse button
            self.is_panning = True
            self.pan_start = (event.xdata, event.ydata)
    
    def on_button_release(self, event):
        """Handle mouse button release."""
        if event.button == 1:  # Left mouse button
            self.is_panning = False
            self.pan_start = None
    
    def on_mouse_move(self, event):
        """Handle mouse movement for both panning and highlighting."""
        if event.inaxes != self.ax:
            return
            
        try:
            # Handle panning
            if self.is_panning and self.pan_start and self.pan_enabled:
                if event.xdata is not None and event.ydata is not None:
                    dx = self.pan_start[0] - event.xdata
                    dy = self.pan_start[1] - event.ydata
                    
                    xlim = self.ax.get_xlim()
                    ylim = self.ax.get_ylim()
                    
                    self.ax.set_xlim([xlim[0] + dx, xlim[1] + dx])
                    self.ax.set_ylim([ylim[0] + dy, ylim[1] + dy])
                    
                    self.canvas.draw_idle()
                return
            
            # Handle price highlighting
            if self.highlighter_enabled and self.mouse_move_connected:
                self.update_crosshair(event)
                
        except Exception as e:
            print(f"Error in mouse move: {e}")
    
    def update_crosshair(self, event):
        """Update crosshair and price information."""
        if not self.highlighter_enabled or event.inaxes != self.ax:
            return
        
        # Performance throttling
        import time
        current_time = time.time() * 1000
        if current_time - self.last_mouse_time < 50:
            return
        self.last_mouse_time = current_time
        
        try:
            # Clear previous crosshair
            if self.crosshair_v:
                self.crosshair_v.remove()
            if self.crosshair_h:
                self.crosshair_h.remove()
            if self.price_info_text:
                self.price_info_text.remove()
            
            # Draw new crosshair
            self.crosshair_v = self.ax.axvline(event.xdata, color='red', alpha=0.7, linestyle='--')
            self.crosshair_h = self.ax.axhline(event.ydata, color='red', alpha=0.7, linestyle='--')
            
            # Get closest data point
            if hasattr(self, 'df') and not self.df.empty:
                mouse_date = pd.to_datetime(event.xdata, origin='unix', unit='D')
                
                # Find closest date
                closest_idx = self.df.index.get_indexer([mouse_date], method='nearest')[0]
                if 0 <= closest_idx < len(self.df):
                    closest_date = self.df.index[closest_idx]
                    closest_row = self.df.iloc[closest_idx]
                    
                    # Create info text
                    info_text = f"Date: {closest_date.strftime('%Y-%m-%d')}\n"
                    info_text += f"Open: ${closest_row['open']:.2f}\n"
                    info_text += f"High: ${closest_row['high']:.2f}\n"
                    info_text += f"Low: ${closest_row['low']:.2f}\n"
                    info_text += f"Close: ${closest_row['close']:.2f}\n"
                    if pd.notna(closest_row['volume']):
                        info_text += f"Volume: {closest_row['volume']:,}"
                    
                    # Position info box
                    self.price_info_text = self.ax.text(
                        0.02, 0.98, info_text,
                        transform=self.ax.transAxes,
                        fontsize=10,
                        verticalalignment='top',
                        horizontalalignment='left',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9, edgecolor='black'),
                        family='monospace'
                    )
            
            self.canvas.draw_idle()
            
        except Exception as e:
            pass  # Silently handle errors to avoid disrupting mouse movement
    
    def zoom_in(self):
        """Zoom in by a fixed factor."""
        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            zoom_factor = 0.8
            
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            
            self.ax.set_xlim([x_center - x_range, x_center + x_range])
            self.ax.set_ylim([y_center - y_range, y_center + y_range])
            
            self.zoom_scale *= 1.25
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error zooming in: {e}")
    
    def zoom_out(self):
        """Zoom out by a fixed factor."""
        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            zoom_factor = 1.25
            
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            
            x_range = (xlim[1] - xlim[0]) * zoom_factor / 2
            y_range = (ylim[1] - ylim[0]) * zoom_factor / 2
            
            self.ax.set_xlim([x_center - x_range, x_center + x_range])
            self.ax.set_ylim([y_center - y_range, y_center + y_range])
            
            self.zoom_scale *= 0.8
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error zooming out: {e}")
    
    def reset_zoom(self):
        """Reset zoom to show all data."""
        try:
            if hasattr(self, 'df') and not self.df.empty:
                # Apply current date range
                filtered_df = self.apply_date_filter(self.df)
                if not filtered_df.empty:
                    self.ax.set_xlim(filtered_df.index.min(), filtered_df.index.max())
                    self.ax.set_ylim(filtered_df['low'].min() * 0.95, filtered_df['high'].max() * 1.05)
                else:
                    self.ax.set_xlim(self.df.index.min(), self.df.index.max())
                    self.ax.set_ylim(self.df['low'].min() * 0.95, self.df['high'].max() * 1.05)
            
            self.zoom_scale = 1.0
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error resetting zoom: {e}")
    
    def toggle_highlighter(self):
        """Toggle the price highlighter on/off."""
        self.highlighter_enabled = self.highlighter_var.get()
        
        if self.highlighter_enabled:
            self.mouse_move_connected = True
        else:
            self.mouse_move_connected = False
            # Clear existing crosshair
            if self.crosshair_v:
                self.crosshair_v.remove()
                self.crosshair_v = None
            if self.crosshair_h:
                self.crosshair_h.remove()
                self.crosshair_h = None
            if self.price_info_text:
                self.price_info_text.remove()
                self.price_info_text = None
            self.canvas.draw()
    
    def on_date_range_change(self, event=None):
        """Handle date range selection change."""
        self.current_date_range = self.date_range_var.get()
        
        if self.current_date_range == "custom":
            self.custom_date_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.custom_date_frame.pack_forget()
            # Apply non-custom date range immediately
            self.update_chart()
    
    def on_custom_date_change(self, event=None):
        """Handle custom date entry changes."""
        if self.current_date_range == "custom":
            # Only update if both dates are entered and valid
            start_str = self.start_date_var.get()
            end_str = self.end_date_var.get()
            
            if start_str and end_str:
                try:
                    self.custom_start_date = pd.to_datetime(start_str).tz_localize(None)
                    self.custom_end_date = pd.to_datetime(end_str).tz_localize(None)
                    self.update_chart()
                except (ValueError, TypeError):
                    pass  # Invalid date format, don't update
    
    def apply_date_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply current date range filter to DataFrame."""
        if df.empty:
            return df
        
        try:
            if self.current_date_range == "all":
                return df
            elif self.current_date_range == "custom":
                if self.custom_start_date and self.custom_end_date:
                    return df[(df.index >= self.custom_start_date) & (df.index <= self.custom_end_date)]
                return df
            else:
                # Calculate date range
                end_date = df.index.max()
                
                if self.current_date_range == "1d":
                    start_date = end_date - pd.Timedelta(days=1)
                elif self.current_date_range == "1w":
                    start_date = end_date - pd.Timedelta(weeks=1)
                elif self.current_date_range == "1m":
                    start_date = end_date - pd.Timedelta(days=30)
                elif self.current_date_range == "3m":
                    start_date = end_date - pd.Timedelta(days=90)
                elif self.current_date_range == "6m":
                    start_date = end_date - pd.Timedelta(days=180)
                elif self.current_date_range == "1y":
                    start_date = end_date - pd.Timedelta(days=365)
                elif self.current_date_range == "2y":
                    start_date = end_date - pd.Timedelta(days=730)
                elif self.current_date_range == "5y":
                    start_date = end_date - pd.Timedelta(days=1825)
                else:
                    return df
                
                return df[df.index >= start_date]
                
        except Exception as e:
            print(f"Error applying date filter: {e}")
            return df
    
    def load_chart_data(self):
        """Load and prepare chart data."""
        try:
            # Convert historical data to DataFrame
            self.df = pd.DataFrame(self.asset_data['historical_data'])
            self.df['date'] = pd.to_datetime(self.df['date'], utc=True)
            self.df.set_index('date', inplace=True)
            self.df.index = self.df.index.tz_convert(None)  # Remove timezone
        except Exception as e:
            print(f"Error loading chart data: {e}")
            self.df = pd.DataFrame()  # Empty dataframe as fallback
    
    def update_chart(self):
        """Update the chart display."""
        if self.is_closing or self.df.empty:
            return
        
        try:
            self.ax.clear()
            
            # Clear crosshair elements
            self.crosshair_v = None
            self.crosshair_h = None
            self.price_info_text = None
            
            # Apply date filtering
            filtered_df = self.apply_date_filter(self.df)
            
            if filtered_df.empty:
                self.ax.set_title(f"{self.symbol} - No data for selected date range")
                self.canvas.draw()
                return
            
            # Plot price line
            self.ax.plot(filtered_df.index, filtered_df['close'], 
                        label=f"{self.symbol}", linewidth=2, color='blue')
            
            # Plot events as vertical lines
            for event in self.events:
                if event['type'] == 'single':
                    event_date = pd.to_datetime(event['date'])
                    if filtered_df.index.min() <= event_date <= filtered_df.index.max():
                        self.ax.axvline(event_date, color='red', linestyle='--', alpha=0.7, linewidth=2)
                        
                        # Add event label
                        y_max = self.ax.get_ylim()[1]
                        self.ax.text(event_date, y_max * 0.95, event['label'], 
                                    rotation=90, verticalalignment='top', 
                                    fontsize=9, color='red', alpha=0.8)
                
                elif event['type'] == 'range':
                    start_date = pd.to_datetime(event['start_date'])
                    end_date = pd.to_datetime(event['end_date'])
                    
                    # Check if range overlaps with visible data
                    if (start_date <= filtered_df.index.max() and end_date >= filtered_df.index.min()):
                        # Highlight the range
                        self.ax.axvspan(start_date, end_date, alpha=0.3, color='orange')
                        
                        # Add label at the start
                        y_max = self.ax.get_ylim()[1]
                        self.ax.text(start_date, y_max * 0.95, event['label'], 
                                    rotation=90, verticalalignment='top', 
                                    fontsize=9, color='orange', alpha=0.8)
            
            # Set chart title and labels
            date_info = ""
            if self.current_date_range != "all":
                if self.current_date_range == "custom":
                    if self.custom_start_date and self.custom_end_date:
                        date_info = f" ({self.custom_start_date.strftime('%Y-%m-%d')} to {self.custom_end_date.strftime('%Y-%m-%d')})"
                else:
                    date_info = f" (Last {self.current_date_range.upper()})"
            
            self.ax.set_title(f"{self.symbol} Price Chart{date_info}")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price ($)")
            self.ax.legend()
            self.ax.grid(True, alpha=0.3)
            
            # Set reasonable axis limits
            if not filtered_df.empty:
                y_min = filtered_df['low'].min() * 0.95
                y_max = filtered_df['high'].max() * 1.05
                self.ax.set_ylim(y_min, y_max)
            
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)
            self.fig.tight_layout()
            
            # Enable highlighting if option is checked
            if self.highlighter_enabled:
                self.mouse_move_connected = True
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating chart: {e}")
    
    # Safe wrapper methods to prevent errors during window closing
    def safe_on_event_select(self, event):
        """Safe wrapper for on_event_select."""
        if not self.is_closing:
            try:
                self.on_event_select(event)
            except Exception as e:
                print(f"Error in event select: {e}")
    
    def safe_add_event(self):
        """Safe wrapper for add_event."""
        if not self.is_closing:
            try:
                self.add_event()
            except Exception as e:
                print(f"Error adding event: {e}")
    
    def safe_add_range_event(self):
        """Safe wrapper for add_range_event."""
        if not self.is_closing:
            try:
                self.add_range_event()
            except Exception as e:
                print(f"Error adding range event: {e}")
    
    def safe_edit_event(self):
        """Safe wrapper for edit_event."""
        if not self.is_closing:
            try:
                self.edit_event()
            except Exception as e:
                print(f"Error editing event: {e}")
    
    def safe_delete_event(self):
        """Safe wrapper for delete_event."""
        if not self.is_closing:
            try:
                self.delete_event()
            except Exception as e:
                print(f"Error deleting event: {e}")
    
    def safe_analyze_selected_event(self):
        """Safe wrapper for analyze_selected_event."""
        if not self.is_closing:
            try:
                self.analyze_selected_event()
            except Exception as e:
                print(f"Error analyzing event: {e}")
    
    def safe_compare_multiple_events(self):
        """Safe wrapper for compare_multiple_events."""
        if not self.is_closing:
            try:
                self.compare_multiple_events()
            except Exception as e:
                print(f"Error comparing events: {e}")
    
    def safe_add_exclusion_range(self):
        """Safe wrapper for add_exclusion_range."""
        if not self.is_closing:
            try:
                self.add_exclusion_range()
            except Exception as e:
                print(f"Error adding exclusion range: {e}")
    
    def safe_remove_exclusion_range(self):
        """Safe wrapper for remove_exclusion_range."""
        if not self.is_closing:
            try:
                self.remove_exclusion_range()
            except Exception as e:
                print(f"Error removing exclusion range: {e}")
    
    def safe_find_similar_patterns(self):
        """Safe wrapper for find_similar_patterns."""
        if not self.is_closing:
            try:
                self.find_similar_patterns()
            except Exception as e:
                print(f"Error finding patterns: {e}")
    
    def safe_analyze_price_sentiment(self):
        """Safe wrapper for analyze_price_sentiment."""
        if not self.is_closing:
            try:
                self.analyze_price_sentiment()
            except Exception as e:
                print(f"Error analyzing sentiment: {e}")
    
    def toggle_sentiment_controls(self):
        """Enable/disable sentiment analysis controls based on checkbox."""
        if self.is_closing:
            return
        
        try:
            if self.sentiment_analysis_var.get():
                # Enable the entry fields
                for widget in self.sentiment_controls.winfo_children():
                    self.enable_widget_tree(widget)
            else:
                # Disable the entry fields
                for widget in self.sentiment_controls.winfo_children():
                    self.disable_widget_tree(widget)
        except Exception as e:
            print(f"Debug: Error toggling sentiment controls: {e}")
    
    def toggle_context_controls(self):
        """Enable/disable context matching controls based on checkbox."""
        if self.is_closing:
            return
        
        try:
            if self.context_matching_var.get():
                # Enable the entry fields
                self.days_before_entry.config(state='normal')
                self.days_after_entry.config(state='normal')
            else:
                # Disable the entry fields and clear them
                self.days_before_entry.config(state='disabled')
                self.days_after_entry.config(state='disabled')
                self.days_before_var.set('')
                self.days_after_var.set('')
        except Exception as e:
            print(f"Debug: Error toggling context controls: {e}")
    
    def toggle_timeframe_controls(self):
        """Enable/disable timeframe controls based on checkbox."""
        if self.is_closing:
            return
        
        print(f"Debug: Checkbox state: {self.custom_timeframe_var.get()}")
        
        try:
            if self.custom_timeframe_var.get():
                # Enable the entry fields
                self.search_start_entry.config(state='normal')
                self.search_end_entry.config(state='normal')
                print("Debug: Enabled timeframe controls")
            else:
                # Disable the entry fields and clear them
                self.search_start_entry.config(state='disabled')
                self.search_end_entry.config(state='disabled')
                self.search_start_var.set('')
                self.search_end_var.set('')
                print("Debug: Disabled and cleared timeframe controls")
        except Exception as e:
            print(f"Debug: Error toggling timeframe controls: {e}")
    
    def enable_widget_tree(self, widget):
        """Recursively enable a widget and its children."""
        if self.is_closing:
            return
        try:
            widget.config(state='normal')
        except:
            pass
        try:
            for child in widget.winfo_children():
                self.enable_widget_tree(child)
        except:
            pass
    
    def disable_widget_tree(self, widget):
        """Recursively disable a widget and its children."""
        if self.is_closing:
            return
        try:
            widget.config(state='disabled')
        except:
            pass
        try:
            for child in widget.winfo_children():
                self.disable_widget_tree(child)
        except:
            pass
    
    def add_exclusion_range(self):
        """Add a time range to exclude from pattern matching."""
        if self.is_closing:
            return
        
        start_date = simpledialog.askstring("Add Exclusion Range", 
                                           "Enter start date to exclude (YYYY-MM-DD):")
        if not start_date:
            return
        
        end_date = simpledialog.askstring("Add Exclusion Range", 
                                         "Enter end date to exclude (YYYY-MM-DD):")
        if not end_date:
            return
        
        try:
            # Validate dates
            pd.to_datetime(start_date)
            pd.to_datetime(end_date)
            
            reason = simpledialog.askstring("Exclusion Reason", 
                                          "Enter reason for exclusion (optional):") or "User defined"
            
            exclusion = {
                'start_date': start_date,
                'end_date': end_date,
                'reason': reason
            }
            
            self.pattern_exclusion_ranges.append(exclusion)
            self.update_exclusion_ranges_list()
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter valid dates in YYYY-MM-DD format.")
    
    def remove_exclusion_range(self):
        """Remove selected exclusion range."""
        if self.is_closing or not self.exclusion_ranges_listbox:
            return
        
        try:
            selection = self.exclusion_ranges_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an exclusion range to remove.")
                return
            
            index = selection[0]
            if 0 <= index < len(self.pattern_exclusion_ranges):
                del self.pattern_exclusion_ranges[index]
                self.update_exclusion_ranges_list()
        except Exception as e:
            print(f"Error removing exclusion range: {e}")
    
    def update_exclusion_ranges_list(self):
        """Update the exclusion ranges listbox."""
        if self.is_closing or not self.exclusion_ranges_listbox:
            return
        
        try:
            self.exclusion_ranges_listbox.delete(0, tk.END)
            
            for exclusion in self.pattern_exclusion_ranges:
                display_text = f"{exclusion['start_date']} to {exclusion['end_date']} - {exclusion['reason']}"
                self.exclusion_ranges_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error updating exclusion ranges: {e}")
    
    def load_events(self) -> List[Dict]:
        """Load events for this asset."""
        events_file = self.get_events_file_path()
        if os.path.exists(events_file):
            try:
                with open(events_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading events: {e}")
                return []
        return []
    
    def save_events(self):
        """Save events for this asset."""
        if self.is_closing:
            return
        
        events_file = self.get_events_file_path()
        os.makedirs(os.path.dirname(events_file), exist_ok=True)
        
        try:
            with open(events_file, 'w') as f:
                json.dump(self.events, f, indent=2)
        except Exception as e:
            print(f"Error saving events: {e}")
            messagebox.showerror("Save Error", f"Could not save events: {str(e)}")
    
    def get_events_file_path(self) -> str:
        """Get the file path for events storage."""
        asset_dir = filepath_manager.get_asset_dir(self.asset_type)
        return os.path.join(asset_dir, f"{self.symbol}_events.json")
    
    def populate_events_list(self):
        """Populate the events listbox."""
        if self.is_closing or not self.events_listbox:
            return
        
        try:
            self.events_listbox.delete(0, tk.END)
            
            for i, event in enumerate(self.events):
                if event['type'] == 'single':
                    display_text = f"{event['date']} - {event['label']}"
                else:  # range
                    display_text = f"{event['start_date']} to {event['end_date']} - {event['label']}"
                
                self.events_listbox.insert(tk.END, display_text)
        except Exception as e:
            print(f"Error populating events list: {e}")
    
    def add_event(self):
        """Add a single date event."""
        if self.is_closing:
            return
        
        date_str = simpledialog.askstring("Add Event", "Enter event date (YYYY-MM-DD):")
        if not date_str:
            return
        
        try:
            pd.to_datetime(date_str)  # Validate date
            label = simpledialog.askstring("Event Label", "Enter event description:")
            if not label:
                return
            
            event = {
                'type': 'single',
                'date': date_str,
                'label': label,
                'created': datetime.now().isoformat()
            }
            
            self.events.append(event)
            self.save_events()
            self.populate_events_list()
            self.update_chart()
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
        except Exception as e:
            print(f"Error adding event: {e}")
    
    def add_range_event(self):
        """Add a date range event."""
        if self.is_closing:
            return
        
        start_date = simpledialog.askstring("Add Range Event", "Enter start date (YYYY-MM-DD):")
        if not start_date:
            return
        
        end_date = simpledialog.askstring("Add Range Event", "Enter end date (YYYY-MM-DD):")
        if not end_date:
            return
        
        try:
            pd.to_datetime(start_date)
            pd.to_datetime(end_date)
            
            label = simpledialog.askstring("Event Label", "Enter event description:")
            if not label:
                return
            
            event = {
                'type': 'range',
                'start_date': start_date,
                'end_date': end_date,
                'label': label,
                'created': datetime.now().isoformat()
            }
            
            self.events.append(event)
            self.save_events()
            self.populate_events_list()
            self.update_chart()
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter valid dates in YYYY-MM-DD format.")
        except Exception as e:
            print(f"Error adding range event: {e}")
    
    def edit_event(self):
        """Edit selected event."""
        if self.is_closing or not self.events_listbox:
            return
        
        try:
            selection = self.events_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an event to edit.")
                return
            
            # For now, just allow editing the label
            event_idx = selection[0]
            event = self.events[event_idx]
            
            new_label = simpledialog.askstring("Edit Event", "Enter new event description:", 
                                              initialvalue=event['label'])
            if new_label:
                self.events[event_idx]['label'] = new_label
                self.save_events()
                self.populate_events_list()
                self.update_chart()
        except Exception as e:
            print(f"Error editing event: {e}")
    
    def delete_event(self):
        """Delete selected event."""
        if self.is_closing or not self.events_listbox:
            return
        
        try:
            selection = self.events_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an event to delete.")
                return
            
            event_idx = selection[0]
            event = self.events[event_idx]
            
            result = messagebox.askyesno("Confirm Delete", 
                                       f"Delete event '{event['label']}'?")
            if result:
                del self.events[event_idx]
                self.save_events()
                self.populate_events_list()
                self.update_chart()
        except Exception as e:
            print(f"Error deleting event: {e}")
    
    def on_event_select(self, event):
        """Handle event selection."""
        if self.is_closing or not self.events_listbox:
            return
        
        try:
            selection = self.events_listbox.curselection()
            if selection:
                self.selected_event = self.events[selection[0]]
            else:
                self.selected_event = None
        except Exception as e:
            print(f"Error handling event selection: {e}")
    
    def analyze_selected_event(self):
        """Analyze the impact of the selected event."""
        if self.is_closing or not self.selected_event:
            if not self.selected_event:
                messagebox.showwarning("No Selection", "Please select an event to analyze.")
            return
        
        try:
            timespan = self.timespan_var.get()
            
            # Get event date(s)
            if self.selected_event['type'] == 'single':
                event_date = pd.to_datetime(self.selected_event['date'])
                analysis_start = event_date
            else:  # range
                event_start = pd.to_datetime(self.selected_event['start_date'])
                event_end = pd.to_datetime(self.selected_event['end_date'])
                analysis_start = event_end  # Start analysis from end of range
            
            # Calculate analysis end date
            if timespan == "1d":
                analysis_end = analysis_start + pd.Timedelta(days=1)
            elif timespan == "3d":
                analysis_end = analysis_start + pd.Timedelta(days=3)
            elif timespan == "1w":
                analysis_end = analysis_start + pd.Timedelta(weeks=1)
            elif timespan == "2w":
                analysis_end = analysis_start + pd.Timedelta(weeks=2)
            elif timespan == "1m":
                analysis_end = analysis_start + pd.Timedelta(days=30)
            elif timespan == "3m":
                analysis_end = analysis_start + pd.Timedelta(days=90)
            elif timespan == "6m":
                analysis_end = analysis_start + pd.Timedelta(days=180)
            
            # Get price data for analysis period
            event_data = self.df[(self.df.index >= analysis_start) & (self.df.index <= analysis_end)]
            
            if event_data.empty:
                self.analysis_text.delete(1.0, tk.END)
                self.analysis_text.insert(tk.END, "No data available for the analysis period.")
                return
            
            # Calculate metrics
            start_price = self.df[self.df.index <= analysis_start]['close'].iloc[-1] if len(self.df[self.df.index <= analysis_start]) > 0 else event_data['close'].iloc[0]
            end_price = event_data['close'].iloc[-1]
            percent_change = ((end_price - start_price) / start_price) * 100
            
            # Calculate volatility (standard deviation of daily returns)
            daily_returns = event_data['close'].pct_change().dropna()
            volatility = daily_returns.std() * 100  # Convert to percentage
            
            # Find max and min during period
            max_price = event_data['close'].max()
            min_price = event_data['close'].min()
            max_gain = ((max_price - start_price) / start_price) * 100
            max_loss = ((min_price - start_price) / start_price) * 100
            
            # Display analysis
            analysis = f"""Event Analysis: {self.selected_event['label']}
Analysis Period: {analysis_start.strftime('%Y-%m-%d')} to {analysis_end.strftime('%Y-%m-%d')}

Price Impact:
• Starting Price: ${start_price:.2f}
• Ending Price: ${end_price:.2f}
• Total Change: {percent_change:+.2f}%

Volatility Analysis:
• Daily Volatility: {volatility:.2f}%
• Max Gain: {max_gain:+.2f}% (${max_price:.2f})
• Max Loss: {max_loss:+.2f}% (${min_price:.2f})

Classification:
• Impact: {'High' if abs(percent_change) > 10 else 'Medium' if abs(percent_change) > 5 else 'Low'}
• Volatility: {'High' if volatility > 3 else 'Medium' if volatility > 1.5 else 'Low'}
• Direction: {'Positive' if percent_change > 0 else 'Negative' if percent_change < 0 else 'Neutral'}
"""
            
            self.analysis_text.delete(1.0, tk.END)
            self.analysis_text.insert(tk.END, analysis)
            
        except Exception as e:
            print(f"Error analyzing event: {e}")
            messagebox.showerror("Analysis Error", f"Error analyzing event: {str(e)}")
    
    def compare_multiple_events(self):
        """Compare multiple events side by side."""
        if self.is_closing:
            return
        
        if not self.events:
            messagebox.showwarning("No Events", "Please add some events first.")
            return
        
        try:
            comparison_window = tk.Toplevel(self.window)
            comparison_window.title("Event Comparison")
            comparison_window.geometry("900x700")
            
            # Create comparison interface
            main_frame = ttk.Frame(comparison_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text="Multiple Event Comparison Analysis", 
                     font=('Arial', 16, 'bold')).pack(pady=(0, 10))
            
            # Create notebook for different comparison views
            notebook = ttk.Notebook(main_frame)
            notebook.pack(fill=tk.BOTH, expand=True)
            
            # Summary comparison tab
            summary_frame = ttk.Frame(notebook)
            notebook.add(summary_frame, text="Summary")
            
            # Detailed comparison tab
            detailed_frame = ttk.Frame(notebook)
            notebook.add(detailed_frame, text="Detailed Analysis")
            
            # Summary comparison
            summary_text = tk.Text(summary_frame, wrap=tk.WORD)
            summary_scroll = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=summary_text.yview)
            summary_text.configure(yscrollcommand=summary_scroll.set)
            
            summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            summary_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Generate comparison report
            comparison_report = f"Event Comparison Report for {self.symbol}\n"
            comparison_report += "=" * 60 + "\n\n"
            
            for i, event in enumerate(self.events):
                comparison_report += f"Event {i+1}: {event['label']}\n"
                if event['type'] == 'single':
                    comparison_report += f"Date: {event['date']}\n"
                else:
                    comparison_report += f"Date Range: {event['start_date']} to {event['end_date']}\n"
                
                # Analyze this event's impact
                try:
                    if event['type'] == 'single':
                        event_date = pd.to_datetime(event['date'])
                        analysis_start = event_date
                    else:
                        analysis_start = pd.to_datetime(event['end_date'])
                    
                    analysis_end = analysis_start + pd.Timedelta(weeks=1)
                    event_data = self.df[(self.df.index >= analysis_start) & (self.df.index <= analysis_end)]
                    
                    if not event_data.empty:
                        start_price = self.df[self.df.index <= analysis_start]['close'].iloc[-1] if len(self.df[self.df.index <= analysis_start]) > 0 else event_data['close'].iloc[0]
                        end_price = event_data['close'].iloc[-1]
                        percent_change = ((end_price - start_price) / start_price) * 100
                        
                        comparison_report += f"1-Week Impact: {percent_change:+.2f}%\n"
                        comparison_report += f"Classification: {'High' if abs(percent_change) > 10 else 'Medium' if abs(percent_change) > 5 else 'Low'} Impact\n"
                    else:
                        comparison_report += "Impact: No data available\n"
                        
                except Exception:
                    comparison_report += "Impact: Analysis error\n"
                
                comparison_report += "\n" + "-" * 40 + "\n\n"
            
            summary_text.insert(tk.END, comparison_report)
            summary_text.config(state='disabled')
            
            # Detailed comparison with charts would go in detailed_frame
            # For now, just add a placeholder
            ttk.Label(detailed_frame, text="Detailed comparison charts coming soon!", 
                     font=('Arial', 12)).pack(expand=True)
            
        except Exception as e:
            print(f"Error in event comparison: {e}")
            messagebox.showerror("Comparison Error", f"Error comparing events: {str(e)}")
    
    def analyze_price_sentiment(self):
        """Analyze market sentiment at similar price levels to the selected event."""
        if self.is_closing:
            return
        
        if not self.selected_event:
            messagebox.showwarning("No Selection", "Please select an event to analyze price sentiment.")
            return
        
        if not self.sentiment_analysis_var.get():
            messagebox.showwarning("Feature Disabled", "Please enable 'Analyze market sentiment at similar price levels' first.")
            return
        
        try:
            # Get event price
            if self.selected_event['type'] == 'single':
                event_date = pd.to_datetime(self.selected_event['date'])
                event_price_data = self.df[self.df.index == event_date]
                if event_price_data.empty:
                    # Find closest date
                    closest_idx = self.df.index.get_indexer([event_date], method='nearest')[0]
                    event_price = self.df.iloc[closest_idx]['close']
                else:
                    event_price = event_price_data['close'].iloc[0]
            else:  # range
                event_start = pd.to_datetime(self.selected_event['start_date'])
                event_end = pd.to_datetime(self.selected_event['end_date'])
                range_data = self.df[(self.df.index >= event_start) & (self.df.index <= event_end)]
                if range_data.empty:
                    messagebox.showwarning("No Data", "No price data found for the selected event range.")
                    return
                event_price = range_data['close'].mean()  # Use average price during range
            
            # Get tolerance settings
            try:
                price_tolerance = float(self.price_tolerance_var.get()) / 100
                min_occurrences = int(self.min_occurrences_var.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers for price tolerance and minimum occurrences.")
                return
            
            # Find similar price levels
            price_range_min = event_price * (1 - price_tolerance)
            price_range_max = event_price * (1 + price_tolerance)
            
            similar_price_data = self.df[
                (self.df['close'] >= price_range_min) & 
                (self.df['close'] <= price_range_max)
            ]
            
            if len(similar_price_data) < min_occurrences:
                messagebox.showinfo("Insufficient Data", 
                                   f"Found only {len(similar_price_data)} occurrences at similar price levels. "
                                   f"Minimum required: {min_occurrences}")
                return
            
            # Analyze market reactions at similar price levels
            reactions = []
            for idx, (date, row) in enumerate(similar_price_data.iterrows()):
                # Look at next few days to see reaction
                future_dates = self.df[self.df.index > date].head(5)  # Next 5 days
                if not future_dates.empty:
                    start_price_reaction = row['close']
                    end_price_reaction = future_dates['close'].iloc[-1]
                    reaction_pct = ((end_price_reaction - start_price_reaction) / start_price_reaction) * 100
                    reactions.append({
                        'date': date,
                        'price': start_price_reaction,
                        'reaction_pct': reaction_pct,
                        'reaction_direction': 'Positive' if reaction_pct > 1 else 'Negative' if reaction_pct < -1 else 'Neutral'
                    })
            
            if not reactions:
                messagebox.showinfo("No Reactions", "No reaction data found for similar price levels.")
                return
            
            # Calculate sentiment statistics
            positive_reactions = [r for r in reactions if r['reaction_direction'] == 'Positive']
            negative_reactions = [r for r in reactions if r['reaction_direction'] == 'Negative']
            neutral_reactions = [r for r in reactions if r['reaction_direction'] == 'Neutral']
            
            avg_reaction = np.mean([r['reaction_pct'] for r in reactions])
            
            # Create sentiment analysis window
            sentiment_window = tk.Toplevel(self.window)
            sentiment_window.title("Price Sentiment Analysis")
            sentiment_window.geometry("600x500")
            
            main_frame = ttk.Frame(sentiment_window, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            ttk.Label(main_frame, text="Price-Based Sentiment Analysis", 
                     font=('Arial', 16, 'bold')).pack(pady=(0, 10))
            
            # Analysis results
            analysis_text = tk.Text(main_frame, wrap=tk.WORD, height=20)
            analysis_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=analysis_text.yview)
            analysis_text.configure(yscrollcommand=analysis_scroll.set)
            
            analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            analysis_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Generate analysis report
            sentiment_report = f"""Price Sentiment Analysis for {self.symbol}
Event: {self.selected_event['label']}
Target Price Level: ${event_price:.2f}
Price Range: ${price_range_min:.2f} - ${price_range_max:.2f} (±{price_tolerance*100:.1f}%)

=== SENTIMENT SUMMARY ===
Total Occurrences: {len(reactions)}
Average Market Reaction: {avg_reaction:+.2f}%

Sentiment Breakdown:
• Positive Reactions: {len(positive_reactions)} ({len(positive_reactions)/len(reactions)*100:.1f}%)
• Negative Reactions: {len(negative_reactions)} ({len(negative_reactions)/len(reactions)*100:.1f}%)
• Neutral Reactions: {len(neutral_reactions)} ({len(neutral_reactions)/len(reactions)*100:.1f}%)

=== MARKET SENTIMENT INTERPRETATION ===
"""
            
            if len(positive_reactions) > len(negative_reactions) * 1.5:
                sentiment_report += "BULLISH: Market typically reacts positively at this price level.\n"
            elif len(negative_reactions) > len(positive_reactions) * 1.5:
                sentiment_report += "BEARISH: Market typically reacts negatively at this price level.\n"
            else:
                sentiment_report += "MIXED: Market reactions are divided at this price level.\n"
            
            sentiment_report += f"\n=== HISTORICAL OCCURRENCES ===\n"
            
            for i, reaction in enumerate(reactions[-20:]):  # Show last 20 occurrences
                sentiment_report += f"{reaction['date'].strftime('%Y-%m-%d')}: ${reaction['price']:.2f} → {reaction['reaction_pct']:+.1f}% ({reaction['reaction_direction']})\n"
            
            if len(reactions) > 20:
                sentiment_report += f"\n... and {len(reactions) - 20} more occurrences"
            
            analysis_text.insert(tk.END, sentiment_report)
            analysis_text.config(state='disabled')
            
        except Exception as e:
            print(f"Error in price sentiment analysis: {e}")
            messagebox.showerror("Analysis Error", f"Error analyzing price sentiment: {str(e)}")
    
    def find_similar_patterns(self):
        """Find similar patterns in the historical data."""
        if self.is_closing:
            return
        
        if not self.selected_event:
            messagebox.showwarning("No Selection", "Please select an event to find similar patterns.")
            return
        
        try:
            # Get pattern matching parameters
            precision = self.precision_var.get()
            price_based = self.price_based_var.get()
            context_matching = self.context_matching_var.get()
            
            # Show progress dialog
            progress_window = tk.Toplevel(self.window)
            progress_window.title("Pattern Search")
            progress_window.geometry("400x150")
            progress_window.transient(self.window)
            progress_window.grab_set()
            
            ttk.Label(progress_window, text="Searching for similar patterns...", 
                     font=('Arial', 12)).pack(pady=20)
            progress_bar = ttk.Progressbar(progress_window, mode='indeterminate')
            progress_bar.pack(pady=10, padx=20, fill=tk.X)
            progress_bar.start()
            
            status_label = ttk.Label(progress_window, text="Initializing...")
            status_label.pack(pady=5)
            
            def search_patterns():
                try:
                    # Update status
                    def update_status(text):
                        if not progress_window.winfo_exists():
                            return
                        status_label.config(text=text)
                        progress_window.update()
                    
                    update_status("Analyzing event pattern...")
                    
                    # Get event date and surrounding data
                    if self.selected_event['type'] == 'single':
                        event_date = pd.to_datetime(self.selected_event['date'])
                        pattern_start = event_date - pd.Timedelta(days=10)
                        pattern_end = event_date + pd.Timedelta(days=10)
                    else:
                        pattern_start = pd.to_datetime(self.selected_event['start_date']) - pd.Timedelta(days=10)
                        pattern_end = pd.to_datetime(self.selected_event['end_date']) + pd.Timedelta(days=10)
                    
                    # Extract pattern data
                    pattern_data = self.df[(self.df.index >= pattern_start) & (self.df.index <= pattern_end)]
                    if pattern_data.empty:
                        raise ValueError("No data found for the event pattern")
                    
                    # Normalize pattern data for comparison
                    pattern_prices = pattern_data['close'].values
                    pattern_normalized = (pattern_prices - pattern_prices.min()) / (pattern_prices.max() - pattern_prices.min())
                    
                    update_status("Searching historical data...")
                    
                    # Search for similar patterns
                    similar_patterns = []
                    search_window_size = len(pattern_normalized)
                    
                    # Apply time frame restrictions if enabled
                    search_data = self.df.copy()
                    if self.custom_timeframe_var.get():
                        start_str = self.search_start_var.get()
                        end_str = self.search_end_var.get()
                        if start_str and end_str:
                            search_start = pd.to_datetime(start_str)
                            search_end = pd.to_datetime(end_str)
                            search_data = search_data[(search_data.index >= search_start) & (search_data.index <= search_end)]
                    
                    # Apply exclusions
                    for exclusion in self.pattern_exclusion_ranges:
                        excl_start = pd.to_datetime(exclusion['start_date'])
                        excl_end = pd.to_datetime(exclusion['end_date'])
                        search_data = search_data[~((search_data.index >= excl_start) & (search_data.index <= excl_end))]
                    
                    total_windows = len(search_data) - search_window_size + 1
                    processed = 0
                    
                    for i in range(0, len(search_data) - search_window_size + 1, 5):  # Skip every 5 for performance
                        if not progress_window.winfo_exists():
                            return
                        
                        processed += 1
                        if processed % 50 == 0:
                            update_status(f"Analyzing window {processed}/{total_windows//5}...")
                        
                        window_data = search_data.iloc[i:i+search_window_size]
                        window_prices = window_data['close'].values
                        
                        if len(window_prices) < search_window_size:
                            continue
                        
                        # Skip if this is the original event
                        window_start_date = window_data.index[0]
                        if abs((window_start_date - pattern_start).days) < 30:
                            continue
                        
                        # Normalize window data
                        if window_prices.max() == window_prices.min():
                            continue  # Skip flat periods
                        
                        window_normalized = (window_prices - window_prices.min()) / (window_prices.max() - window_prices.min())
                        
                        # Calculate similarity using correlation
                        correlation = np.corrcoef(pattern_normalized, window_normalized)[0, 1]
                        
                        if np.isnan(correlation):
                            continue
                        
                        # Check if correlation meets precision threshold
                        if correlation >= precision:
                            similarity_score = correlation
                            
                            # Additional context matching if enabled
                            if context_matching:
                                days_before_str = self.days_before_var.get()
                                days_after_str = self.days_after_var.get()
                                
                                context_score = 1.0
                                
                                if days_before_str:
                                    try:
                                        days_before = int(days_before_str)
                                        # Compare behavior before both events
                                        # Implementation would go here
                                    except ValueError:
                                        pass
                                
                                if days_after_str:
                                    try:
                                        days_after = int(days_after_str)
                                        # Compare behavior after both events
                                        # Implementation would go here
                                    except ValueError:
                                        pass
                                
                                similarity_score *= context_score
                            
                            similar_patterns.append({
                                'start_date': window_start_date,
                                'end_date': window_data.index[-1],
                                'similarity': similarity_score,
                                'start_price': window_prices[0],
                                'end_price': window_prices[-1],
                                'price_change': ((window_prices[-1] - window_prices[0]) / window_prices[0]) * 100
                            })
                    
                    # Sort by similarity
                    similar_patterns.sort(key=lambda x: x['similarity'], reverse=True)
                    
                    # Show results
                    def show_results():
                        if progress_window.winfo_exists():
                            progress_window.destroy()
                        
                        if not similar_patterns:
                            messagebox.showinfo("No Patterns Found", 
                                              f"No similar patterns found with precision threshold of {precision:.0%}")
                            return
                        
                        # Create results window
                        results_window = tk.Toplevel(self.window)
                        results_window.title("Similar Patterns Found")
                        results_window.geometry("800x600")
                        
                        main_frame = ttk.Frame(results_window, padding="10")
                        main_frame.pack(fill=tk.BOTH, expand=True)
                        
                        ttk.Label(main_frame, text=f"Similar Patterns to: {self.selected_event['label']}", 
                                 font=('Arial', 16, 'bold')).pack(pady=(0, 10))
                        
                        ttk.Label(main_frame, text=f"Found {len(similar_patterns)} patterns with {precision:.0%}+ similarity").pack(pady=(0, 10))
                        
                        # Results table
                        columns = ('similarity', 'start_date', 'end_date', 'price_change')
                        tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=15)
                        
                        tree.heading('similarity', text='Similarity')
                        tree.heading('start_date', text='Start Date')
                        tree.heading('end_date', text='End Date')
                        tree.heading('price_change', text='Price Change')
                        
                        tree.column('similarity', width=100)
                        tree.column('start_date', width=150)
                        tree.column('end_date', width=150)
                        tree.column('price_change', width=120)
                        
                        for pattern in similar_patterns[:50]:  # Show top 50 results
                            tree.insert('', tk.END, values=(
                                f"{pattern['similarity']:.1%}",
                                pattern['start_date'].strftime('%Y-%m-%d'),
                                pattern['end_date'].strftime('%Y-%m-%d'),
                                f"{pattern['price_change']:+.1f}%"
                            ))
                        
                        tree_scroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
                        tree.configure(yscrollcommand=tree_scroll.set)
                        
                        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                    
                    self.window.after(0, show_results)
                    
                except Exception as e:
                    def show_error():
                        if progress_window.winfo_exists():
                            progress_window.destroy()
                        messagebox.showerror("Search Error", f"Error during pattern search: {str(e)}")
                    
                    self.window.after(0, show_error)
            
            # Start search in background thread
            import threading
            threading.Thread(target=search_patterns, daemon=True).start()
            
        except Exception as e:
            print(f"Error in pattern search: {e}")
            messagebox.showerror("Search Error", f"Error starting pattern search: {str(e)}")
    
    def on_closing(self):
        """Handle window closing."""
        print("Closing AssetAnalysisWindow...")
        self.is_closing = True  # Set flag to prevent further operations
        
        try:
            # Unbind all events that might cause issues
            if hasattr(self, 'events_listbox') and self.events_listbox:
                try:
                    self.events_listbox.unbind('<<ListboxSelect>>')
                except:
                    pass
            
            if hasattr(self, 'exclusion_ranges_listbox') and self.exclusion_ranges_listbox:
                try:
                    self.exclusion_ranges_listbox.unbind_all()
                except:
                    pass
            
            # Clean up matplotlib
            if hasattr(self, 'fig'):
                try:
                    plt.close(self.fig)
                except:
                    pass
            
            # Destroy the window
            if hasattr(self, 'window') and self.window:
                try:
                    self.window.destroy()
                except:
                    pass
                    
        except Exception as e:
            print(f"Error during cleanup: {e}")
            # Force destroy if cleanup fails
            try:
                if hasattr(self, 'window'):
                    self.window.destroy()
            except:
                pass
