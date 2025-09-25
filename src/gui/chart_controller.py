import tkinter as tk
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time


class ChartController:
    """Handles all chart-related functionality for the asset analysis window."""
    
    def __init__(self, parent_window):
        """
        Initialize the chart controller.
        
        Args:
            parent_window: Reference to the main AssetAnalysisWindow instance
        """
        self.parent = parent_window
        self.fig = parent_window.fig
        self.ax = parent_window.ax
        self.canvas = parent_window.canvas
        
        # Chart data
        self.df = pd.DataFrame()  # Main price data
        self.market_cap_df = None  # Market cap data
        self.ax2 = None  # Secondary axis for market cap
        
        # Chart interaction variables
        self.zoom_enabled = True
        self.pan_enabled = True
        self.is_panning = False
        self.pan_start = None
        self.zoom_scale = 1.0
        
        # Crosshair variables for price highlighter
        self.crosshair_v = None
        self.crosshair_h = None
        self.price_info_text = None
        self.mouse_move_connected = False
        self.last_mouse_time = 0
        self.highlighter_enabled = True
        
        # Date range variables
        self.current_date_range = "all"
        self.custom_start_date = None
        self.custom_end_date = None
        
        # Connect chart events
        self.connect_chart_events()
    
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
    
    def load_chart_data(self):
        """Load and prepare chart data."""
        try:
            # Convert historical data to DataFrame
            self.df = pd.DataFrame(self.parent.asset_data['historical_data'])
            self.df['date'] = pd.to_datetime(self.df['date'], utc=True)
            self.df.set_index('date', inplace=True)
            self.df.index = self.df.index.tz_convert(None)  # Remove timezone
        except Exception as e:
            print(f"Error loading chart data: {e}")
            self.df = pd.DataFrame()  # Empty dataframe as fallback
    
    def update_chart(self):
        """Update the chart display."""
        if self.parent.is_closing or self.df.empty:
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
                self.ax.set_title(f"{self.parent.symbol} - No data for selected date range")
                self.canvas.draw()
                return
            
            # Check if we should show market cap
            show_market_cap = (hasattr(self.parent, 'show_market_cap_var') and 
                             self.parent.show_market_cap_var.get() and
                             self.parent.asset_type == "equities" and
                             self.parent.asset_data.get('market_cap_history'))
            
            # Clear or create secondary axis if needed
            if show_market_cap:
                if self.ax2 is None:
                    self.ax2 = self.ax.twinx()
            else:
                # Remove secondary axis if it exists and we don't need it
                if self.ax2 is not None:
                    self.ax2.remove()
                    self.ax2 = None
                self.market_cap_df = None
            
            # Plot price line
            line1 = self.ax.plot(filtered_df.index, filtered_df['close'], 
                        label=f"{self.parent.symbol} Price", linewidth=2, color='blue')
            
            # Plot market cap if enabled
            if show_market_cap and self.ax2:
                # Get market cap data and filter by date range
                market_cap_data = self.parent.asset_data['market_cap_history']
                market_cap_df = pd.DataFrame(market_cap_data)
                market_cap_df['date'] = pd.to_datetime(market_cap_df['date'], utc=True)
                market_cap_df.set_index('date', inplace=True)
                
                # Convert to timezone-naive to match price data
                market_cap_df.index = market_cap_df.index.tz_convert(None)
                
                # Filter market cap data to match the price data date range
                filtered_market_cap = market_cap_df[
                    (market_cap_df.index >= filtered_df.index.min()) & 
                    (market_cap_df.index <= filtered_df.index.max())
                ]
                
                if not filtered_market_cap.empty:
                    # Store for use in crosshair
                    self.market_cap_df = filtered_market_cap
                    
                    line2 = self.ax2.plot(filtered_market_cap.index, filtered_market_cap['market_cap_billions'], 
                            label=f"{self.parent.symbol} Market Cap", linewidth=2, color='green', alpha=0.7)
                    self.ax2.set_ylabel("Market Cap (Billions $)", color='green')
                    self.ax2.tick_params(axis='y', labelcolor='green')
                else:
                    print("No market cap data found for the selected date range")
                    self.market_cap_df = None
            
            # Plot events as vertical lines
            for event in self.parent.events:
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
            date_info = self._get_date_info_string()
            title = f"{self.parent.symbol} Price Chart{date_info}"
            if show_market_cap:
                title += " with Market Cap"
            self.ax.set_title(title)
            
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price ($)", color='blue')
            self.ax.tick_params(axis='y', labelcolor='blue')
            
            # Combine legends if we have both price and market cap
            if show_market_cap and self.ax2:
                # Get handles and labels from both axes
                lines1, labels1 = self.ax.get_legend_handles_labels()
                lines2, labels2 = self.ax2.get_legend_handles_labels()
                self.ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            else:
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
            if self.parent.highlighter_var.get():
                self.mouse_move_connected = True
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating chart: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_date_info_string(self):
        """Get date info string for chart title."""
        date_info = ""
        if self.current_date_range != "all":
            if self.current_date_range == "custom":
                if self.custom_start_date and self.custom_end_date:
                    date_info = f" ({self.custom_start_date.strftime('%Y-%m-%d')} to {self.custom_end_date.strftime('%Y-%m-%d')})"
            else:
                date_info = f" (Last {self.current_date_range.upper()})"
        return date_info
    
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
    
    def on_date_range_change(self, event=None):
        """Handle date range selection change."""
        self.current_date_range = self.parent.date_range_var.get()
        
        if self.current_date_range == "custom":
            self.parent.custom_date_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.parent.custom_date_frame.pack_forget()
            # Apply non-custom date range immediately
            self.update_chart()
    
    def on_custom_date_change(self, event=None):
        """Handle custom date entry changes."""
        if self.current_date_range == "custom":
            # Only update if both dates are entered and valid
            start_str = self.parent.start_date_var.get()
            end_str = self.parent.end_date_var.get()
            
            if start_str and end_str:
                try:
                    self.custom_start_date = pd.to_datetime(start_str).tz_localize(None)
                    self.custom_end_date = pd.to_datetime(end_str).tz_localize(None)
                    self.update_chart()
                except (ValueError, TypeError):
                    pass  # Invalid date format, don't update
    
    # Mouse and keyboard interaction methods
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
        # Check if mouse is in either axis (primary or secondary)
        if event.inaxes != self.ax and event.inaxes != self.ax2:
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
        if not self.highlighter_enabled:
            return
        
        # Work with whichever axis the mouse is in
        if event.inaxes != self.ax and event.inaxes != self.ax2:
            return
        
        # Performance throttling
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
            
            # Draw new crosshair - always on primary axis
            self.crosshair_v = self.ax.axvline(event.xdata, color='red', alpha=0.7, linestyle='--')
            self.crosshair_h = self.ax.axhline(event.ydata, color='red', alpha=0.7, linestyle='--')
            
            # Get closest data point
            if not self.df.empty:
                mouse_date = pd.to_datetime(event.xdata, origin='unix', unit='D')
                
                # Find closest date
                closest_idx = self.df.index.get_indexer([mouse_date], method='nearest')[0]
                if 0 <= closest_idx < len(self.df):
                    closest_date = self.df.index[closest_idx]
                    closest_row = self.df.iloc[closest_idx]
                    
                    # Create info text with price data
                    info_text = f"Date: {closest_date.strftime('%Y-%m-%d')}\n"
                    info_text += f"Open: ${closest_row['open']:.2f}\n"
                    info_text += f"High: ${closest_row['high']:.2f}\n"
                    info_text += f"Low: ${closest_row['low']:.2f}\n"
                    info_text += f"Close: ${closest_row['close']:.2f}\n"
                    if pd.notna(closest_row['volume']):
                        info_text += f"Volume: {closest_row['volume']:,}\n"
                    
                    # Add market cap info if available
                    if self.market_cap_df is not None and not self.market_cap_df.empty:
                        try:
                            # Find closest market cap date
                            mc_idx = self.market_cap_df.index.get_indexer([closest_date], method='nearest')[0]
                            if 0 <= mc_idx < len(self.market_cap_df):
                                mc_row = self.market_cap_df.iloc[mc_idx]
                                info_text += f"\nMarket Cap: ${mc_row['market_cap_billions']:.2f}B"
                        except Exception as e:
                            print(f"Error getting market cap for crosshair: {e}")
                    
                    # Position info box - move down if market cap is displayed to avoid legend
                    y_position = 0.90 if self.market_cap_df is not None else 0.98
                    
                    # Position info box
                    self.price_info_text = self.ax.text(
                        0.02, y_position, info_text,
                        transform=self.ax.transAxes,
                        fontsize=10,
                        verticalalignment='top',
                        horizontalalignment='left',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9, edgecolor='black'),
                        family='monospace'
                    )
            
            self.canvas.draw_idle()
            
        except Exception as e:
            print(f"Error updating crosshair: {e}")
            pass  # Silently handle errors to avoid disrupting mouse movement
    
    def toggle_highlighter(self):
        """Toggle the price highlighter on/off."""
        self.highlighter_enabled = self.parent.highlighter_var.get()
        
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
    
    # Zoom control methods
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
            if not self.df.empty:
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
    
    def cleanup(self):
        """Clean up chart controller resources."""
        try:
            # Clear crosshair elements
            if self.crosshair_v:
                try:
                    self.crosshair_v.remove()
                except:
                    pass
            if self.crosshair_h:
                try:
                    self.crosshair_h.remove()
                except:
                    pass
            if self.price_info_text:
                try:
                    self.price_info_text.remove()
                except:
                    pass
            
            # Remove secondary axis if it exists
            if self.ax2:
                try:
                    self.ax2.remove()
                except:
                    pass
            
            # Disconnect mouse events
            self.mouse_move_connected = False
            
            print("ChartController cleaned up successfully")
            
        except Exception as e:
            print(f"Error during ChartController cleanup: {e}")
