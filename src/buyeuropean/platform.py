"""Platform detection utilities for UI selection."""

import sys
import platform


def is_linux() -> bool:
    """Check if the current platform is Linux."""
    return sys.platform.startswith("linux")


def is_windows() -> bool:
    """Check if the current platform is Windows."""
    return sys.platform.startswith("win")


def is_macos() -> bool:
    """Check if the current platform is macOS."""
    return sys.platform.startswith("darwin")


def is_android() -> bool:
    """Check if the current platform is Android."""
    # Simple, naive detection for Android by checking Linux + "android" in the machine name
    return sys.platform.startswith("linux") and "android" in platform.machine().lower()


def should_use_gtk(force_gtk=False, force_qt=False) -> bool:
    """Determine if GTK should be used based on platform and user preference."""
    if force_gtk:
        return True
    if force_qt:
        return False
    return is_linux() or is_windows()


def should_use_qt(force_gtk=False, force_qt=False) -> bool:
    """Determine if Qt should be used based on platform and user preference."""
    if force_qt:
        return True
    if force_gtk:
        return False
    return is_macos() or is_android() or not should_use_gtk(force_gtk, force_qt)


def get_ui_toolkit(force_gtk=False, force_qt=False):
    """Get the appropriate UI toolkit based on platform and user preference.

    Args:
        force_gtk: If True, forces the use of GTK4 regardless of platform.
        force_qt: If True, forces the use of Qt6 regardless of platform.

    Returns:
        The appropriate UI application class.

    Raises:
        ImportError: If neither GTK4 nor Qt6 is available.
    """
    if force_gtk or (should_use_gtk(force_gtk, force_qt) and not force_qt):
        # Try to import GTK modules
        try:
            import gi
            gi.require_version('Gtk', '4.0')
            from gi.repository import Gtk
            from buyeuropean.ui.gtk.app import GtkApp
            return GtkApp
        except (ImportError, ValueError) as e:
            if force_gtk:
                # If GTK was explicitly requested but not available, raise the error
                raise ImportError(f"GTK4 was explicitly requested but could not be loaded: {e}")
            print("GTK 4 not available, falling back to Qt")
            pass

    # Try to import Qt modules
    try:
        from PyQt6.QtWidgets import QApplication
        from buyeuropean.ui.qt.app import QtApp
        return QtApp
    except ImportError as e:
        if force_qt:
            # If Qt was explicitly requested but not available, raise the error
            raise ImportError(f"Qt6 was explicitly requested but could not be loaded: {e}")

        # If we get here, neither toolkit is available
        raise ImportError("Neither GTK4 nor Qt6 is available. Please install one of them.")
