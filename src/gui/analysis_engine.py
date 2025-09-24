import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading


class AnalysisEngine:
    """Handles all analysis functionality for the asset analysis window."""
    
    def __init__(self, parent_window):
        """
        Initialize the analysis engine.
        
        Args:
            parent_window: Reference to the main AssetAnalysisWindow instance
        """
        self.parent = parent_window
        
        # Get reference to chart data through chart controller
        self.chart_controller = None  # Will be set after chart controller is initialized
        
    def set_chart_controller(self, chart_controller):
        """Set reference to chart controller for data access."""
        self.chart_controller = chart_controller
    
    @property
    def df(self):
        """Get chart data from chart controller."""
        if self.chart_controller:
            return self.chart_controller.df
        return pd.DataFrame()
    
    # Event management methods
    def on_event_select(self, event):
        """Handle event selection."""
        if self.parent.is_closing or not self.parent.events_listbox:
            return
        
        try:
            selection = self.parent.events_listbox.curselection()
            if selection:
                self.parent.selected_event = self.parent.events[selection[0]]
            else:
                self.parent.selected_event = None
        except Exception as e:
            print(f"Error handling event selection: {e}")
    
    def add_event(self):
        """Add a single date event."""
        if self.parent.is_closing:
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
            
            self.parent.events.append(event)
            self.parent.save_events()
            self.parent.populate_events_list()
            if hasattr(self.parent, 'chart_controller'):
                self.parent.chart_controller.update_chart()
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter a valid date in YYYY-MM-DD format.")
        except Exception as e:
            print(f"Error adding event: {e}")
    
    def add_range_event(self):
        """Add a date range event."""
        if self.parent.is_closing:
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
            
            self.parent.events.append(event)
            self.parent.save_events()
            self.parent.populate_events_list()
            if hasattr(self.parent, 'chart_controller'):
                self.parent.chart_controller.update_chart()
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter valid dates in YYYY-MM-DD format.")
        except Exception as e:
            print(f"Error adding range event: {e}")
    
    def edit_event(self):
        """Edit selected event."""
        if self.parent.is_closing or not self.parent.events_listbox:
            return
        
        try:
            selection = self.parent.events_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an event to edit.")
                return
            
            # For now, just allow editing the label
            event_idx = selection[0]
            event = self.parent.events[event_idx]
            
            new_label = simpledialog.askstring("Edit Event", "Enter new event description:", 
                                              initialvalue=event['label'])
            if new_label:
                self.parent.events[event_idx]['label'] = new_label
                self.parent.save_events()
                self.parent.populate_events_list()
                if hasattr(self.parent, 'chart_controller'):
                    self.parent.chart_controller.update_chart()
        except Exception as e:
            print(f"Error editing event: {e}")
    
    def delete_event(self):
        """Delete selected event."""
        if self.parent.is_closing or not self.parent.events_listbox:
            return
        
        try:
            selection = self.parent.events_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an event to delete.")
                return
            
            event_idx = selection[0]
            event = self.parent.events[event_idx]
            
            result = messagebox.askyesno("Confirm Delete", 
                                       f"Delete event '{event['label']}'?")
            if result:
                del self.parent.events[event_idx]
                self.parent.save_events()
                self.parent.populate_events_list()
                if hasattr(self.parent, 'chart_controller'):
                    self.parent.chart_controller.update_chart()
        except Exception as e:
            print(f"Error deleting event: {e}")
    
    # Event analysis methods
    def analyze_selected_event(self):
        """Analyze the impact of the selected event."""
        if self.parent.is_closing or not self.parent.selected_event:
            if not self.parent.selected_event:
                messagebox.showwarning("No Selection", "Please select an event to analyze.")
            return
        
        try:
            timespan = self.parent.timespan_var.get()
            
            # Get event date(s)
            if self.parent.selected_event['type'] == 'single':
                event_date = pd.to_datetime(self.parent.selected_event['date'])
                analysis_start = event_date
            else:  # range
                event_start = pd.to_datetime(self.parent.selected_event['start_date'])
                event_end = pd.to_datetime(self.parent.selected_event['end_date'])
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
                self.parent.analysis_text.delete(1.0, tk.END)
                self.parent.analysis_text.insert(tk.END, "No data available for the analysis period.")
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
            analysis = f"""Event Analysis: {self.parent.selected_event['label']}
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
            
            self.parent.analysis_text.delete(1.0, tk.END)
            self.parent.analysis_text.insert(tk.END, analysis)
            
        except Exception as e:
            print(f"Error analyzing event: {e}")
            messagebox.showerror("Analysis Error", f"Error analyzing event: {str(e)}")
    
    def compare_multiple_events(self):
        """Compare multiple events side by side."""
        if self.parent.is_closing:
            return
        
        if not self.parent.events:
            messagebox.showwarning("No Events", "Please add some events first.")
            return
        
        try:
            comparison_window = tk.Toplevel(self.parent.window)
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
            comparison_report = f"Event Comparison Report for {self.parent.symbol}\n"
            comparison_report += "=" * 60 + "\n\n"
            
            for i, event in enumerate(self.parent.events):
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
    
    # Price sentiment analysis methods
    def analyze_price_sentiment(self):
        """Analyze market sentiment at similar price levels to the selected event."""
        if self.parent.is_closing:
            return
        
        if not self.parent.selected_event:
            messagebox.showwarning("No Selection", "Please select an event to analyze price sentiment.")
            return
        
        if not self.parent.sentiment_analysis_var.get():
            messagebox.showwarning("Feature Disabled", "Please enable 'Analyze market sentiment at similar price levels' first.")
            return
        
        try:
            # Get event price
            if self.parent.selected_event['type'] == 'single':
                event_date = pd.to_datetime(self.parent.selected_event['date'])
                event_price_data = self.df[self.df.index == event_date]
                if event_price_data.empty:
                    # Find closest date
                    closest_idx = self.df.index.get_indexer([event_date], method='nearest')[0]
                    event_price = self.df.iloc[closest_idx]['close']
                else:
                    event_price = event_price_data['close'].iloc[0]
            else:  # range
                event_start = pd.to_datetime(self.parent.selected_event['start_date'])
                event_end = pd.to_datetime(self.parent.selected_event['end_date'])
                range_data = self.df[(self.df.index >= event_start) & (self.df.index <= event_end)]
                if range_data.empty:
                    messagebox.showwarning("No Data", "No price data found for the selected event range.")
                    return
                event_price = range_data['close'].mean()  # Use average price during range
            
            # Get tolerance settings
            try:
                price_tolerance = float(self.parent.price_tolerance_var.get()) / 100
                min_occurrences = int(self.parent.min_occurrences_var.get())
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
                try:
                    future_dates = self.df[self.df.index > date].head(5)  # Next 5 days
                    if not future_dates.empty:
                        start_price_reaction = float(row['close'])
                        end_price_reaction = float(future_dates['close'].iloc[-1])
                        reaction_pct = ((end_price_reaction - start_price_reaction) / start_price_reaction) * 100
                        reactions.append({
                            'date': date,
                            'price': start_price_reaction,
                            'reaction_pct': reaction_pct,
                            'reaction_direction': 'Positive' if reaction_pct > 1 else 'Negative' if reaction_pct < -1 else 'Neutral'
                        })
                except (ValueError, TypeError, KeyError) as reaction_error:
                    # Skip this reaction if there's a data type issue
                    print(f"Skipping reaction analysis for {date}: {reaction_error}")
                    continue
            
            if not reactions:
                messagebox.showinfo("No Reactions", "No reaction data found for similar price levels.")
                return
            
            # Calculate sentiment statistics
            positive_reactions = [r for r in reactions if r['reaction_direction'] == 'Positive']
            negative_reactions = [r for r in reactions if r['reaction_direction'] == 'Negative']
            neutral_reactions = [r for r in reactions if r['reaction_direction'] == 'Neutral']
            
            avg_reaction = np.mean([r['reaction_pct'] for r in reactions])
            
            # Create sentiment analysis window
            self._show_sentiment_analysis_window(event_price, price_range_min, price_range_max, 
                                               price_tolerance, reactions, positive_reactions, 
                                               negative_reactions, neutral_reactions, avg_reaction)
            
        except Exception as e:
            print(f"Error in price sentiment analysis: {e}")
            messagebox.showerror("Analysis Error", f"Error analyzing price sentiment: {str(e)}")
    
    def _show_sentiment_analysis_window(self, event_price, price_range_min, price_range_max,
                                      price_tolerance, reactions, positive_reactions,
                                      negative_reactions, neutral_reactions, avg_reaction):
        """Show the sentiment analysis results window."""
        sentiment_window = tk.Toplevel(self.parent.window)
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
        sentiment_report = f"""Price Sentiment Analysis for {self.parent.symbol}
Event: {self.parent.selected_event['label']}
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
    
    # Pattern matching methods
    def find_similar_patterns(self):
        """Find similar patterns in the historical data."""
        if self.parent.is_closing:
            return
        
        if not self.parent.selected_event:
            messagebox.showwarning("No Selection", "Please select an event to find similar patterns.")
            return
        
        try:
            # Get pattern matching parameters
            precision = self.parent.precision_var.get()
            price_based = self.parent.price_based_var.get()
            context_matching = self.parent.context_matching_var.get()
            
            # Show progress dialog
            progress_window = tk.Toplevel(self.parent.window)
            progress_window.title("Pattern Search")
            progress_window.geometry("400x150")
            progress_window.transient(self.parent.window)
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
                    similar_patterns = self._search_similar_patterns(precision, price_based, 
                                                                   context_matching, progress_window, 
                                                                   status_label)
                    
                    # Show results
                    def show_results():
                        if progress_window.winfo_exists():
                            progress_window.destroy()
                        
                        if not similar_patterns:
                            messagebox.showinfo("No Patterns Found", 
                                              f"No similar patterns found with precision threshold of {precision:.0%}")
                            return
                        
                        self._show_pattern_results_window(similar_patterns, precision)
                    
                    self.parent.window.after(0, show_results)
                    
                except Exception as search_error:
                    def show_error():
                        if progress_window.winfo_exists():
                            progress_window.destroy()
                        messagebox.showerror("Search Error", f"Error during pattern search: {str(search_error)}")
                    
                    self.parent.window.after(0, show_error)
            
            # Start search in background thread
            threading.Thread(target=search_patterns, daemon=True).start()
            
        except Exception as e:
            print(f"Error in pattern search: {e}")
            messagebox.showerror("Search Error", f"Error starting pattern search: {str(e)}")
    
    def _search_similar_patterns(self, precision, price_based, context_matching, 
                               progress_window, status_label):
        """Perform the actual pattern search."""
        # Update status
        def update_status(text):
            if not progress_window.winfo_exists():
                return
            status_label.config(text=text)
            progress_window.update()
        
        update_status("Analyzing event pattern...")
        
        # Get event date and surrounding data
        if self.parent.selected_event['type'] == 'single':
            event_date = pd.to_datetime(self.parent.selected_event['date'])
            pattern_start = event_date - pd.Timedelta(days=10)
            pattern_end = event_date + pd.Timedelta(days=10)
        else:
            pattern_start = pd.to_datetime(self.parent.selected_event['start_date']) - pd.Timedelta(days=10)
            pattern_end = pd.to_datetime(self.parent.selected_event['end_date']) + pd.Timedelta(days=10)
        
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
        if self.parent.custom_timeframe_var.get():
            start_str = self.parent.search_start_var.get()
            end_str = self.parent.search_end_var.get()
            
            # Apply "after" date filter (search_start = after this date)
            if start_str:
                try:
                    search_after = pd.to_datetime(start_str)
                    search_data = search_data[search_data.index > search_after]
                    print(f"Filtered data AFTER {search_after}: {len(search_data)} records remaining")
                except (ValueError, TypeError) as e:
                    print(f"Invalid 'after' date format: {start_str}, error: {e}")
            
            # Apply "before" date filter (search_end = before this date)  
            if end_str:
                try:
                    search_before = pd.to_datetime(end_str)
                    search_data = search_data[search_data.index < search_before]
                    print(f"Filtered data BEFORE {search_before}: {len(search_data)} records remaining")
                except (ValueError, TypeError) as e:
                    print(f"Invalid 'before' date format: {end_str}, error: {e}")
            
            print(f"Final search data range: {search_data.index.min()} to {search_data.index.max()}")
        else:
            print(f"Using full dataset: {len(search_data)} records")
        
        # Apply exclusions
        for exclusion in self.parent.pattern_exclusion_ranges:
            excl_start = pd.to_datetime(exclusion['start_date'])
            excl_end = pd.to_datetime(exclusion['end_date'])
            search_data = search_data[~((search_data.index >= excl_start) & (search_data.index <= excl_end))]
        
        total_windows = len(search_data) - search_window_size + 1
        processed = 0
        
        for i in range(0, len(search_data) - search_window_size + 1, 5):  # Skip every 5 for performance
            if not progress_window.winfo_exists():
                return []
            
            processed += 1
            if processed % 50 == 0:
                update_status(f"Analyzing window {processed}/{total_windows//5}...")
            
            window_data = search_data.iloc[i:i+search_window_size]
            window_prices = window_data['close'].values
            
            if len(window_prices) < search_window_size:
                continue
            
            # Skip if this is the original event
            window_start_date = window_data.index[0]
            window_end_date = window_data.index[-1]
            
            # Skip if this is the original event (within 30 days of pattern)
            if abs((window_start_date - pattern_start).days) < 30:
                continue
            
            # Additional check: ensure the window is actually within our search timeframe
            # This is a double-check in case the filtering above missed something
            if self.parent.custom_timeframe_var.get():
                start_str = self.parent.search_start_var.get()
                end_str = self.parent.search_end_var.get()
                
                # Check "after" constraint
                if start_str:
                    try:
                        search_after = pd.to_datetime(start_str)
                        if window_end_date <= search_after:  # Window ends before our "after" date
                            continue
                    except:
                        pass
                
                # Check "before" constraint  
                if end_str:
                    try:
                        search_before = pd.to_datetime(end_str)
                        if window_start_date >= search_before:  # Window starts after our "before" date
                            continue
                    except:
                        pass
            
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
                    days_before_str = self.parent.days_before_var.get()
                    days_after_str = self.parent.days_after_var.get()
                    
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
        
        return similar_patterns
    
    def _show_pattern_results_window(self, similar_patterns, precision):
        """Show the pattern matching results window."""
        # Create results window
        results_window = tk.Toplevel(self.parent.window)
        results_window.title("Similar Patterns Found")
        results_window.geometry("800x700")  # Made taller for additional stats
        
        main_frame = ttk.Frame(results_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=f"Similar Patterns to: {self.parent.selected_event['label']}", 
                 font=('Arial', 16, 'bold')).pack(pady=(0, 10))
        
        ttk.Label(main_frame, text=f"Found {len(similar_patterns)} patterns with {precision:.0%}+ similarity").pack(pady=(0, 5))
        
        # Calculate statistics for top 10 patterns
        top_10_patterns = similar_patterns[:10]
        if len(top_10_patterns) > 0:
            price_changes = [pattern['price_change'] for pattern in top_10_patterns]
            
            # Calculate statistics
            average_change = np.mean(price_changes)
            median_change = np.median(price_changes)
            min_change = min(price_changes)
            max_change = max(price_changes)
            
            # Create statistics frame
            stats_frame = ttk.LabelFrame(main_frame, text=f"Statistics for Top {len(top_10_patterns)} Most Similar Patterns", padding="10")
            stats_frame.pack(fill=tk.X, pady=(5, 10))
            
            # Create two columns for stats
            stats_left = ttk.Frame(stats_frame)
            stats_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            stats_right = ttk.Frame(stats_frame)
            stats_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
            
            # Left column stats
            ttk.Label(stats_left, text=f"Average Price Change: {average_change:+.2f}%", 
                     font=('Arial', 10, 'bold')).pack(anchor=tk.W)
            ttk.Label(stats_left, text=f"Median Price Change: {median_change:+.2f}%", 
                     font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(2, 0))
            
            # Right column stats
            ttk.Label(stats_right, text=f"Range: {min_change:+.2f}% to {max_change:+.2f}%", 
                     font=('Arial', 10)).pack(anchor=tk.W)
            
            # Interpretation
            if average_change > 2:
                interpretation = "📈 Historically bullish pattern"
                color = "green"
            elif average_change < -2:
                interpretation = "📉 Historically bearish pattern" 
                color = "red"
            else:
                interpretation = "📊 Historically neutral pattern"
                color = "blue"
            
            ttk.Label(stats_left, text=interpretation, 
                     font=('Arial', 10, 'italic'), foreground=color).pack(anchor=tk.W, pady=(5, 0))
        
        # Results table
        table_frame = ttk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        ttk.Label(table_frame, text="Pattern Search Results:", 
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        columns = ('rank', 'similarity', 'start_date', 'end_date', 'price_change')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        
        tree.heading('rank', text='Rank')
        tree.heading('similarity', text='Similarity')
        tree.heading('start_date', text='Start Date')
        tree.heading('end_date', text='End Date')
        tree.heading('price_change', text='Price Change')
        
        tree.column('rank', width=60)
        tree.column('similarity', width=100)
        tree.column('start_date', width=120)
        tree.column('end_date', width=120)
        tree.column('price_change', width=120)
        
        # Insert patterns with ranking
        for i, pattern in enumerate(similar_patterns[:50], 1):  # Show top 50 results
            # Highlight top 10 patterns used for statistics
            tags = ('top10',) if i <= 10 else ()
            
            tree.insert('', tk.END, values=(
                f"#{i}",
                f"{pattern['similarity']:.1%}",
                pattern['start_date'].strftime('%Y-%m-%d'),
                pattern['end_date'].strftime('%Y-%m-%d'),
                f"{pattern['price_change']:+.1f}%"
            ), tags=tags)
        
        # Style the top 10 rows
        tree.tag_configure('top10', background='lightblue')
        
        tree_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=tree_scroll.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add note about highlighted rows
        note_frame = ttk.Frame(main_frame)
        note_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Label(note_frame, text="💡 Blue highlighted rows are the top 10 patterns used for statistics", 
                 font=('Arial', 9, 'italic')).pack(anchor=tk.W)
    
    # Exclusion range management methods
    def add_exclusion_range(self):
        """Add a time range to exclude from pattern matching."""
        if self.parent.is_closing:
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
            
            self.parent.pattern_exclusion_ranges.append(exclusion)
            self.parent.update_exclusion_ranges_list()
            
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter valid dates in YYYY-MM-DD format.")
    
    def remove_exclusion_range(self):
        """Remove selected exclusion range."""
        if self.parent.is_closing or not self.parent.exclusion_ranges_listbox:
            return
        
        try:
            selection = self.parent.exclusion_ranges_listbox.curselection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an exclusion range to remove.")
                return
            
            index = selection[0]
            if 0 <= index < len(self.parent.pattern_exclusion_ranges):
                del self.parent.pattern_exclusion_ranges[index]
                self.parent.update_exclusion_ranges_list()
        except Exception as e:
            print(f"Error removing exclusion range: {e}")
    
    # Control toggle methods
    def toggle_context_controls(self):
        """Enable/disable context matching controls based on checkbox."""
        if self.parent.is_closing:
            return
        
        try:
            if self.parent.context_matching_var.get():
                # Enable the entry fields
                self.parent.days_before_entry.config(state='normal')
                self.parent.days_after_entry.config(state='normal')
            else:
                # Disable the entry fields and clear them
                self.parent.days_before_entry.config(state='disabled')
                self.parent.days_after_entry.config(state='disabled')
                self.parent.days_before_var.set('')
                self.parent.days_after_var.set('')
        except Exception as e:
            print(f"Error toggling context controls: {e}")
    
    def toggle_sentiment_controls(self):
        """Enable/disable sentiment analysis controls based on checkbox."""
        if self.parent.is_closing:
            return
        
        try:
            if self.parent.sentiment_analysis_var.get():
                # Enable the entry fields
                for widget in self.parent.sentiment_controls.winfo_children():
                    self._enable_widget_tree(widget)
            else:
                # Disable the entry fields
                for widget in self.parent.sentiment_controls.winfo_children():
                    self._disable_widget_tree(widget)
        except Exception as e:
            print(f"Error toggling sentiment controls: {e}")
    
    def toggle_timeframe_controls(self):
        """Enable/disable timeframe controls based on checkbox."""
        if self.parent.is_closing:
            return
        
        try:
            if self.parent.custom_timeframe_var.get():
                # Enable the entry fields
                self.parent.search_start_entry.config(state='normal')
                self.parent.search_end_entry.config(state='normal')
            else:
                # Disable the entry fields and clear them
                self.parent.search_start_entry.config(state='disabled')
                self.parent.search_end_entry.config(state='disabled')
                self.parent.search_start_var.set('')
                self.parent.search_end_var.set('')
        except Exception as e:
            print(f"Error toggling timeframe controls: {e}")
    
    def _enable_widget_tree(self, widget):
        """Recursively enable a widget and its children."""
        if self.parent.is_closing:
            return
        try:
            widget.config(state='normal')
        except:
            pass
        try:
            for child in widget.winfo_children():
                self._enable_widget_tree(child)
        except:
            pass
    
    def _disable_widget_tree(self, widget):
        """Recursively disable a widget and its children."""
        if self.parent.is_closing:
            return
        try:
            widget.config(state='disabled')
        except:
            pass
        try:
            for child in widget.winfo_children():
                self._disable_widget_tree(child)
        except:
            pass
    
    def cleanup(self):
        """Clean up analysis engine resources."""
        try:
            # Clear any references
            self.chart_controller = None
            
            print("AnalysisEngine cleaned up successfully")
            
        except Exception as e:
            print(f"Error during AnalysisEngine cleanup: {e}")
