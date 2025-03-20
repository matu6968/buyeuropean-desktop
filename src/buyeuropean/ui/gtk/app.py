"""GTK 4 implementation of BuyEuropean frontend."""

import os
import gi
import threading
from pathlib import Path
import subprocess

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, GLib, Gio, GdkPixbuf, Adw

# Try to import GStreamer for better sound handling
try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
    HAS_GST = True
except (ImportError, ValueError):
    HAS_GST = False

from buyeuropean.api import BuyEuropeanAPI

# Define sound file paths
SOUND_DIR = Path(__file__).parent.parent.parent / "sounds"
SUCCESS_SOUND_OGG = SOUND_DIR / "success.ogg"
ERROR_SOUND_OGG = SOUND_DIR / "error.ogg"
SUCCESS_SOUND_WAV = SOUND_DIR / "success.wav"
ERROR_SOUND_WAV = SOUND_DIR / "error.wav"

# Define logo path
LOGO_PATH = Path(__file__).parent / "logos" / "logo_buyeuropean.png"

class GtkApp:
    """GTK 4 application for BuyEuropean."""
    
    def __init__(self):
        """Initialize the GTK application."""
        self.api = BuyEuropeanAPI()
        # Use Adw.Application for better GNOME integration
        self.app = Adw.Application(application_id="io.buyeuropean.desktop")
        self.app.connect('activate', self.on_activate)
        
        # Initialize sound players if GStreamer is available
        self.success_player = None
        self.error_player = None
        
        if HAS_GST:
            self.setup_sound_players()
    
    def setup_sound_players(self):
        """Set up GStreamer sound players for better audio handling."""
        self.success_player = Gst.ElementFactory.make("playbin", "success")
        self.error_player = Gst.ElementFactory.make("playbin", "error")
        
        # Try WAV files first, then fall back to OGG
        if SUCCESS_SOUND_WAV.exists():
            self.success_player.set_property("uri", f"file://{SUCCESS_SOUND_WAV.absolute()}")
        elif SUCCESS_SOUND_OGG.exists():
            self.success_player.set_property("uri", f"file://{SUCCESS_SOUND_OGG.absolute()}")
            
        if ERROR_SOUND_WAV.exists():
            self.error_player.set_property("uri", f"file://{ERROR_SOUND_WAV.absolute()}")
        elif ERROR_SOUND_OGG.exists():
            self.error_player.set_property("uri", f"file://{ERROR_SOUND_OGG.absolute()}")
    
    def on_activate(self, app):
        """Handle application activation."""
        # Create the main window as an Adw.ApplicationWindow
        self.window = Adw.ApplicationWindow(application=app, title="BuyEuropean")
        self.window.set_default_size(800, 600)
        
        # Create a header bar with modern GNOME style
        self.header_bar = Adw.HeaderBar()
        
        # Create title widget with European flag emoji and text
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Title label with emoji
        title_label = Gtk.Label()
        title_label.set_markup("<b>🇪🇺 BuyEuropean Desktop</b>")
        title_box.append(title_label)
        
        self.header_bar.set_title_widget(title_box)
        
        # Create main content box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Add the header bar
        main_box.append(self.header_bar)
        
        # Create a scrollable content area
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)
        
        # Create content box with proper margins (following GNOME HIG)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=24)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Add title with proper GNOME styling
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        title_box.set_halign(Gtk.Align.CENTER)
        
        # Add app logo in title area (check if logo file exists)
        logo_exists = LOGO_PATH.exists()
        if logo_exists:
            try:
                # In GTK4, we use Gtk.Picture.new_for_file instead of new_for_pixbuf
                app_image = Gtk.Picture.new_for_filename(str(LOGO_PATH))
                # Set a consistent size
                app_image.set_size_request(128, 128)
                app_image.set_margin_bottom(12)
                title_box.append(app_image)
            except Exception as e:
                print(f"Error loading logo: {e}")
                # Fallback to European flag emoji
                emoji_label = Gtk.Label()
                emoji_label.set_markup("<span size='72000'>🇪🇺</span>")
                emoji_label.set_margin_bottom(12)
                title_box.append(emoji_label)
        else:
            # Fallback to European flag emoji
            emoji_label = Gtk.Label()
            emoji_label.set_markup("<span size='72000'>🇪🇺</span>")
            emoji_label.set_margin_bottom(12)
            title_box.append(emoji_label)
        
        # Add title label with GNOME standard styling
        title_label = Gtk.Label()
        title_label.set_markup("<span size='xx-large' weight='bold'>BuyEuropean</span>")
        title_box.append(title_label)
        
        # Add subtitle label
        subtitle_label = Gtk.Label()
        subtitle_label.set_markup("<span size='large'>Check if products are from European companies</span>")
        title_box.append(subtitle_label)
        
        content_box.append(title_box)
        
        # Add action area with product selection
        action_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        action_box.set_margin_top(12)
        
        # Create a card UI for the product selection
        selection_card = Adw.PreferencesGroup()
        
        # Add button to select image with icon
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.CENTER)
        
        select_image_button = Gtk.Button()
        select_image_button.add_css_class("suggested-action")  # Blue accent color for primary action
        
        # Create a box for the button content with icon and label
        button_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Add icon to the button content box
        image_icon = Gtk.Image.new_from_icon_name("document-open-symbolic")
        button_content.append(image_icon)
        
        # Add label to the button content box
        button_label = Gtk.Label(label="Select Product Image")
        button_content.append(button_label)
        
        # Set the content box as the button's child
        select_image_button.set_child(button_content)
        
        select_image_button.connect("clicked", self.on_select_image_clicked)
        button_box.append(select_image_button)
        
        selection_card.add(button_box)
        action_box.append(selection_card)
        
        # Add image preview area with frame
        image_frame = Gtk.Frame()
        image_frame.set_margin_top(12)
        
        self.image_preview = Gtk.Picture()
        self.image_preview.set_size_request(300, 300)
        self.image_preview.set_halign(Gtk.Align.CENTER)
        image_frame.set_child(self.image_preview)
        action_box.append(image_frame)
        
        # Add analyze button with icon
        button_action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_action_box.set_halign(Gtk.Align.CENTER)
        button_action_box.set_margin_top(12)
        
        self.analyze_button = Gtk.Button()
        analyze_button_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        analyze_icon = Gtk.Image.new_from_icon_name("find-location-symbolic")
        analyze_button_content.append(analyze_icon)
        
        analyze_label = Gtk.Label(label="Analyze Product")
        analyze_button_content.append(analyze_label)
        
        self.analyze_button.set_child(analyze_button_content)
        self.analyze_button.add_css_class("suggested-action")
        self.analyze_button.connect("clicked", self.on_analyze_clicked)
        self.analyze_button.set_sensitive(False)
        
        button_action_box.append(self.analyze_button)
        action_box.append(button_action_box)
        
        content_box.append(action_box)
        
        # Add results area with card UI
        self.results_card = Adw.PreferencesGroup()
        self.results_card.set_margin_top(24)
        
        # Results header (initially hidden)
        self.result_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Results label with icon
        self.result_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.result_icon = Gtk.Image()
        self.result_icon.set_pixel_size(32)
        self.result_header.append(self.result_icon)
        
        self.result_label = Gtk.Label()
        self.result_label.set_halign(Gtk.Align.START)
        self.result_header.append(self.result_label)
        
        self.result_box.append(self.result_header)
        
        # Add classification label with styling
        self.classification_label = Gtk.Label()
        self.classification_label.set_halign(Gtk.Align.START)
        self.classification_label.set_margin_start(44)  # To align with the text from the icon
        self.result_box.append(self.classification_label)
        
        self.results_card.add(self.result_box)
        
        # Add detailed results with scrolling in a card
        details_card = Adw.PreferencesGroup()
        details_card.set_margin_top(12)
        
        details_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        details_icon = Gtk.Image.new_from_icon_name("dialog-information-symbolic")
        details_header.append(details_icon)
        
        details_title = Gtk.Label(label="Product Details")
        details_title.set_halign(Gtk.Align.START)
        details_header.append(details_title)
        
        details_scroll = Gtk.ScrolledWindow()
        details_scroll.set_min_content_height(200)
        details_scroll.set_vexpand(True)
        
        self.details_view = Gtk.TextView()
        self.details_view.set_editable(False)
        self.details_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.details_view.add_css_class("card")
        self.details_buffer = self.details_view.get_buffer()
        
        details_scroll.set_child(self.details_view)
        
        details_card.add(details_header)
        details_card.add(details_scroll)
        
        content_box.append(self.results_card)
        content_box.append(details_card)
        
        # Alternative buttons area
        self.alt_buttons_group = Adw.PreferencesGroup()
        self.alt_buttons_group.set_margin_top(12)
        self.alt_buttons_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        alt_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        alt_icon = Gtk.Image.new_from_icon_name("starred-symbolic")
        alt_header.append(alt_icon)
        
        alt_title = Gtk.Label(label="European Alternatives")
        alt_title.set_halign(Gtk.Align.START)
        alt_header.append(alt_title)
        
        self.alt_buttons_group.add(alt_header)
        self.alt_buttons_group.add(self.alt_buttons_box)
        
        content_box.append(self.alt_buttons_group)
        
        # Set the child for the scrolled window
        scrolled_window.set_child(content_box)
        main_box.append(scrolled_window)
        
        # Set the window content
        self.window.set_content(main_box)
        self.window.present()
        
        # Store the selected image path
        self.selected_image_path = None
        
        # Initially hide results sections
        self.results_card.set_visible(False)
        self.alt_buttons_group.set_visible(False)
        
    def on_select_image_clicked(self, button):
        """Handle image selection button click."""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select a Product Image")
        
        filter = Gtk.FileFilter()
        filter.set_name("Image files")
        filter.add_mime_type("image/jpeg")
        filter.add_mime_type("image/png")
        filter.add_pattern("*.jpg")
        filter.add_pattern("*.jpeg")
        filter.add_pattern("*.png")
        
        dialog.set_default_filter(filter)
        
        dialog.open(self.window, None, self.on_file_dialog_response)
        
    def on_file_dialog_response(self, dialog, result):
        """Handle file dialog response."""
        try:
            file = dialog.open_finish(result)
            if file:
                self.selected_image_path = file.get_path()
                # Set preview image
                self.image_preview.set_filename(self.selected_image_path)
                # Enable the analyze button
                self.analyze_button.set_sensitive(True)
        except Exception as e:
            print(f"Error selecting file: {e}")
    
    def on_analyze_clicked(self, button):
        """Handle analyze button click."""
        if not self.selected_image_path:
            return
            
        # Disable the button during analysis
        self.analyze_button.set_sensitive(False)
        
        # Update button with a spinner
        original_child = self.analyze_button.get_child()
        spinner = Gtk.Spinner()
        spinner.start()
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        spinner_box.append(spinner)
        spinner_box.append(Gtk.Label(label="Analyzing..."))
        self.analyze_button.set_child(spinner_box)
        
        # Clear previous results
        self.details_buffer.set_text("")
        self.result_label.set_text("")
        self.classification_label.set_text("")
        
        # Clear any alternative buttons
        self.clear_alt_buttons()
        
        # Hide results sections until we have new results
        self.results_card.set_visible(False)
        self.alt_buttons_group.set_visible(False)
            
        # Run analysis in a thread to prevent UI blocking
        threading.Thread(target=self.analyze_image, daemon=True).start()
        
    def analyze_image(self):
        """Analyze the selected image in a background thread."""
        try:
            result = self.api.analyze_product(Path(self.selected_image_path))
            
            # Update UI in the main thread
            GLib.idle_add(self.update_results, result)
        except Exception as e:
            GLib.idle_add(self.show_error, str(e))
    
    def update_results(self, result):
        """Update the UI with analysis results."""
        if not result:
            self.show_error("Failed to analyze product. Please try again.")
            return
            
        # Update the main result label
        product_name = result.get("identified_product_name", "Unknown product")
        company = result.get("identified_company", "Unknown company")
        country = result.get("identified_headquarters", "Unknown country")
        classification = result.get("classification", "unknown")
        
        # Handle classification properly with GNOME-style icons and colors
        icon_name = "emblem-default-symbolic"
        css_class = "success"
        if classification == "european_country":
            category = "European"
            icon_name = "emblem-ok-symbolic"
            css_class = "success"
            self.play_sound(True)  # Success sound
        elif classification == "european_ally":
            category = "European Ally"
            icon_name = "emblem-ok-symbolic"
            css_class = "success"
            self.play_sound(True)  # Success sound
        elif classification == "european_sceptic":
            category = "European Sceptic"
            icon_name = "dialog-warning-symbolic"
            css_class = "warning"
            self.play_sound(False)  # Error sound
        else:
            category = "Unknown"
            icon_name = "dialog-question-symbolic"
            css_class = "dim-label"
            
        # Set the result icon
        self.result_icon.set_from_icon_name(icon_name)
            
        # Create result header with product information
        self.result_label.set_markup(
            f"<b>{product_name}</b> by <b>{company}</b> from <b>{country}</b>"
        )
        
        # Set classification with appropriate styling
        self.classification_label.set_markup(f"<span size='large'><b>{category}</b></span>")
        self.classification_label.add_css_class(css_class)
        
        # Make results visible
        self.results_card.set_visible(True)
        
        # Update detailed results with improved formatting
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
        
        # Update the text buffer
        self.details_buffer.set_text(detailed_text)
        
        # Add potential alternatives if available and create buttons
        alternatives = result.get("potential_alternatives", [])
        if alternatives:
            self.clear_alt_buttons()
            
            # Show the alternatives group
            self.alt_buttons_group.set_visible(True)
            
            for alt in alternatives:
                alt_name = alt.get('product_name', 'N/A')
                alt_company = alt.get('company', 'N/A')
                alt_country = alt.get('country', 'N/A')
                
                # Create a row for each alternative
                alt_row = Adw.ActionRow()
                alt_row.set_title(alt_name)
                alt_row.set_subtitle(f"by {alt_company} ({alt_country})")
                
                # Use country flag emoji based on country name
                country_emoji = self.get_country_flag_emoji(alt_country)
                country_label = Gtk.Label()
                country_label.set_markup(f"<span size='large'>{country_emoji}</span>")
                country_label.set_margin_end(6)
                alt_row.add_prefix(country_label)
                
                # Add a button to learn more
                learn_button = Gtk.Button()
                learn_button.set_icon_name("web-browser-symbolic")
                learn_button.set_tooltip_text(f"Learn more about {alt_name}")
                learn_button.add_css_class("flat")
                learn_button.connect("clicked", 
                                     lambda b, name=alt_name, company=alt_company: 
                                     self.open_search(f"{name} {company}"))
                
                alt_row.add_suffix(learn_button)
                self.alt_buttons_box.append(alt_row)
        else:
            self.alt_buttons_group.set_visible(False)
        
        # Add a disclamer saying AI results can make mistakes
        disclaimer = Gtk.Label(label="This is an AI-powered tool, as it can make mistakes. Please verify the information before making any decisions.")
        disclaimer.set_halign(Gtk.Align.START)
        disclaimer.set_margin_top(12)
        disclaimer.set_margin_bottom(12)
        disclaimer.set_margin_start(44)
        disclaimer.set_margin_end(44)
        self.results_card.add(disclaimer) 

        # Restore the analyze button
        analyze_button_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        analyze_icon = Gtk.Image.new_from_icon_name("find-location-symbolic")
        analyze_button_content.append(analyze_icon)
        analyze_label = Gtk.Label(label="Analyze Product")
        analyze_button_content.append(analyze_label)
        self.analyze_button.set_child(analyze_button_content)
        
        # Re-enable the analyze button
        self.analyze_button.set_sensitive(True)
    
    def open_search(self, search_term):
        """Open a web browser with a search for the given term."""
        import webbrowser
        search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
        webbrowser.open(search_url)
        
    def clear_alt_buttons(self):
        """Clear alternative buttons."""
        for child in self.alt_buttons_box:
            self.alt_buttons_box.remove(child)
        
    def show_error(self, message):
        """Show an error message in the UI."""
        # Show the results card for the error
        self.results_card.set_visible(True)
        
        # Set error icon
        self.result_icon.set_from_icon_name("dialog-error-symbolic")
        
        # Set error message
        self.result_label.set_markup(f"<span><b>Error</b></span>")
        self.classification_label.set_markup(f"<span>{message}</span>")
        self.classification_label.add_css_class("error")
        
        # Restore the analyze button
        analyze_button_content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        analyze_icon = Gtk.Image.new_from_icon_name("find-location-symbolic")
        analyze_button_content.append(analyze_icon)
        analyze_label = Gtk.Label(label="Analyze Product")
        analyze_button_content.append(analyze_label)
        self.analyze_button.set_child(analyze_button_content)
        
        # Re-enable the analyze button
        self.analyze_button.set_sensitive(True)
        
        # Play error sound
        self.play_sound(False)  # Error sound
        
        # Hide alternatives section
        self.alt_buttons_group.set_visible(False)
    
    def play_sound(self, is_success):
        """Play a sound based on the result using native GStreamer if available."""
        # Use GStreamer if available (preferred method)
        if HAS_GST and self.success_player and self.error_player:
            try:
                if is_success:
                    # Reset and play the success sound
                    self.success_player.set_state(Gst.State.NULL)
                    self.success_player.set_state(Gst.State.PLAYING)
                else:
                    # Reset and play the error sound
                    self.error_player.set_state(Gst.State.NULL)
                    self.error_player.set_state(Gst.State.PLAYING)
                return
            except Exception as e:
                print(f"Error playing sound with GStreamer: {e}")
        
        # Fallback to subprocess method if GStreamer isn't available
        sound_path = SUCCESS_SOUND_WAV if is_success else ERROR_SOUND_WAV
        if not sound_path.exists():
            sound_path = SUCCESS_SOUND_OGG if is_success else ERROR_SOUND_OGG
        
        if not sound_path.exists():
            print(f"Warning: Sound file not found: {sound_path}")
            return
            
        try:
            # Use GStreamer command-line tool
            subprocess.Popen(['gst-play-1.0', str(sound_path)], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error playing sound via subprocess: {e}")
            # Fallback to simple player if available
            try:
                subprocess.Popen(['ogg123', str(sound_path)], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            except:
                pass
    
    def get_country_flag_emoji(self, country_name):
        """Convert a country name to its flag emoji."""
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
        
        # Try to match the country name exactly
        if country_name in country_map:
            return country_map[country_name]
        
        # Check for partial matches
        for known_country, emoji in country_map.items():
            if known_country in country_name or country_name in known_country:
                return emoji
        
        # If no match found, return the EU flag as default
        return "🇪🇺"
    
    def run(self):
        """Run the application."""
        return self.app.run(None) 