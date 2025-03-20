"""Qt 6 implementation of BuyEuropean frontend."""

import os
import sys
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QWidget, QFileDialog, QScrollArea, QTextEdit, QFrame, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QObject, QThread, QUrl
from PyQt6.QtMultimedia import QSoundEffect, QMediaPlayer, QAudioOutput

# Define QFrame shape and shadow constants for compatibility with different PyQt6 versions
try:
    # Try accessing the enum directly
    QFrame.HLine  # If this works, we're using a newer PyQt6 version
    QFrame.VLine
    QFrame.StyledPanel
    QFrame.Raised
    QFrame.Sunken
except AttributeError:
    # If the above fails, we're using an older PyQt6 version with nested enums
    # Define frame shape constants
    if hasattr(QFrame, 'Shape'):
        QFrame.HLine = QFrame.Shape.HLine
        QFrame.VLine = QFrame.Shape.VLine
        QFrame.StyledPanel = QFrame.Shape.StyledPanel
        QFrame.NoFrame = QFrame.Shape.NoFrame
    else:
        # Hardcoded values from Qt documentation as last resort
        QFrame.HLine = 0x0004
        QFrame.VLine = 0x0005
        QFrame.StyledPanel = 0x0006
        QFrame.NoFrame = 0
        
    # Define frame shadow constants
    if hasattr(QFrame, 'Shadow'):
        QFrame.Raised = QFrame.Shadow.Raised
        QFrame.Sunken = QFrame.Shadow.Sunken
        QFrame.Plain = QFrame.Shadow.Plain
    else:
        # Hardcoded values from Qt documentation as last resort
        QFrame.Raised = 0x0020
        QFrame.Sunken = 0x0030
        QFrame.Plain = 0x0010

from buyeuropean.api import BuyEuropeanAPI

# Define sound file paths
SOUND_DIR = Path(__file__).parent.parent.parent / "sounds"
SUCCESS_SOUND_OGG = SOUND_DIR / "success.ogg"
ERROR_SOUND_OGG = SOUND_DIR / "error.ogg"
SUCCESS_SOUND_WAV = SOUND_DIR / "success.wav"
ERROR_SOUND_WAV = SOUND_DIR / "error.wav"

# Define logo path
LOGO_PATH = Path(__file__).parent.parent / "qt" / "logos" / "logo_buyeuropean.png"

class WorkerSignals(QObject):
    """Worker signals for threaded operations."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class AnalysisWorker(QThread):
    """Worker thread for analysis operations."""
    def __init__(self, api, image_path):
        super().__init__()
        self.api = api
        self.image_path = image_path
        self.signals = WorkerSignals()
        
    def run(self):
        """Run the analysis in a separate thread."""
        try:
            result = self.api.analyze_product(Path(self.image_path))
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class QtApp:
    """Qt 6 application for BuyEuropean."""
    
    def __init__(self):
        """Initialize the Qt application."""
        self.api = BuyEuropeanAPI()
        self.app = QApplication(sys.argv)
        
        # Set the application style to Fusion for consistent look
        self.app.setStyle("Fusion")
        
        # Set up dark palette for consistent theming with GTK version
        self.setup_dark_palette()
        
        self.setup_ui()
        
        # Initialize sound effects with multi-format support
        self.setup_sound_effects()
        
    def setup_dark_palette(self):
        """Set up a dark color palette for the application."""
        dark_palette = QPalette()
        
        # Set color roles for dark theme
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
        
        # Apply the palette to the application
        self.app.setPalette(dark_palette)
        
    def setup_sound_effects(self):
        """Initialize sound effects with multi-format support."""
        # Set up primary sound player using QSoundEffect
        self.success_sound = QSoundEffect()
        self.error_sound = QSoundEffect()
        
        # Try WAV files first (better compatibility with Qt)
        if SUCCESS_SOUND_WAV.exists():
            self.success_sound.setSource(QUrl.fromLocalFile(str(SUCCESS_SOUND_WAV)))
        elif SUCCESS_SOUND_OGG.exists():
            self.success_sound.setSource(QUrl.fromLocalFile(str(SUCCESS_SOUND_OGG)))
            
        if ERROR_SOUND_WAV.exists():
            self.error_sound.setSource(QUrl.fromLocalFile(str(ERROR_SOUND_WAV)))
        elif ERROR_SOUND_OGG.exists():
            self.error_sound.setSource(QUrl.fromLocalFile(str(ERROR_SOUND_OGG)))
            
        # Set volume for both sound effects
        self.success_sound.setVolume(0.5)
        self.error_sound.setVolume(0.5)
        
        # Set up fallback player using QMediaPlayer
        self.use_mediaplayer_fallback = False
        
        # Test if sound effects loaded correctly
        if not self.success_sound.isLoaded() and not self.error_sound.isLoaded():
            print("QSoundEffect failed to load sounds, will use QMediaPlayer as fallback")
            self.use_mediaplayer_fallback = True
            self.setup_mediaplayer_fallback()
    
    def setup_mediaplayer_fallback(self):
        """Set up QMediaPlayer as fallback for sound playback."""
        # Create players and audio outputs
        self.success_player = QMediaPlayer()
        self.success_audio = QAudioOutput()
        self.success_player.setAudioOutput(self.success_audio)
        
        self.error_player = QMediaPlayer()
        self.error_audio = QAudioOutput()
        self.error_player.setAudioOutput(self.error_audio)
        
        # Set volume
        self.success_audio.setVolume(0.5)
        self.error_audio.setVolume(0.5)
        
        # Set sources with format priority
        if SUCCESS_SOUND_WAV.exists():
            self.success_player.setSource(QUrl.fromLocalFile(str(SUCCESS_SOUND_WAV)))
        elif SUCCESS_SOUND_OGG.exists():
            self.success_player.setSource(QUrl.fromLocalFile(str(SUCCESS_SOUND_OGG)))
            
        if ERROR_SOUND_WAV.exists():
            self.error_player.setSource(QUrl.fromLocalFile(str(ERROR_SOUND_WAV)))
        elif ERROR_SOUND_OGG.exists():
            self.error_player.setSource(QUrl.fromLocalFile(str(ERROR_SOUND_OGG)))
            
    def setup_ui(self):
        """Set up the user interface."""
        # Create the main window
        self.window = QMainWindow()
        self.window.setWindowTitle("BuyEuropean")
        self.window.setMinimumSize(800, 600)
        
        # Create a central widget for the window
        central_widget = QWidget()
        
        # Create main layout
        outer_layout = QVBoxLayout(central_widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        # Create a scroll area to make the entire UI scrollable
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create container for scrollable content
        scroll_content = QWidget()
        
        # Create layout for content inside the scroll area
        self.main_layout = QVBoxLayout(scroll_content)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Add logo if it exists
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo_exists = LOGO_PATH.exists()
        if logo_exists:
            try:
                logo_pixmap = QPixmap(str(LOGO_PATH))
                if not logo_pixmap.isNull():
                    # Scale the logo to a reasonable size
                    logo_pixmap = logo_pixmap.scaled(
                        128, 128,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    logo_label = QLabel()
                    logo_label.setPixmap(logo_pixmap)
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    logo_layout.addWidget(logo_label)
                    self.main_layout.addLayout(logo_layout)
            except Exception as e:
                print(f"Error loading logo: {e}")
                # In case of error, we'll proceed without the logo
        
        # Add title label
        title_label = QLabel("BuyEuropean")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(title_label)
        
        # Add subtitle label
        subtitle_label = QLabel("Check if products are from European companies")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(subtitle_label)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("QFrame { background-color: #555; }")
        self.main_layout.addWidget(separator)
        
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add button to select image
        self.select_image_button = QPushButton("Select Product Image")
        self.select_image_button.setMinimumWidth(200)
        self.select_image_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
        """)
        self.select_image_button.clicked.connect(self.on_select_image_clicked)
        button_layout.addWidget(self.select_image_button)
        
        self.main_layout.addLayout(button_layout)
        
        # Add image preview area
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setMinimumSize(300, 300)
        self.image_preview.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.image_preview.setStyleSheet("border: 1px solid #555;")
        self.main_layout.addWidget(self.image_preview)
        
        # Add analyze button (initially disabled)
        self.analyze_button = QPushButton("Analyze Product")
        self.analyze_button.setEnabled(False)
        self.analyze_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.analyze_button.setMinimumWidth(200)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
            QPushButton:disabled {
                background-color: #2c2c2c;
                color: #777;
            }
        """)
        analyze_button_layout = QHBoxLayout()
        analyze_button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        analyze_button_layout.addWidget(self.analyze_button)
        self.main_layout.addLayout(analyze_button_layout)
        
        # Add results area with title frame
        self.results_frame = QFrame()
        self.results_frame.setFrameShape(QFrame.StyledPanel)
        self.results_frame.setFrameShadow(QFrame.Raised)
        self.results_frame.setStyleSheet("QFrame { background-color: #2c2c2c; }")
        self.results_frame.setVisible(False)  # Initially hide results area
        
        results_layout = QVBoxLayout(self.results_frame)
        results_layout.setContentsMargins(15, 15, 15, 15)
        results_layout.setSpacing(10)
        
        # Product info header
        self.product_info = QLabel()
        self.product_info.setTextFormat(Qt.TextFormat.RichText)
        self.product_info.setWordWrap(True)
        self.product_info.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.product_info.setStyleSheet("font-size: 14px; padding: 6px;")
        results_layout.addWidget(self.product_info)
        
        # Classification label
        self.classification_label = QLabel()
        self.classification_label.setTextFormat(Qt.TextFormat.RichText)
        self.classification_label.setWordWrap(True)
        self.classification_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.classification_label.setStyleSheet("font-size: 18px; font-weight: bold; padding: 6px;")
        results_layout.addWidget(self.classification_label)
        
        # Add space
        results_layout.addSpacing(10)
        
        # Detailed info section
        details_label = QLabel("Product Details")
        details_label.setStyleSheet("font-weight: bold; padding: 4px;")
        results_layout.addWidget(details_label)
        
        # Add detailed results with scrolling
        self.details_view = QTextEdit()
        self.details_view.setReadOnly(True)
        self.details_view.setMinimumHeight(150)
        self.details_view.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                border: 1px solid #555;
                padding: 6px;
            }
        """)
        results_layout.addWidget(self.details_view)
        
        # Alternatives section
        self.alternatives_label = QLabel("European Alternatives")
        self.alternatives_label.setStyleSheet("font-weight: bold; padding: 4px; margin-top: 6px;")
        self.alternatives_label.setVisible(False)
        results_layout.addWidget(self.alternatives_label)
        
        # Section for alternative buttons
        self.alternatives_widget = QWidget()
        self.alternatives_layout = QVBoxLayout(self.alternatives_widget)
        self.alternatives_layout.setContentsMargins(0, 0, 0, 0)
        self.alternatives_widget.setVisible(False)
        results_layout.addWidget(self.alternatives_widget)

        # Add a disclaimer saying AI results can make mistakes
        disclaimer = QLabel("This is an AI-powered tool, as it can make mistakes. Please verify the information before making any decisions.")
        disclaimer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimer.setStyleSheet("font-size: 12px; padding: 6px;")
        results_layout.addWidget(disclaimer)    
        
        # Add the results frame to the main layout
        self.main_layout.addWidget(self.results_frame)
        
        # Set the scroll content as the widget for scroll area
        scroll_area.setWidget(scroll_content)
        
        # Add the scroll area to the outer layout
        outer_layout.addWidget(scroll_area)
        
        # Set the central widget
        self.window.setCentralWidget(central_widget)
        
        # Store the selected image path
        self.selected_image_path = None
        
        # Connect analyze button
        self.analyze_button.clicked.connect(self.on_analyze_clicked)
        
    def on_select_image_clicked(self):
        """Handle image selection button click."""
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select a Product Image")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Image Files (*.png *.jpg *.jpeg)")
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.selected_image_path = file_paths[0]
                
                # Set preview image
                pixmap = QPixmap(self.selected_image_path)
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(
                        300, 300, 
                        Qt.AspectRatioMode.KeepAspectRatio, 
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_preview.setPixmap(pixmap)
                    
                    # Enable the analyze button
                    self.analyze_button.setEnabled(True)
                    self.analyze_button.setStyleSheet("""
                        QPushButton {
                            background-color: #3174ad;
                            color: white;
                            border: 1px solid #2c6ca0;
                            padding: 8px 16px;
                            border-radius: 4px;
                        }
                        QPushButton:hover {
                            background-color: #3c87c7;
                        }
                        QPushButton:pressed {
                            background-color: #296090;
                        }
                    """)
    
    def on_analyze_clicked(self):
        """Handle analyze button click."""
        if not self.selected_image_path:
            return
            
        # Disable the button during analysis
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("Analyzing...")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #aaa;
                border: 1px solid #555;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:disabled {
                background-color: #2c2c2c;
                color: #777;
            }
        """)
        
        # Clear previous results
        self.details_view.clear()
        self.product_info.clear()
        self.classification_label.clear()
        
        # Hide the results frame until we have new results
        self.results_frame.setVisible(False)
        
        # Clear any alternative buttons
        self.clear_alt_buttons()
        
        # Create and start worker thread
        self.worker = AnalysisWorker(self.api, self.selected_image_path)
        self.worker.signals.finished.connect(self.update_results)
        self.worker.signals.error.connect(self.show_error)
        self.worker.start()
        
    def update_results(self, result):
        """Update the UI with analysis results."""
        if not result:
            self.show_error("Failed to analyze product. Please try again.")
            return
            
        # Show the results frame
        self.results_frame.setVisible(True)
            
        # Update the main result label
        product_name = result.get("identified_product_name", "Unknown product")
        company = result.get("identified_company", "Unknown company")
        country = result.get("identified_headquarters", "Unknown country")
        classification = result.get("classification", "unknown")
        
        # Handle classification properly
        if classification == "european_country":
            category = "European"
            color = "green"
            self.play_sound(True)  # Success sound
        elif classification == "european_ally":
            category = "European Ally"
            color = "#3366cc"  # Blue
            self.play_sound(True)  # Success sound
        elif classification == "european_sceptic":
            category = "European Sceptic"
            color = "#ff6600"  # Orange
            self.play_sound(False)  # Error sound
        else:
            category = "Unknown"
            color = "#cc9900"  # Yellow-orange
        
        # Set product info
        self.product_info.setText(
            f"<b>{product_name}</b> by <b>{company}</b> from <b>{country}</b>"
        )
        
        # Set classification label with color
        self.classification_label.setText(
            f"<span style='color: {color};'>{category}</span>"
        )
        
        # Update detailed results
        detailed_text = (
            f"Product: {product_name}\n"
            f"Company: {company}\n"
            f"Headquarters: {country}\n"
            f"Classification: {classification}\n\n"
        )
        
        # Add identification rationale with better formatting
        rationale = result.get('identification_rationale', '')
        if rationale:
            detailed_text += f"Identification rationale:\n{rationale}\n\n"
            
        # Add thinking output if available
        thinking = result.get('potential_alternative_thinking', '')
        if thinking:
            detailed_text += f"Alternative Analysis:\n{thinking}\n\n"
            
        # Add debugging information if available
        debug_text = "Debugging Information:\n"
        has_debug = False
        
        request_id = result.get('id')
        if request_id:
            debug_text += f"Request ID: {request_id}\n"
            has_debug = True
            
        input_tokens = result.get('input_tokens')
        if input_tokens:
            debug_text += f"Input Tokens: {input_tokens}\n"
            has_debug = True
            
        output_tokens = result.get('output_tokens')
        if output_tokens:
            debug_text += f"Output Tokens: {output_tokens}\n"
            has_debug = True
            
        total_tokens = result.get('total_tokens')
        if total_tokens:
            debug_text += f"Total Tokens: {total_tokens}\n"
            has_debug = True
            
        if has_debug:
            detailed_text += debug_text + "\n"
        
        # Update the text area
        self.details_view.setText(detailed_text)
        
        # Add potential alternatives if available
        alternatives = result.get("potential_alternatives", [])
        if alternatives:
            # Show alternatives section
            self.alternatives_label.setVisible(True)
            self.alternatives_widget.setVisible(True)
            
            # Clear any previous alternative buttons
            self.clear_alt_buttons()
            
            for alt in alternatives:
                alt_name = alt.get('product_name', 'N/A')
                alt_company = alt.get('company', 'N/A')
                alt_country = alt.get('country', 'N/A')
                alt_description = alt.get('description', '')
                
                # Create a frame for each alternative
                alt_frame = QFrame()
                alt_frame.setFrameShape(QFrame.StyledPanel)
                alt_frame.setStyleSheet("""
                    QFrame { 
                        background-color: #333; 
                        border-radius: 4px;
                        padding: 4px;
                        margin: 4px;
                    }
                """)
                
                alt_layout = QVBoxLayout(alt_frame)
                alt_layout.setContentsMargins(8, 8, 8, 8)
                
                # Add header with country emoji
                header_layout = QHBoxLayout()
                
                # Get country emoji
                country_emoji = self.get_country_flag_emoji(alt_country)
                emoji_label = QLabel(country_emoji)
                emoji_label.setStyleSheet("font-size: 18px; margin-right: 6px;")
                header_layout.addWidget(emoji_label)
                
                # Add product name and company
                product_label = QLabel(f"<b>{alt_name}</b> by {alt_company}")
                product_label.setStyleSheet("color: white;")
                header_layout.addWidget(product_label)
                header_layout.addStretch()
                
                alt_layout.addLayout(header_layout)
                
                # Add description if available
                if alt_description:
                    desc_label = QLabel(alt_description)
                    desc_label.setWordWrap(True)
                    desc_label.setStyleSheet("color: #ccc; margin-top: 4px;")
                    alt_layout.addWidget(desc_label)
                
                # Add learn more button
                learn_button = QPushButton("Learn More")
                learn_button.setStyleSheet("""
                    QPushButton {
                        background-color: #2a5a8c;
                        color: white;
                        border: none;
                        padding: 6px 12px;
                        border-radius: 3px;
                        margin-top: 6px;
                    }
                    QPushButton:hover {
                        background-color: #336699;
                    }
                """)
                learn_button.clicked.connect(
                    lambda checked=False, name=alt_name, company=alt_company: 
                    self.open_search(f"{name} {company}")
                )
                
                alt_layout.addWidget(learn_button)
                self.alternatives_layout.addWidget(alt_frame)
        else:
            # Hide the alternatives section if no alternatives
            self.alternatives_label.setVisible(False)
            self.alternatives_widget.setVisible(False)
        
        # Re-enable the analyze button
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("Analyze Product")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #3174ad;
                color: white;
                border: 1px solid #2c6ca0;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3c87c7;
            }
            QPushButton:pressed {
                background-color: #296090;
            }
        """)
    
    def get_country_flag_emoji(self, country_name):
        """Convert a country name to its flag emoji or formatted text."""
        # Map of common European countries to their flag emojis
        country_map = {
            "Austria": "🇦🇹",
            "Belgium": "🇧🇪",
            "Bulgaria": "🇧🇬",
            "Croatia": "🇭🇷",
            "Cyprus": "🇨🇾",
            "Czech Republic": "🇨🇿",
            "Denmark": "🇩🇰",
            "Estonia": "🇪🇪",
            "Finland": "🇫🇮",
            "France": "🇫🇷",
            "Germany": "🇩🇪",
            "Greece": "🇬🇷",
            "Hungary": "🇭🇺",
            "Ireland": "🇮🇪",
            "Italy": "🇮🇹",
            "Latvia": "🇱🇻",
            "Lithuania": "🇱🇹",
            "Luxembourg": "🇱🇺",
            "Malta": "🇲🇹",
            "Netherlands": "🇳🇱",
            "Poland": "🇵🇱",
            "Portugal": "🇵🇹",
            "Romania": "🇷🇴",
            "Slovakia": "🇸🇰",
            "Slovenia": "🇸🇮",
            "Spain": "🇪🇸",
            "Sweden": "🇸🇪",
            "United Kingdom": "🇬🇧",
            "Switzerland": "🇨🇭",
            "Norway": "🇳🇴",
            "Iceland": "🇮🇸",
            "Liechtenstein": "🇱🇮",
            "United States": "🇺🇸",
            "China": "🇨🇳",
            "Japan": "🇯🇵",
            "South Korea": "🇰🇷",
            "Russia": "🇷🇺",
            "India": "🇮🇳",
            "Brazil": "🇧🇷",
            "Canada": "🇨🇦",
            "Australia": "🇦🇺",
            "New Zealand": "🇳🇿",
        }
        
        # Two-letter country codes for backup text representation
        country_codes = {
            "Austria": "AT",
            "Belgium": "BE",
            "Bulgaria": "BG",
            "Croatia": "HR",
            "Cyprus": "CY",
            "Czech Republic": "CZ",
            "Denmark": "DK",
            "Estonia": "EE",
            "Finland": "FI",
            "France": "FR",
            "Germany": "DE",
            "Greece": "GR",
            "Hungary": "HU",
            "Ireland": "IE",
            "Italy": "IT",
            "Latvia": "LV",
            "Lithuania": "LT",
            "Luxembourg": "LU",
            "Malta": "MT",
            "Netherlands": "NL",
            "Poland": "PL",
            "Portugal": "PT",
            "Romania": "RO",
            "Slovakia": "SK",
            "Slovenia": "SI",
            "Spain": "ES",
            "Sweden": "SE",
            "United Kingdom": "GB",
            "Switzerland": "CH",
            "Norway": "NO",
            "Iceland": "IS",
            "Liechtenstein": "LI",
            "United States": "US",
            "China": "CN",
            "Japan": "JP",
            "South Korea": "KR",
            "Russia": "RU",
            "India": "IN",
            "Brazil": "BR",
            "Canada": "CA",
            "Australia": "AU",
            "New Zealand": "NZ",
        }
        
        # Try to match the country name exactly
        if country_name in country_map:
            emoji = country_map[country_name]
            code = country_codes.get(country_name, "EU")
            return f"{emoji} {code}"
        
        # Check for partial matches
        for known_country, emoji in country_map.items():
            if known_country in country_name or country_name in known_country:
                code = country_codes.get(known_country, "EU")
                return f"{emoji} {code}"
        
        # If no match found, return the EU flag as default
        return "🇪🇺 EU"
        
    def open_search(self, search_term):
        """Open a web browser with a search for the given term."""
        import webbrowser
        search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
        webbrowser.open(search_url)
    
    def clear_alt_buttons(self):
        """Clear alternative buttons from the UI."""
        while self.alternatives_layout.count():
            item = self.alternatives_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            
    def play_sound(self, is_success):
        """Play a sound based on the result."""
        try:
            if self.use_mediaplayer_fallback:
                # Use QMediaPlayer for playback
                if is_success:
                    self.success_player.play()
                else:
                    self.error_player.play()
            else:
                # Use QSoundEffect for playback
                if is_success:
                    if self.success_sound.isLoaded():
                        self.success_sound.play()
                else:
                    if self.error_sound.isLoaded():
                        self.error_sound.play()
        except Exception as e:
            print(f"Error playing sound: {e}")
            
    def show_error(self, message):
        """Show an error message in the UI."""
        # Make results frame visible for error display
        self.results_frame.setVisible(True)
        
        self.product_info.setText("<b>Error</b>")
        self.classification_label.setText(f"<span style='color: red;'>{message}</span>")
        
        # Clear any alternative buttons
        self.clear_alt_buttons()
        
        # Hide the alternatives section
        self.alternatives_label.setVisible(False)
        self.alternatives_widget.setVisible(False)
        
        # Re-enable the analyze button
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("Analyze Product")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #3174ad;
                color: white;
                border: 1px solid #2c6ca0;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3c87c7;
            }
            QPushButton:pressed {
                background-color: #296090;
            }
        """)
        
        # Play error sound
        self.play_sound(False)
        
    def run(self):
        """Run the application."""
        self.window.show()
        return self.app.exec() 