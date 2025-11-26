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

        # Update button icon
        self._update_button_icon()

        # Basic styling
        accent_color = self.config.get('accent_color', '#0d6efd')
        text_color = self.config.get('text_color', '#D9D9D9')
        font_size = self.config.get('font_size', 12)

        self.button.setStyleSheet(f"""
            QPushButton {{
                background-color: #343a40;
                color: {text_color};
                border: 1px solid #6c757d;
                padding: 8px;
                border-radius: 4px;
                font-size: {font_size}px;
            }}
            QPushButton:checked {{ background-color: {accent_color}; }}
            QPushButton:hover {{ border-color: {accent_color}; }}
        """)

    def _update_button_icon(self):
        """Update button icon and text based on config"""
        icon_data = self.config.get('icon_data', '')
        is_text = self.config.get('icon_is_text', False)
        icon_size = self.config.get('icon_size', 24)
        icon_position = self.config.get('icon_position', 'left')
        display_name = self.config.get('display_name', self.topic)
        show_text = self.config.get('show_text', True)

        # Clear existing icon
        self.button.setIcon(QIcon())

        # If show_text is False, only show icon
        if not show_text:
            self.button.setText("")
            if icon_data:
                if is_text:
                    # Text icon (emoji)
                    self.button.setText(icon_data)
                    text_color = self.config.get('text_color', '#D9D9D9')
                    self.button.setStyleSheet(f"""
                        QPushButton {{
                            background-color: #343a40;
                            color: {text_color};
                            border: 1px solid #6c757d;
                            padding: 8px;
                            border-radius: 4px;
                            font-size: {icon_size}px;
                        }}
                        QPushButton:checked {{ background-color: {self.config.get('accent_color', '#0d6efd')}; }}
                        QPushButton:hover {{ border-color: {self.config.get('accent_color', '#0d6efd')}; }}
                    """)
                else:
                    # Image icon
                    if Path(icon_data).exists():
                        pixmap = QPixmap(icon_data)
                        if not pixmap.isNull():
                            self.button.setIcon(QIcon(pixmap))
                            self.button.setIconSize(pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio).size())
            return

        # Normal flow with text visible
        if not icon_data:
            # No icon, just text
            self.button.setText(display_name)
            return

        if icon_position == 'only':
            # Icon only, no text
            self.button.setText("")
            if is_text:
                # For text icons, we need to use text with large font
                self.button.setText(icon_data)
                text_color = self.config.get('text_color', '#D9D9D9')
                self.button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: #343a40;
                        color: {text_color};
                        border: 1px solid #6c757d;
                        padding: 8px;
                        border-radius: 4px;
                        font-size: {icon_size}px;
                    }}
                    QPushButton:checked {{ background-color: {self.config.get('accent_color', '#0d6efd')}; }}
                    QPushButton:hover {{ border-color: {self.config.get('accent_color', '#0d6efd')}; }}
                """)
            else:
                # Image icon
                if Path(icon_data).exists():
                    pixmap = QPixmap(icon_data)
                    if not pixmap.isNull():
                        self.button.setIcon(QIcon(pixmap))
                        self.button.setIconSize(pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio).size())
        else:
            # Icon with text (left or right)
            if is_text:
                # For text icons with text, combine them
                if icon_position == 'left':
                    self.button.setText(f"{icon_data} {display_name}")
                else:  # right
                    self.button.setText(f"{display_name} {icon_data}")
            else:
                # Image icon with text
                self.button.setText(display_name)
                if Path(icon_data).exists():
                    pixmap = QPixmap(icon_data)
                    if not pixmap.isNull():
                        self.button.setIcon(QIcon(pixmap))
                        self.button.setIconSize(pixmap.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio).size())

    def get_value(self):
        return str(self.button.isChecked())