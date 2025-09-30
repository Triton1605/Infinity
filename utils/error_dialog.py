"""
Custom error dialog with copyable text.
Place this in: utils/error_dialog.py
"""

import tkinter as tk
from tkinter import ttk
import traceback
from typing import Optional


class CopyableErrorDialog:
    """Error dialog with copyable error message."""
    
    @staticmethod
    def showerror(title: str, message: str, parent=None, exception: Optional[Exception] = None):
        """
        Show an error dialog with copyable text.
        
        Args:
            title: Dialog title
            message: Error message
            parent: Parent window (optional)
            exception: Exception object to include traceback (optional)
        """
        dialog = tk.Toplevel(parent) if parent else tk.Tk()
        dialog.title(title)
        dialog.geometry("600x400")
        
        # Make dialog modal
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center the dialog
        if parent:
            dialog.geometry("+%d+%d" % (
                parent.winfo_rootx() + 50,
                parent.winfo_rooty() + 50
            ))
        
        # Main frame
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label with error icon
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="❌", font=('Arial', 24)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(title_frame, text=title, font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 10))
        
        # Error message in a text widget (copyable)
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create text widget with scrollbar
        text_widget = tk.Text(text_frame, wrap=tk.WORD, height=15, width=70)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert error message
        text_widget.insert('1.0', message)
        
        # Add traceback if exception provided
        if exception:
            text_widget.insert(tk.END, "\n\n" + "="*60 + "\n")
            text_widget.insert(tk.END, "TECHNICAL DETAILS:\n")
            text_widget.insert(tk.END, "="*60 + "\n\n")
            text_widget.insert(tk.END, traceback.format_exc())
        
        # Make text widget read-only but still selectable
        text_widget.configure(state='disabled')
        
        # Enable Ctrl+A to select all
        text_widget.bind('<Control-a>', lambda e: text_widget.tag_add('sel', '1.0', 'end'))
        text_widget.bind('<Control-A>', lambda e: text_widget.tag_add('sel', '1.0', 'end'))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Copy to clipboard button
        def copy_to_clipboard():
            dialog.clipboard_clear()
            error_text = text_widget.get('1.0', 'end-1c')
            dialog.clipboard_append(error_text)
            copy_button.config(text="✓ Copied!")
            dialog.after(2000, lambda: copy_button.config(text="Copy to Clipboard"))
        
        copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # OK button
        ttk.Button(button_frame, text="OK", command=dialog.destroy).pack(side=tk.RIGHT)
        
        # Make dialog stay on top and wait for it to close
        dialog.focus_set()
        if parent:
            dialog.wait_window()
    
    @staticmethod
    def showwarning(title: str, message: str, parent=None):
        """
        Show a warning dialog with copyable text.
        
        Args:
            title: Dialog title
            message: Warning message
            parent: Parent window (optional)
        """
        dialog = tk.Toplevel(parent) if parent else tk.Tk()
        dialog.title(title)
        dialog.geometry("600x300")
        
        dialog.transient(parent)
        dialog.grab_set()
        
        if parent:
            dialog.geometry("+%d+%d" % (
                parent.winfo_rootx() + 50,
                parent.winfo_rooty() + 50
            ))
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with warning icon
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="⚠️", font=('Arial', 24)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(title_frame, text=title, font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 10))
        
        # Message text
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, height=10, width=70)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget.insert('1.0', message)
        text_widget.configure(state='disabled')
        
        text_widget.bind('<Control-a>', lambda e: text_widget.tag_add('sel', '1.0', 'end'))
        text_widget.bind('<Control-A>', lambda e: text_widget.tag_add('sel', '1.0', 'end'))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def copy_to_clipboard():
            dialog.clipboard_clear()
            dialog.clipboard_append(text_widget.get('1.0', 'end-1c'))
            copy_button.config(text="✓ Copied!")
            dialog.after(2000, lambda: copy_button.config(text="Copy to Clipboard"))
        
        copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="OK", command=dialog.destroy).pack(side=tk.RIGHT)
        
        dialog.focus_set()
        if parent:
            dialog.wait_window()
    
    @staticmethod
    def showinfo(title: str, message: str, parent=None):
        """
        Show an info dialog with copyable text.
        
        Args:
            title: Dialog title
            message: Info message
            parent: Parent window (optional)
        """
        dialog = tk.Toplevel(parent) if parent else tk.Tk()
        dialog.title(title)
        dialog.geometry("600x300")
        
        dialog.transient(parent)
        dialog.grab_set()
        
        if parent:
            dialog.geometry("+%d+%d" % (
                parent.winfo_rootx() + 50,
                parent.winfo_rooty() + 50
            ))
        
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title with info icon
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(title_frame, text="ℹ️", font=('Arial', 24)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(title_frame, text=title, font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(0, 10))
        
        # Message text
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, height=10, width=70)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_widget.insert('1.0', message)
        text_widget.configure(state='disabled')
        
        text_widget.bind('<Control-a>', lambda e: text_widget.tag_add('sel', '1.0', 'end'))
        text_widget.bind('<Control-A>', lambda e: text_widget.tag_add('sel', '1.0', 'end'))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def copy_to_clipboard():
            dialog.clipboard_clear()
            dialog.clipboard_append(text_widget.get('1.0', 'end-1c'))
            copy_button.config(text="✓ Copied!")
            dialog.after(2000, lambda: copy_button.config(text="Copy to Clipboard"))
        
        copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard)
        copy_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="OK", command=dialog.destroy).pack(side=tk.RIGHT)
        
        dialog.focus_set()
        if parent:
            dialog.wait_window()


# Convenience function to replace messagebox calls
def showerror(title, message, parent=None, exception=None):
    """Show copyable error dialog."""
    CopyableErrorDialog.showerror(title, message, parent, exception)


def showwarning(title, message, parent=None):
    """Show copyable warning dialog."""
    CopyableErrorDialog.showwarning(title, message, parent)


def showinfo(title, message, parent=None):
    """Show copyable info dialog."""
    CopyableErrorDialog.showinfo(title, message, parent)
