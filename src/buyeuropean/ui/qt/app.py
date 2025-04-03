"""Qt 6 implementation of BuyEuropean frontend."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QFileDialog, QScrollArea, QTextEdit, QFrame, QSizePolicy,
    QDialog, QCheckBox, QMessageBox, QDialogButtonBox
)
from PyQt6.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QUrl
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


# Feedback dialog class
class FeedbackDialog(QDialog):
    """Dialog for collecting user feedback on analysis results."""

    def __init__(self, parent=None):
        """Initialize the feedback dialog."""
        super().__init__(parent)
        self.setWindowTitle("What was incorrect?")
        self.setMinimumWidth(400)

        # Create the layout
        layout = QVBoxLayout(self)

        # Add checkboxes for different issues
        self.product_check = QCheckBox("Product identification")
        layout.addWidget(self.product_check)

        self.brand_check = QCheckBox("Brand identification")
        layout.addWidget(self.brand_check)

        self.country_check = QCheckBox("Country identification")
        layout.addWidget(self.country_check)

        self.classification_check = QCheckBox("Classification")
        layout.addWidget(self.classification_check)

        self.alternatives_check = QCheckBox("Suggested alternatives")
        layout.addWidget(self.alternatives_check)

        self.other_check = QCheckBox("Other")
        layout.addWidget(self.other_check)

        # Add a text edit for comments
        layout.addWidget(QLabel("Any additional comments?"))

        self.comments_edit = QTextEdit()
        self.comments_edit.setMinimumHeight(100)
        layout.addWidget(self.comments_edit)

        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


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

        # Store the current analysis result
        self.current_result = None

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

        # Store the current result for feedback
        self.current_result = result

        # Show the results frame
        self.results_frame.setVisible(True)

        # Update the main result label
        product_name = result.get("identified_product_name", "Unknown product")
        company = result.get("identified_company", "Unknown company")
        country_code = result.get("identified_company_headquarters", "")
        country = country_code  # Start with code, will be expanded if available

        # Get the parent company information if available
        parent_company = result.get("ultimate_parent_company")
        parent_country_code = result.get("ultimate_parent_company_headquarters")

        # Get product/animal/human classification
        item_type = result.get("product_or_animal_or_human", "product")

        classification = result.get("classification", "unknown")

        # Escape special characters for HTML
        product_name_escaped = self.escape_html(product_name)
        company_escaped = self.escape_html(company)
        country_escaped = self.escape_html(country)

        # Try to get a more readable country name for display
        country_name = self.get_country_name_from_code(country_code)
        if country_name:
            country = f"{country_name} ({country_code})"
            country_escaped = self.escape_html(country)

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
        elif classification == "european_adversary":
            category = "European Adversary"
            color = "#ff0000"  # Red
            self.play_sound(False)  # Error sound
        elif classification == "neutral":
            category = "Neutral"
            color = "#999999"  # Gray
            # No sound for neutral classification
        else:
            category = "Unknown"
            color = "#cc9900"  # Yellow-orange

        # Set product info with parent company if available
        if parent_company and parent_company != company:
            # Get readable parent company country name
            parent_company_escaped = self.escape_html(parent_company)
            parent_country_name = self.get_country_name_from_code(parent_country_code)
            parent_country_display = parent_country_code
            if parent_country_name:
                parent_country_display = f"{parent_country_name} ({parent_country_code})"
            parent_country_escaped = self.escape_html(parent_country_display)

            # Include parent company in the display
            self.product_info.setText(
                f"<b>{product_name_escaped}</b> by <b>{company_escaped}</b> from <b>{country_escaped}</b><br/>"
                f"<span style='font-size: 12px;'>Parent company: <b>{parent_company_escaped}</b> from <b>{parent_country_escaped}</b></span>"
            )
        else:
            # Standard display without parent company
            self.product_info.setText(
                f"<b>{product_name_escaped}</b> by <b>{company_escaped}</b> from <b>{country_escaped}</b>"
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
        )

        # Add parent company info if available and different
        if parent_company and parent_company != company:
            parent_country_display = parent_country_code
            parent_country_name = self.get_country_name_from_code(parent_country_code)
            if parent_country_name:
                parent_country_display = f"{parent_country_name} ({parent_country_code})"

            detailed_text += f"Parent Company: {parent_company}\n"
            detailed_text += f"Parent Company HQ: {parent_country_display}\n"

        # Add classification and item type
        detailed_text += f"Classification: {classification}\n"
        if item_type and item_type != "product":
            detailed_text += f"Detected Type: {item_type}\n"
        detailed_text += "\n"

        # Add identification rationale with better formatting
        rationale = result.get("identification_rationale", "")
        if rationale:
            detailed_text += f"Identification rationale:\n{rationale}\n\n"

        # Add thinking output if available
        thinking = result.get("potential_alternative_thinking", "")
        if thinking:
            detailed_text += f"Alternative Analysis:\n{thinking}\n\n"

        # Add debugging information if available
        debug_text = "Debugging Information:\n"
        has_debug = False

        request_id = result.get("id")
        if request_id:
            debug_text += f"Request ID: {request_id}\n"
            has_debug = True

        input_tokens = result.get("input_tokens")
        if input_tokens:
            debug_text += f"Input Tokens: {input_tokens}\n"
            has_debug = True

        output_tokens = result.get("output_tokens")
        if output_tokens:
            debug_text += f"Output Tokens: {output_tokens}\n"
            has_debug = True

        total_tokens = result.get("total_tokens")
        if total_tokens:
            debug_text += f"Total Tokens: {total_tokens}\n"
            has_debug = True

        if has_debug:
            detailed_text += debug_text + "\n"

        # Update the details view
        self.details_view.setText(detailed_text)

        # Handle alternatives - check both potential_alternatives (original format) and alternatives (new format)
        alternatives = result.get("alternatives", result.get("potential_alternatives", []))

        if alternatives:
            self.clear_alt_buttons()
            self.alternatives_label.setVisible(True)
            self.alternatives_widget.setVisible(True)

            for alt in alternatives:
                # Handle both new and old format
                if "name" in alt:
                    # New format
                    alt_name = alt.get("name", "Unknown")
                    alt_company = ""
                    if "by" in alt:
                        alt_company = alt.get("by", "").replace("by ", "")

                    alt_country = alt.get("country", "")
                    country_code = alt.get("country_code", "")
                    alt_description = alt.get("information", "")

                    # Try to extract more info from the information field
                    alt_info = alt.get("information", "")
                    if alt_info and not alt_company and "by " in alt_info:
                        # Extract company name from "by Company (Country)" format
                        parts = alt_info.split("by ")
                        if len(parts) > 1:
                            company_part = parts[1]
                            if " (" in company_part:
                                alt_company = company_part.split(" (")[0].strip()
                                if not alt_country and "(" in company_part and ")" in company_part:
                                    # Extract country from parentheses if not already set
                                    country_part = company_part.split("(")[1].split(")")[0].strip()
                                    alt_country = country_part
                else:
                    # Old format
                    alt_name = alt.get("product_name", "Unknown")
                    alt_company = alt.get("company", "")
                    alt_country = alt.get("country", "")
                    country_code = ""
                    alt_description = alt.get("description", "")

                # Skip if no name
                if not alt_name or alt_name == "Unknown":
                    continue

                # Create a container for this alternative
                alt_container = QWidget()
                alt_container_layout = QVBoxLayout(alt_container)
                alt_container_layout.setContentsMargins(0, 0, 0, 0)
                alt_container_layout.setSpacing(4)

                # Create button with proper information
                button_text = alt_name
                tooltip_text = ""

                # Add country and company info if available
                country_flag = self.get_country_flag_emoji(alt_country, country_code)
                if country_flag:
                    button_text = f"{country_flag} {alt_name}"

                # Escape special characters for tooltip
                # alt_name_escaped = self.escape_html(alt_name)
                alt_company_escaped = self.escape_html(alt_company)
                alt_country_escaped = self.escape_html(alt_country)

                if alt_company:
                    tooltip_text = f"by {alt_company_escaped}"
                    if alt_country:
                        tooltip_text += f" ({alt_country_escaped})"
                elif alt_country:
                    tooltip_text = f"Country: {alt_country_escaped}"

                # Create a button layout
                alt_button = QPushButton(button_text)
                if tooltip_text:
                    alt_button.setToolTip(tooltip_text)

                # Style the button
                alt_button.setStyleSheet("""
                    QPushButton {
                        background-color: #3174ad;
                        color: white;
                        border: 1px solid #2c6ca0;
                        padding: 4px 8px;
                        border-radius: 4px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #3c87c7;
                    }
                """)

                # Connect the button to a search function
                search_term = alt_name
                if alt_company:
                    search_term += f" {alt_company}"
                alt_button.clicked.connect(lambda _, term=search_term: self.search_alternative(term))

                # Add button to container
                alt_container_layout.addWidget(alt_button)

                # Add description if available
                if alt_description:
                    desc_label = QLabel(alt_description)
                    desc_label.setWordWrap(True)
                    desc_label.setStyleSheet("""
                        QLabel {
                            color: #aaa;
                            font-size: 12px;
                            padding: 2px 8px;
                            margin-left: 16px;
                        }
                    """)
                    alt_container_layout.addWidget(desc_label)

                # Add a separator
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("QFrame { background-color: #444; margin: 8px 0; }")
                separator.setMaximumHeight(1)
                alt_container_layout.addWidget(separator)

                # Add to layout
                self.alternatives_layout.addWidget(alt_container)
        else:
            self.alternatives_label.setVisible(False)
            self.alternatives_widget.setVisible(False)

        # Reset analyze button
        self.analyze_button.setText("Analyze Product")
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

        # Add feedback buttons
        self.add_feedback_buttons()

    def add_feedback_buttons(self):
        """Add feedback buttons to the results layout."""
        # If feedback buttons already exist, remove them first
        if hasattr(self, 'feedback_widget'):
            self.main_layout.removeWidget(self.feedback_widget)
            self.feedback_widget.deleteLater()

        # Create container for feedback buttons
        self.feedback_widget = QWidget()
        feedback_layout = QHBoxLayout(self.feedback_widget)

        # Add feedback label
        feedback_label = QLabel("Was this analysis helpful?")
        feedback_layout.addWidget(feedback_label)

        # Add thumbs up button
        thumbs_up_button = QPushButton("👍 Yes")
        thumbs_up_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        thumbs_up_button.clicked.connect(self.on_thumbs_up_clicked)
        feedback_layout.addWidget(thumbs_up_button)

        # Add thumbs down button
        thumbs_down_button = QPushButton("👎 No")
        thumbs_down_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        thumbs_down_button.clicked.connect(self.on_thumbs_down_clicked)
        feedback_layout.addWidget(thumbs_down_button)

        # Add spacer to right-align buttons
        feedback_layout.addStretch()

        # Add to main layout
        self.main_layout.addWidget(self.feedback_widget)

    def on_thumbs_up_clicked(self):
        """Handle thumbs up button click - positive feedback."""
        if not self.current_result or "id" not in self.current_result:
            return

        # Send positive feedback
        response = self.api.send_feedback(is_positive=True)

        if response.get("status") == "success":
            QMessageBox.information(self.window, "Feedback Sent", "Thanks for your feedback!")

    def on_thumbs_down_clicked(self):
        """Handle thumbs down button click - show feedback dialog."""
        if not self.current_result or "id" not in self.current_result:
            return

        # Create and show feedback dialog
        dialog = FeedbackDialog(self.window)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            # Get feedback data
            feedback_text = dialog.comments_edit.toPlainText()

            # Send the feedback
            response = self.api.send_feedback(
                is_positive=False,
                wrong_product=dialog.product_check.isChecked(),
                wrong_brand=dialog.brand_check.isChecked(),
                wrong_country=dialog.country_check.isChecked(),
                wrong_classification=dialog.classification_check.isChecked(),
                wrong_alternatives=dialog.alternatives_check.isChecked(),
                wrong_other=dialog.other_check.isChecked(),
                feedback_text=feedback_text
            )

            if response.get("status") == "success":
                QMessageBox.information(self.window, "Feedback Sent", "Thanks for your feedback!")
            else:
                QMessageBox.warning(self.window, "Error", f"Failed to send feedback: {response.get('message', 'Unknown error')}")

    def search_alternative(self, name):
        """Search for an alternative product."""
        import webbrowser
        search_url = f"https://www.google.com/search?q={name.replace(' ', '+')}"
        webbrowser.open(search_url)

    def get_country_flag_emoji(self, country_name, country_code=""):
        """Get flag emoji for a country name."""
        if not country_name and not country_code:
            return "🇪🇺 EU"

        # Handle 3-letter ISO country codes
        if country_code and len(country_code) == 3:
            # Map of 3-letter codes to 2-letter codes for emoji conversion
            code_map = {
                "AUT": "AT", "BEL": "BE", "BGR": "BG", "HRV": "HR", "CYP": "CY",
                "CZE": "CZ", "DNK": "DK", "EST": "EE", "FIN": "FI", "FRA": "FR",
                "DEU": "DE", "GRC": "GR", "HUN": "HU", "IRL": "IE", "ITA": "IT",
                "LVA": "LV", "LTU": "LT", "LUX": "LU", "MLT": "MT", "NLD": "NL",
                "POL": "PL", "PRT": "PT", "ROU": "RO", "SVK": "SK", "SVN": "SI",
                "ESP": "ES", "SWE": "SE", "GBR": "GB", "CHE": "CH", "NOR": "NO",
                "ISL": "IS", "LIE": "LI", "USA": "US", "CAN": "CA", "JPN": "JP",
                "CHN": "CN", "RUS": "RU", "KOR": "KR", "IND": "IN", "BRA": "BR",
                "AUS": "AU", "NZL": "NZ", "MEX": "MX", "ZAF": "ZA", "TUR": "TR",
                "ISR": "IL", "ARE": "AE", "ARG": "AR", "SGP": "SG", "MYS": "MY",
                "IDN": "ID", "THA": "TH", "VNM": "VN", "PAK": "PK",
            }

            # Convert to 2-letter code if available
            if country_code in code_map:
                two_letter = code_map[country_code]
                # Convert to flag emoji (regional indicator symbols)
                flag = chr(ord(two_letter[0]) + 127397) + chr(ord(two_letter[1]) + 127397)
                return f"{flag} {country_code}"
            else:
                # Return EU flag if code not found
                return "🇪🇺 EU"

        # Use country code if provided (usually more reliable)
        if country_code and len(country_code) == 2:
            # Convert country code to regional indicator symbols
            code = country_code.upper()
            return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397) + " " + code

        # Common European countries (for more reliable mapping)
        country_map = {
            "germany": "🇩🇪 DE",
            "france": "🇫🇷 FR",
            "italy": "🇮🇹 IT",
            "spain": "🇪🇸 ES",
            "austria": "🇦🇹 AT",
            "netherlands": "🇳🇱 NL",
            "belgium": "🇧🇪 BE",
            "sweden": "🇸🇪 SE",
            "switzerland": "🇨🇭 CH",
            "united kingdom": "🇬🇧 GB",
            "uk": "🇬🇧 GB",
            "usa": "🇺🇸 US",
            "united states": "🇺🇸 US",
            "poland": "🇵🇱 PL",
            "finland": "🇫🇮 FI",
            "denmark": "🇩🇰 DK",
            "greece": "🇬🇷 GR",
            "czech republic": "🇨🇿 CZ",
            "czechia": "🇨🇿 CZ",
            "portugal": "🇵🇹 PT",
            "ireland": "🇮🇪 IE",
            "hungary": "🇭🇺 HU",
            "japan": "🇯🇵 JP",
            "china": "🇨🇳 CN",
            "canada": "🇨🇦 CA",
            "australia": "🇦🇺 AU",
            "taiwan": "🇹🇼 TW",
            "south korea": "🇰🇷 KR",
            "korea": "🇰🇷 KR",
            "india": "🇮🇳 IN",
            "russia": "🇷🇺 RU",
            "brazil": "🇧🇷 BR",
            "mexico": "🇲🇽 MX",
            "norway": "🇳🇴 NO",
            "pakistan": "🇵🇰 PK",
        }

        # Try to match the country name
        country_lower = country_name.lower() if country_name else ""
        if country_lower in country_map:
            return country_map[country_lower]

        # Check for partial matches
        for key, flag in country_map.items():
            if country_lower and (key in country_lower or country_lower in key):
                return flag

        # Fallback to European flag if not found
        return "🇪🇺 EU"

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

    def escape_html(self, text):
        """Escape special characters for HTML markup.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for use in HTML markup
        """
        if not text:
            return ""

        # Convert the text to string if it's not already
        if not isinstance(text, str):
            text = str(text)

        # Replace special characters with their escaped versions
        replacements = [
            ('&', '&amp;'),   # This must be first to avoid double-escaping
            ('<', '&lt;'),
            ('>', '&gt;'),
            ('"', '&quot;'),
            ("'", '&#39;'),
        ]

        for old, new in replacements:
            text = text.replace(old, new)

        return text

    def get_country_name_from_code(self, code):
        """Convert a country code to a country name."""
        if not code:
            return ""

        # Map of ISO 3166-1 alpha-3 codes to country names
        country_codes = {
            "AUT": "Austria",
            "BEL": "Belgium",
            "BGR": "Bulgaria",
            "HRV": "Croatia",
            "CYP": "Cyprus",
            "CZE": "Czech Republic",
            "DNK": "Denmark",
            "EST": "Estonia",
            "FIN": "Finland",
            "FRA": "France",
            "DEU": "Germany",
            "GRC": "Greece",
            "HUN": "Hungary",
            "IRL": "Ireland",
            "ITA": "Italy",
            "LVA": "Latvia",
            "LTU": "Lithuania",
            "LUX": "Luxembourg",
            "MLT": "Malta",
            "NLD": "Netherlands",
            "POL": "Poland",
            "PRT": "Portugal",
            "ROU": "Romania",
            "SVK": "Slovakia",
            "SVN": "Slovenia",
            "ESP": "Spain",
            "SWE": "Sweden",
            "GBR": "United Kingdom",
            "CHE": "Switzerland",
            "NOR": "Norway",
            "ISL": "Iceland",
            "LIE": "Liechtenstein",
            "USA": "United States",
            "CAN": "Canada",
            "JPN": "Japan",
            "CHN": "China",
            "RUS": "Russia",
            "KOR": "South Korea",
            "IND": "India",
            "BRA": "Brazil",
            "AUS": "Australia",
            "NZL": "New Zealand",
            "MEX": "Mexico",
            "ZAF": "South Africa",
            "TUR": "Turkey",
            "ISR": "Israel",
            "ARE": "United Arab Emirates",
            "ARG": "Argentina",
            "SGP": "Singapore",
            "MYS": "Malaysia",
            "IDN": "Indonesia",
            "THA": "Thailand",
            "VNM": "Vietnam",
            "PAK": "Pakistan",
        }

        return country_codes.get(code, "")
