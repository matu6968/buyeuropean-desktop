"""GTK 4 implementation of BuyEuropean frontend."""

import gi
import threading
from pathlib import Path
import subprocess
from gi.repository import Gtk, GLib

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Adw

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
        self.app.connect("activate", self.on_activate)

        # Initialize sound players if GStreamer is available
        self.success_player = None
        self.error_player = None

        if HAS_GST:
            self.setup_sound_players()

        # Store analysis result
        self.current_result = None

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

        # Create a toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()

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

        # Set the toast overlay as the content of the window and add the main box to it
        self.toast_overlay.set_child(main_box)
        self.window.set_content(self.toast_overlay)

        # Show the window
        self.window.present()

        # Store the selected image path
        self.selected_image_path = None

        # Initially hide results sections
        self.results_card.set_visible(False)
        self.alt_buttons_group.set_visible(False)

    def on_select_image_clicked(self):
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

    def on_analyze_clicked(self):
        """Handle analyze button click."""
        if not self.selected_image_path:
            return

        # Disable the button during analysis
        self.analyze_button.set_sensitive(False)

        # Update button with a spinner
        # original_child = self.analyze_button.get_child()
        spinner = Gtk.Spinner()
        spinner.start()
        spinner_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6
        )
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

        # Store the current result for use in feedback
        self.current_result = result

        # Update the main result label
        product_name = result.get("identified_product_name", "Unknown product")
        company = result.get(
            "identified_company", "Unknown company"
        )
        country_code = result.get("identified_company_headquarters", "")
        country = country_code  # Start with the code, will be expanded if available

        # Get the parent company information if available
        parent_company = result.get("ultimate_parent_company")
        parent_country_code = result.get("ultimate_parent_company_headquarters")

        # Get product/animal/human classification
        item_type = result.get("product_or_animal_or_human", "product")

        classification = result.get("classification", "unknown")

        # Escape special characters for markup
        product_name_escaped = self.escape_markup(product_name)
        company_escaped = self.escape_markup(company)
        country_escaped = self.escape_markup(country)

        # Try to get a more readable country name for display
        country_name = self.get_country_name_from_code(country_code)
        if country_name:
            country = f"{country_name} ({country_code})"
            country_escaped = self.escape_markup(country)

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
        elif classification == "european_adversary":
            category = "European Adversary"
            icon_name = "dialog-error-symbolic"
            css_class = "error"
            self.play_sound(False)  # Error sound
        elif classification == "neutral":
            category = "Neutral"
            icon_name = "dialog-information-symbolic"
            css_class = "dim-label"
            # No sound for neutral classification
        else:
            category = "Unknown"
            icon_name = "dialog-question-symbolic"
            css_class = "dim-label"

        # Set the result icon
        self.result_icon.set_from_icon_name(icon_name)

        # Create result header with product information
        if parent_company and parent_company != company:
            parent_company_escaped = self.escape_markup(parent_company)
            parent_country_name = self.get_country_name_from_code(parent_country_code)
            parent_country_display = parent_country_code
            if parent_country_name:
                parent_country_display = f"{parent_country_name} ({parent_country_code})"
            parent_country_escaped = self.escape_markup(parent_country_display)

            # Include parent company in display
            self.result_label.set_markup(
                f"<b>{product_name_escaped}</b> by <b>{company_escaped}</b> from <b>{country_escaped}</b>\n"
                f"<span size='small'>Parent company: <b>{parent_company_escaped}</b> from <b>{parent_country_escaped}</b></span>"
            )
        else:
            # Standard display without parent company
            self.result_label.set_markup(
                f"<b>{product_name_escaped}</b> by <b>{company_escaped}</b> from <b>{country_escaped}</b>"
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

        # Update the text buffer
        self.details_buffer.set_text(detailed_text)

        # Check both potential_alternatives (original format) and alternatives (new format)
        alternatives = result.get("alternatives", result.get("potential_alternatives", []))

        if alternatives:
            self.clear_alt_buttons()

            # Show the alternatives group
            self.alt_buttons_group.set_visible(True)

            for alt in alternatives:
                # Handle both new and old format
                if "name" in alt:
                    # New format
                    alt_name = alt.get("name", "Unknown")
                    alt_company = alt.get("by", "").replace("by ", "")
                    if not alt_company and "information" in alt:
                        # Try to extract company from information
                        info = alt.get("information", "")
                        if "by " in info:
                            parts = info.split("by ")
                            if len(parts) > 1:
                                company_part = parts[1]
                                if " (" in company_part:
                                    alt_company = company_part.split(" (")[0].strip()

                    alt_country = alt.get("country", "")
                    country_code = alt.get("country_code", "")
                    alt_description = alt.get("information", "")
                else:
                    # Old format
                    alt_name = alt.get("product_name", "Unknown")
                    alt_company = alt.get("company", "Unknown")
                    alt_country = alt.get("country", "")
                    country_code = ""
                    alt_description = alt.get("description", "")

                # Escape special characters for markup
                alt_name_escaped = self.escape_markup(alt_name)
                alt_company_escaped = self.escape_markup(alt_company)
                alt_country_escaped = self.escape_markup(alt_country)

                # Create a row for each alternative
                alt_row = Adw.ActionRow()
                alt_row.set_title(alt_name_escaped)

                # Set subtitle with company and country
                if alt_company:
                    if alt_country:
                        subtitle = f"by {alt_company_escaped} ({alt_country_escaped})"
                    else:
                        subtitle = f"by {alt_company_escaped}"
                    alt_row.set_subtitle(subtitle)

                # Use country flag emoji based on country name or code
                country_emoji = self.get_country_flag_emoji(alt_country, country_code)
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

                # Add description as a separate row if available
                if alt_description:
                    desc_label = Gtk.Label(label=alt_description)
                    desc_label.set_wrap(True)
                    desc_label.set_xalign(0)  # Align text to the left
                    desc_label.set_margin_start(32)  # Indent for better hierarchy
                    desc_label.set_margin_end(16)
                    desc_label.set_margin_top(4)
                    desc_label.set_margin_bottom(8)
                    desc_label.add_css_class("dim-label")  # Slightly dimmed text for description
                    self.alt_buttons_box.append(desc_label)

                    # Add a small separator after each alternative with description
                    separator = Gtk.Separator.new(Gtk.Orientation.HORIZONTAL)
                    separator.set_margin_top(8)
                    separator.set_margin_bottom(8)
                    separator.set_margin_start(16)
                    separator.set_margin_end(16)
                    self.alt_buttons_box.append(separator)
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

        # Add a feedback button
        feedback_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        feedback_box.set_halign(Gtk.Align.CENTER)
        feedback_box.set_margin_top(12)
        feedback_box.set_margin_bottom(12)

        # Thumbs up button
        thumbs_up_button = Gtk.Button()
        thumbs_up_button.set_icon_name("emblem-ok-symbolic")
        thumbs_up_button.set_tooltip_text("This analysis is correct")
        thumbs_up_button.add_css_class("suggested-action")
        thumbs_up_button.connect("clicked", self.on_thumbs_up_clicked)
        feedback_box.append(thumbs_up_button)

        # Add a small space
        spacing = Gtk.Box()
        spacing.set_size_request(10, -1)
        feedback_box.append(spacing)

        # Thumbs down button
        thumbs_down_button = Gtk.Button()
        thumbs_down_button.set_icon_name("dialog-warning-symbolic")
        thumbs_down_button.set_tooltip_text("This analysis has issues")
        thumbs_down_button.add_css_class("destructive-action")
        thumbs_down_button.connect("clicked", self.on_thumbs_down_clicked)
        feedback_box.append(thumbs_down_button)

        self.results_card.add(feedback_box)

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
            except Exception as e:
                print(f"Error playing sound via simple player: {e}")

    def get_country_flag_emoji(self, country_name, country_code=""):
        """Convert a country name to its flag emoji."""
        if not country_name and not country_code:
            return "🇪🇺"

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

        # Map of common European countries to their flag emojis (case-insensitive keys)
        country_map = {
            "austria": "🇦🇹",
            "belgium": "🇧🇪",
            "bulgaria": "🇧🇬",
            "croatia": "🇭🇷",
            "cyprus": "🇨🇾",
            "czech republic": "🇨🇿",
            "czechia": "🇨🇿",
            "denmark": "🇩🇰",
            "estonia": "🇪🇪",
            "finland": "🇫🇮",
            "france": "🇫🇷",
            "germany": "🇩🇪",
            "greece": "🇬🇷",
            "hungary": "🇭🇺",
            "ireland": "🇮🇪",
            "italy": "🇮🇹",
            "latvia": "🇱🇻",
            "lithuania": "🇱🇹",
            "luxembourg": "🇱🇺",
            "malta": "🇲🇹",
            "netherlands": "🇳🇱",
            "poland": "🇵🇱",
            "portugal": "🇵🇹",
            "romania": "🇷🇴",
            "slovakia": "🇸🇰",
            "slovenia": "🇸🇮",
            "spain": "🇪🇸",
            "sweden": "🇸🇪",
            "united kingdom": "🇬🇧",
            "uk": "🇬🇧",
            "switzerland": "🇨🇭",
            "norway": "🇳🇴",
            "iceland": "🇮🇸",
            "liechtenstein": "🇱🇮",
            "united states": "🇺🇸",
            "usa": "🇺🇸",
            "china": "🇨🇳",
            "japan": "🇯🇵",
            "south korea": "🇰🇷",
            "korea": "🇰🇷",
            "russia": "🇷🇺",
            "india": "🇮🇳",
            "brazil": "🇧🇷",
            "canada": "🇨🇦",
            "australia": "🇦🇺",
            "new zealand": "🇳🇿",
            "pakistan": "🇵🇰",
        }

        # Two-letter country codes
        country_codes = {
            "austria": "AT",
            "belgium": "BE",
            "bulgaria": "BG",
            "croatia": "HR",
            "cyprus": "CY",
            "czech republic": "CZ",
            "czechia": "CZ",
            "denmark": "DK",
            "estonia": "EE",
            "finland": "FI",
            "france": "FR",
            "germany": "DE",
            "greece": "GR",
            "hungary": "HU",
            "ireland": "IE",
            "italy": "IT",
            "latvia": "LV",
            "lithuania": "LT",
            "luxembourg": "LU",
            "malta": "MT",
            "netherlands": "NL",
            "poland": "PL",
            "portugal": "PT",
            "romania": "RO",
            "slovakia": "SK",
            "slovenia": "SI",
            "spain": "ES",
            "sweden": "SE",
            "united kingdom": "GB",
            "uk": "GB",
            "switzerland": "CH",
            "norway": "NO",
            "iceland": "IS",
            "liechtenstein": "LI",
            "united states": "US",
            "usa": "US",
            "china": "CN",
            "japan": "JP",
            "south korea": "KR",
            "korea": "KR",
            "russia": "RU",
            "india": "IN",
            "brazil": "BR",
            "canada": "CA",
            "australia": "AU",
            "new zealand": "NZ",
            "pakistan": "PK",
        }

        # Convert to lowercase for case-insensitive matching
        country_lower = country_name.lower() if country_name else ""

        # Try to match the country name exactly
        if country_lower in country_map:
            emoji = country_map[country_lower]
            code = country_codes.get(country_lower, "EU")
            return f"{emoji} {code}"

        # Check for partial matches
        for known_country, emoji in country_map.items():
            if country_lower and (known_country in country_lower or country_lower in known_country):
                code = country_codes.get(known_country, "EU")
                return f"{emoji} {code}"

        # If no match found, return the EU flag as default
        return "🇪🇺 EU"

    def on_thumbs_up_clicked(self, button):
        """Handle thumbs up button click - send positive feedback."""
        if not self.current_result or not self.current_result.get("id"):
            return

        # Run sending feedback in a separate thread
        threading.Thread(target=self.send_positive_feedback).start()

    def send_positive_feedback(self):
        """Send positive feedback in a separate thread."""
        response = self.api.send_feedback(is_positive=True)

        if response.get("status") == "success":
            # Show a success toast message
            GLib.idle_add(self.show_success_toast)

    def show_success_toast(self):
        """Show success toast message."""
        toast = Adw.Toast.new("Thanks for your feedback!")
        self.toast_overlay.add_toast(toast)

    def on_thumbs_down_clicked(self, button):
        """Handle thumbs down button click - show feedback dialog."""
        if not self.current_result or not self.current_result.get("id"):
            return

        # Run the feedback dialog creation in a separate thread
        threading.Thread(target=self.create_feedback_dialog).start()

    def create_feedback_dialog(self):
        # Create a dialog for feedback
        dialog = Adw.MessageDialog.new(self.window, "What was incorrect?", None)

        # Add the feedback options
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)

        # Add checkboxes for different issues
        self.product_check = Gtk.CheckButton.new_with_label("Product identification")
        content_box.append(self.product_check)

        self.brand_check = Gtk.CheckButton.new_with_label("Brand identification")
        content_box.append(self.brand_check)

        self.country_check = Gtk.CheckButton.new_with_label("Country identification")
        content_box.append(self.country_check)

        self.classification_check = Gtk.CheckButton.new_with_label("Classification")
        content_box.append(self.classification_check)

        self.alternatives_check = Gtk.CheckButton.new_with_label("Suggested alternatives")
        content_box.append(self.alternatives_check)

        self.other_check = Gtk.CheckButton.new_with_label("Other")
        content_box.append(self.other_check)

        # Add a text entry for additional comments
        comments_label = Gtk.Label(label="Any additional comments?")
        comments_label.set_halign(Gtk.Align.START)
        comments_label.set_margin_top(12)
        content_box.append(comments_label)

        self.feedback_text = Gtk.TextView()
        self.feedback_text.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.feedback_text.set_size_request(-1, 100)

        # Create a scrollable text entry
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(self.feedback_text)
        content_box.append(scrolled_window)

        dialog.set_extra_child(content_box)

        # Add buttons
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("submit", "Submit")
        dialog.set_response_appearance("submit", Adw.ResponseAppearance.SUGGESTED)

        # Connect response signal
        dialog.connect("response", self.on_feedback_dialog_response)

        # Show the dialog
        dialog.present()

    def on_feedback_dialog_response(self, dialog, response):
        """Handle feedback dialog response."""
        if response == "submit":
            # Get the feedback text from buffer
            buffer = self.feedback_text.get_buffer()
            start_iter = buffer.get_start_iter()
            end_iter = buffer.get_end_iter()
            feedback_text = buffer.get_text(start_iter, end_iter, False)

            # Send the feedback
            response = self.api.send_feedback(
                is_positive=False,
                wrong_product=self.product_check.get_active(),
                wrong_brand=self.brand_check.get_active(),
                wrong_country=self.country_check.get_active(),
                wrong_classification=self.classification_check.get_active(),
                wrong_alternatives=self.alternatives_check.get_active(),
                wrong_other=self.other_check.get_active(),
                feedback_text=feedback_text
            )

            if response.get("status") == "success":
                # Show a success toast message
                toast = Adw.Toast.new("Thanks for your feedback!")
                self.toast_overlay.add_toast(toast)

    def run(self):
        """Run the application."""
        return self.app.run(None)

    def escape_markup(self, text):
        """Escape special characters for GTK markup.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for use in GTK markup
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
            ("'", '&apos;'),
            ('"', '&quot;'),
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
