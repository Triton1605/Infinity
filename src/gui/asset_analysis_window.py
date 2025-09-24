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
from .chart_controller import ChartController
from .analysis_engine import AnalysisEngine


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
        
        # Initialize exclusion ranges
        self.pattern_exclusion_ranges = []
        
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Asset Analysis - {symbol}")
        self.window.geometry("1200x800")  # Reasonable default size
        
        # Initialize widgets to None to track their state
        self.tree = None
        self.events_listbox = None
        self.exclusion_ranges_listbox = None
        
        self.setup_gui()
        
        # Initialize controllers after GUI is set up
        self.chart_controller = ChartController(self)
        self.analysis_engine = AnalysisEngine(self)
        
        # Set cross-references between controllers
        self.analysis_engine.set_chart_controller(self.chart_controller)
        
        # Load and display chart
        self.chart_controller.load_chart_data()
        self.chart_controller.update_chart()
        
        # Populate initial data
        self.populate_events_list()
        
        # Handle window closing
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
    
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
            
            self.setup_asset_info_section(scrollable_frame)
            self.setup_chart_controls_section(scrollable_frame)
            self.setup_events_section(scrollable_frame)
            self.setup_analysis_section(scrollable_frame)
            self.setup_pattern_matching_section(scrollable_frame)
            
        except Exception as e:
            print(f"Error setting up left panel: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_asset_info_section(self, parent):
        """Set up asset information section."""
        info_frame = ttk.LabelFrame(parent, text="Asset Information", padding="10")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(info_frame, text=f"Symbol: {self.symbol}", font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Type: {self.asset_type.title()}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Company: {self.asset_data.get('company_name', 'Unknown')}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Latest Price: ${self.asset_data.get('latest_price', 'N/A')}").pack(anchor=tk.W)
    
    def setup_chart_controls_section(self, parent):
        """Set up chart controls section."""
        chart_controls_frame = ttk.LabelFrame(parent, text="Chart Controls", padding="10")
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
    
    def setup_events_section(self, parent):
        """Set up events section."""
        events_frame = ttk.LabelFrame(parent, text="Significant Events", padding="10")
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
    
    def setup_analysis_section(self, parent):
        """Set up analysis section."""
        analysis_frame = ttk.LabelFrame(parent, text="Event Analysis", padding="10")
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
    
    def setup_pattern_matching_section(self, parent):
        """Set up pattern matching section."""
        pattern_frame = ttk.LabelFrame(parent, text="Pattern Matching", padding="10")
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
        
        # Create subsections for pattern matching
        self.setup_context_matching_section(pattern_frame)
        self.setup_sentiment_analysis_section(pattern_frame)
        self.setup_timeframe_section(pattern_frame)
        self.setup_exclusion_section(pattern_frame)
        
        # Search buttons
        search_button_frame = ttk.Frame(pattern_frame)
        search_button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(search_button_frame, text="Find Similar Patterns", 
                  command=self.safe_find_similar_patterns).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(search_button_frame, text="Analyze Price Sentiment", 
                  command=self.safe_analyze_price_sentiment).pack(side=tk.LEFT)
    
    def setup_context_matching_section(self, parent):
        """Set up context matching controls."""
        context_frame = ttk.LabelFrame(parent, text="Event Context Matching", padding="5")
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
    
    def setup_sentiment_analysis_section(self, parent):
        """Set up sentiment analysis controls."""
        sentiment_frame = ttk.LabelFrame(parent, text="Price-Based Sentiment Analysis", padding="5")
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
    
    def setup_timeframe_section(self, parent):
        """Set up timeframe controls."""
        time_frame_frame = ttk.LabelFrame(parent, text="Search Time Frame", padding="5")
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
        ttk.Label(self.timeframe_controls, text="After:").pack(anchor=tk.W)
        self.search_start_var = tk.StringVar()
        start_entry_frame = ttk.Frame(self.timeframe_controls)
        start_entry_frame.pack(fill=tk.X, pady=(2, 5))
        self.search_start_entry = ttk.Entry(start_entry_frame, textvariable=self.search_start_var)
        self.search_start_entry.pack(fill=tk.X)
        
        # End date - stack vertically
        ttk.Label(self.timeframe_controls, text="Before:").pack(anchor=tk.W)
        self.search_end_var = tk.StringVar()
        end_entry_frame = ttk.Frame(self.timeframe_controls)
        end_entry_frame.pack(fill=tk.X, pady=(2, 5))
        self.search_end_entry = ttk.Entry(end_entry_frame, textvariable=self.search_end_var)
        self.search_end_entry.pack(fill=tk.X)
        
        # Help text
        ttk.Label(self.timeframe_controls, text="Format: YYYY-MM-DD (leave empty for all data)", 
                 font=('Arial', 8), foreground='gray').pack(anchor=tk.W)
    
    def setup_exclusion_section(self, parent):
        """Set up exclusion ranges section."""
        exclusion_frame = ttk.LabelFrame(parent, text="Exclude Time Periods", padding="5")
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
        
        # Initially disable timeframe controls
        self.toggle_timeframe_controls()
    
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
            
            # Initial chart
            self.ax.set_title(f"{self.symbol} Price Chart")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price ($)")
            self.canvas.draw()
        except Exception as e:
            print(f"Error setting up chart: {e}")
    
    # Event handling methods (delegate to controllers)
    def on_date_range_change(self, event=None):
        """Handle date range selection change."""
        if hasattr(self, 'chart_controller'):
            self.chart_controller.on_date_range_change(event)
    
    def on_custom_date_change(self, event=None):
        """Handle custom date entry changes."""
        if hasattr(self, 'chart_controller'):
            self.chart_controller.on_custom_date_change(event)
    
    def toggle_highlighter(self):
        """Toggle the price highlighter on/off."""
        if hasattr(self, 'chart_controller'):
            self.chart_controller.toggle_highlighter()
    
    def zoom_in(self):
        """Zoom in by a fixed factor."""
        if hasattr(self, 'chart_controller'):
            self.chart_controller.zoom_in()
    
    def zoom_out(self):
        """Zoom out by a fixed factor."""
        if hasattr(self, 'chart_controller'):
            self.chart_controller.zoom_out()
    
    def reset_zoom(self):
        """Reset zoom to show all data."""
        if hasattr(self, 'chart_controller'):
            self.chart_controller.reset_zoom()
    
    def toggle_context_controls(self):
        """Enable/disable context matching controls based on checkbox."""
        if hasattr(self, 'analysis_engine'):
            self.analysis_engine.toggle_context_controls()
    
    def toggle_sentiment_controls(self):
        """Enable/disable sentiment analysis controls based on checkbox."""
        if hasattr(self, 'analysis_engine'):
            self.analysis_engine.toggle_sentiment_controls()
    
    def toggle_timeframe_controls(self):
        """Enable/disable timeframe controls based on checkbox."""
        if hasattr(self, 'analysis_engine'):
            self.analysis_engine.toggle_timeframe_controls()
    
    # Safe wrapper methods to prevent errors during window closing
    def safe_on_event_select(self, event):
        """Safe wrapper for on_event_select."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.on_event_select(event)
    
    def safe_add_event(self):
        """Safe wrapper for add_event."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.add_event()
    
    def safe_add_range_event(self):
        """Safe wrapper for add_range_event."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.add_range_event()
    
    def safe_edit_event(self):
        """Safe wrapper for edit_event."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.edit_event()
    
    def safe_delete_event(self):
        """Safe wrapper for delete_event."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.delete_event()
    
    def safe_analyze_selected_event(self):
        """Safe wrapper for analyze_selected_event."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.analyze_selected_event()
    
    def safe_compare_multiple_events(self):
        """Safe wrapper for compare_multiple_events."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.compare_multiple_events()
    
    def safe_add_exclusion_range(self):
        """Safe wrapper for add_exclusion_range."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.add_exclusion_range()
    
    def safe_remove_exclusion_range(self):
        """Safe wrapper for remove_exclusion_range."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.remove_exclusion_range()
    
    def safe_find_similar_patterns(self):
        """Safe wrapper for find_similar_patterns."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.find_similar_patterns()
    
    def safe_analyze_price_sentiment(self):
        """Safe wrapper for analyze_price_sentiment."""
        if not self.is_closing and hasattr(self, 'analysis_engine'):
            self.analysis_engine.analyze_price_sentiment()
    
    # Event and data management methods
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
            
            # Clean up controllers
            if hasattr(self, 'chart_controller'):
                try:
                    self.chart_controller.cleanup()
                except:
                    pass
            
            if hasattr(self, 'analysis_engine'):
                try:
                    self.analysis_engine.cleanup()
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
