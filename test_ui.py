#!/usr/bin/env python3
"""Test script to verify UI implementations in BuyEuropean."""

import os
import sys
import argparse
from pathlib import Path

def setup_path():
    """Add the project root to the Python path if running from the repo."""
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "src" / "buyeuropean").exists():
        sys.path.insert(0, str(script_dir))
        print(f"Added {script_dir} to Python path.")

def main():
    """Run the test script."""
    # Add the project root to the Python path if needed
    setup_path()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test BuyEuropean UI implementations")
    parser.add_argument("--gtk", action="store_true", help="Force GTK4 frontend")
    parser.add_argument("--qt", action="store_true", help="Force Qt6 frontend")
    parser.add_argument("--show-all", action="store_true", help="Show both UIs one after another")
    args = parser.parse_args()
    
    if args.show_all:
        # Try GTK first, then Qt
        print("Starting GTK UI test...")
        run_ui(True, False)
        
        print("\nStarting Qt UI test...")
        run_ui(False, True)
    else:
        # Run just one UI based on arguments
        run_ui(args.gtk, args.qt)

def run_ui(force_gtk, force_qt):
    """Run a specific UI implementation."""
    try:
        from buyeuropean.platform import get_ui_toolkit
        
        # Get the appropriate UI toolkit
        try:
            App = get_ui_toolkit(force_gtk=force_gtk, force_qt=force_qt)
            app = App()
            
            ui_type = "GTK" if force_gtk else "Qt" if force_qt else "Auto-detected"
            print(f"Running {ui_type} UI: {App.__name__}")
            
            return app.run()
        except ImportError as e:
            print(f"Error: {e}")
            print("Please install either PyGObject (for GTK4) or PyQt6 depending on your platform.")
            return 1
    except Exception as e:
        print(f"Failed to run UI test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
