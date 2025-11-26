from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QIcon
from .resizable_widget import ResizableWidget
from pathlib import Path

class ButtonWidget(ResizableWidget):
    def __init__(self, topic, mqtt_client=None, parent=None, config=None):
        super().__init__("button", topic, mqtt_client, parent, config)
        self.init_content()
        self.connect_signals()
        self.apply_config()

    def init_content(self):
        """Initialize the content of the button widget."""
        self.button = QPushButton("Button")
        self.content_layout.addWidget(self.button)

    def connect_signals(self):
        """Connect signals for the button."""
        self.button.clicked.connect(self.on_button_clicked)
        if self.mqtt_client:
            input_topic = self.config.get('button_input_topic', self.topic)
            if input_topic:
                self.mqtt_client.subscribe(input_topic)
                self.mqtt_client.message_received.connect(self.on_message_received)

    def on_button_clicked(self):
        """Handle button click."""
        try:
            current_state = self.button.isChecked()
            on_payload = self.config.get('button_on_value', '1')
            off_payload = self.config.get('button_off_value', '0')
            payload = on_payload if not current_state else off_payload

            # Toggle the button's checked state and publish
            self.button.setChecked(not current_state)
            if self.mqtt_client and self.mqtt_client.connected:
                self.mqtt_client.publish(self.topic, payload)
                if self.error_state: self.clear_error()
            else:
                raise Exception("MQTT client not connected")
        except Exception as e:
            self.show_error(f"Publish failed: {e}")

    def on_message_received(self, topic, message):
        """Handle incoming MQTT messages for state updates."""
        input_topic = self.config.get('button_input_topic', self.topic)
        if topic == input_topic:
            try:
                on_payload = self.config.get('button_on_value', '1')
                is_on = str(message).strip() == on_payload
                self.button.setChecked(is_on)
                if self.error_state: self.clear_error()
            except RuntimeError:
                pass # Widget might be deleted

    def apply_config(self):
        """Apply configuration to the widget."""
        super().apply_config()

        # Update button text, icon, and styling
        self._update_button_icon_and_text()

    def _update_button_icon_and_text(self):
        """Update button icon, text, and styling based on config"""
        # Get style properties from config, with reasonable fallbacks
        accent_color = self.config.get('accent_color', '#0d6efd')
        button_bg_color = self.config.get('button_bg_color', '#343a40')
        button_text_color = self.config.get('button_text_color', self.config.get('text_color', '#D9D9D9'))
        border_color = self.config.get('border_color', '#6c757d')
        font_size = self.config.get('font_size', 12)

        # Get content properties from config
        icon_data = self.config.get('icon_data', '')
        is_text_icon = self.config.get('icon_is_text', False)
        icon_size = self.config.get('icon_size', 24)
        icon_position = self.config.get('icon_position', 'left')
        # Use 'or self.topic' to fall back if display_name is an empty string
        display_name = self.config.get('display_name') or self.topic
        show_text = self.config.get('show_text', True)

        # Clear existing icon and text
        self.button.setIcon(QIcon())
        self.button.setText("")

        current_text = ""
        current_font_size = font_size

        if icon_data:
            if is_text_icon:
                if icon_position == 'only' or not show_text:
                    current_text = icon_data
                    current_font_size = icon_size  # Use icon size for emoji-only button
                elif icon_position == 'left':
                    current_text = f"{icon_data} {display_name}"
                else:  # right
                    current_text = f"{display_name} {icon_data}"
            else:  # Image icon
                if Path(icon_data).exists():
                    pixmap = QPixmap(icon_data)
                    if not pixmap.isNull():
                        self.button.setIcon(QIcon(pixmap))
                        self.button.setIconSize(pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio).size())
                if show_text and icon_position != 'only':
                    current_text = display_name
        elif show_text:
            current_text = display_name
        
        self.button.setText(current_text)
        
        # Apply stylesheet
        self.button.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_bg_color};
                color: {button_text_color};
                border: 1px solid {border_color};
                padding: 8px;
                border-radius: 4px;
                font-size: {current_font_size}px;
            }}
            QPushButton:checked {{
                background-color: {accent_color};
                border: 1px solid {accent_color};
            }}
            QPushButton:hover {{
                border-color: {accent_color};
            }}
        """)

    def get_value(self):
        return str(self.button.isChecked())