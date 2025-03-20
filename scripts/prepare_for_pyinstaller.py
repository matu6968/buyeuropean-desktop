#!/usr/bin/env python3
"""
Prepare the BuyEuropean application for PyInstaller packaging.
This script ensures all necessary data files are available.
"""

import os
from pathlib import Path

def ensure_directory_exists(directory):
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

def check_assets():
    """Check that all necessary asset files exist."""
    # Define the project root
    project_root = Path(__file__).parent.parent
    
    # Check sound files
    sounds_dir = project_root / "src" / "buyeuropean" / "sounds"
    if not sounds_dir.exists():
        print(f"Warning: Sounds directory not found: {sounds_dir} Any sound effects will not play.")
    else:
        sound_files = [
            sounds_dir / "success.ogg",
            sounds_dir / "error.ogg",
            sounds_dir / "success.wav",
            sounds_dir / "error.wav"
        ]
        
        for sound_file in sound_files:
            if not sound_file.exists():
                print(f"Warning: Sound file not found: {sound_file} This sound effect will not play.")
    
    # Check logo files
    logos_dir = project_root / "src" / "buyeuropean" / "ui" / "gtk" / "logos"
    if not logos_dir.exists():
        print(f"Warning: Logos directory not found: {logos_dir} Any logos in the GTK frontend will instead show the European Union emoji.")
    else:
        logo_file = logos_dir / "logo_buyeuropean.png"
        if not logo_file.exists():
            print(f"Warning: Logo file not found: {logo_file} This logo in the GTK frontend will instead show as the European Union emoji.")
    
    # Check Qt logo files
    qt_logos_dir = project_root / "src" / "buyeuropean" / "ui" / "qt" / "logos"
    if not qt_logos_dir.exists():
        print(f"Warning: Qt logos directory not found: {qt_logos_dir}")
        print(f"Creating Qt logos directory and copying logo from GTK directory...")
        ensure_directory_exists(qt_logos_dir)
        if logos_dir.exists() and (logos_dir / "logo_buyeuropean.png").exists():
            import shutil
            shutil.copy2(
                logos_dir / "logo_buyeuropean.png",
                qt_logos_dir / "logo_buyeuropean.png"
            )
            print(f"Logo copied successfully to Qt directory.")
    else:
        qt_logo_file = qt_logos_dir / "logo_buyeuropean.png"
        if not qt_logo_file.exists():
            print(f"Warning: Qt logo file not found: {qt_logo_file} Any logos in the Qt frontend will instead show nothing.")
            if logos_dir.exists() and (logos_dir / "logo_buyeuropean.png").exists():
                import shutil
                shutil.copy2(
                    logos_dir / "logo_buyeuropean.png",
                    qt_logos_dir / "logo_buyeuropean.png"
                )
                print(f"Logo copied successfully to Qt directory.")

def main():
    """Run the preparation steps."""
    print("Preparing BuyEuropean for PyInstaller packaging...")
    
    # Check existing assets
    check_assets()
    
    print("Preparation completed. All necessary assets have been verified.")
    print("You can now run 'pyinstaller buyeuropean.spec' to create the package.")

if __name__ == "__main__":
    main() 