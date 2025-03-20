"""Main entry point for the BuyEuropean desktop application."""

import sys
import argparse
from buyeuropean.platform import get_ui_toolkit

def main():
    """Run the BuyEuropean application."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="BuyEuropean Desktop - Check if products are from European companies")
    
    # Add flags to force GTK4 or Qt6 UI
    ui_group = parser.add_mutually_exclusive_group()
    ui_group.add_argument("--gtk4", action="store_true", help="Force GTK4 user interface")
    ui_group.add_argument("--qt6", action="store_true", help="Force Qt6 user interface")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine frontend preference
    force_gtk = args.gtk4 if hasattr(args, 'gtk4') else False
    force_qt = args.qt6 if hasattr(args, 'qt6') else False
    
    # Get the appropriate UI toolkit based on platform and arguments
    try:
        App = get_ui_toolkit(force_gtk=force_gtk, force_qt=force_qt)
        app = App()
        return app.run()
    except ImportError as e:
        print(f"Error: {e}")
        print("Please install either PyGObject (for GTK4) or PyQt6 depending on your platform.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 