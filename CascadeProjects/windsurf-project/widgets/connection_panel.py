from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLineEdit, QPushButton, QLabel, QMessageBox, QSpinBox,
                           QCheckBox, QGroupBox, QSlider, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal

class ConnectionPanel(QWidget):
    connection_requested = pyqtSignal(dict)  # Emits connection settings
    opacity_changed = pyqtSignal(float)  # Emits opacity value (0.0 - 1.0)
    theme_changed = pyqtSignal(str)  # Emits theme name

    def __init__(self, mqtt_client, settings=None, parent=None):
        super().__init__(parent)
        self.mqtt = mqtt_client
        self.settings = settings or {}
        self.init_ui()
        self.load_settings()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Connection Settings Group
        connection_group = QGroupBox("MQTT Connection Settings")
        form_layout = QFormLayout()
        
        # Broker Address
        self.broker_edit = QLineEdit()
        self.broker_edit.setPlaceholderText("mqtt.example.com")
        form_layout.addRow("Broker:", self.broker_edit)
        
        # Port
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        self.port_edit.setValue(1883)
        form_layout.addRow("Port:", self.port_edit)
        
        # Username
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Optional")
        form_layout.addRow("Username:", self.username_edit)
        
        # Password
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Optional")
        form_layout.addRow("Password:", self.password_edit)
        
        # SSL/TLS
        self.ssl_check = QCheckBox("Use SSL/TLS")
        form_layout.addRow("", self.ssl_check)
        
        # Auto Connect
        self.auto_connect = QCheckBox("Connect on startup")
        form_layout.addRow("", self.auto_connect)
        
        connection_group.setLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(self.disconnect_btn)
        
        # Status
        self.status_label = QLabel("Status: Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")

        # Theme Selection Group
        theme_group = QGroupBox("Tema og Utseende")
        theme_layout = QFormLayout()

        # Theme selector
        self.theme_combo = QComboBox()
        self.load_themes()
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        theme_layout.addRow("Tema:", self.theme_combo)

        # Custom theme button
        custom_theme_btn = QPushButton("Lag Nytt Tema...")
        custom_theme_btn.clicked.connect(self.create_custom_theme)
        theme_layout.addRow("", custom_theme_btn)

        theme_group.setLayout(theme_layout)

        # Presentation Mode Group
        presentation_group = QGroupBox("Presentasjonsmodus")
        presentation_layout = QFormLayout()

        # Opacity slider
        opacity_layout = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setMinimum(10)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        self.opacity_label = QLabel("100%")
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        presentation_layout.addRow("Gjennomsiktighet:", opacity_layout)

        presentation_group.setLayout(presentation_layout)

        # Add widgets to main layout
        layout.addWidget(connection_group)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(theme_group)
        layout.addWidget(presentation_group)
        layout.addStretch()

        # Connect MQTT signals
        self.mqtt.connection_status.connect(self.update_connection_status)
        
    def load_settings(self):
        """Load settings from the provided dictionary"""
        if not self.settings:
            return
            
        self.broker_edit.setText(self.settings.get('broker', ''))
        self.port_edit.setValue(int(self.settings.get('port', 1883)))
        self.username_edit.setText(self.settings.get('username', ''))
        self.password_edit.setText(self.settings.get('password', ''))
        self.ssl_check.setChecked(self.settings.get('use_ssl', False))
        self.auto_connect.setChecked(self.settings.get('auto_connect', False))
        
        if self.auto_connect.isChecked():
            self.on_connect_clicked()
    
    def get_settings(self):
        """Return the current settings as a dictionary"""
        return {
            'broker': self.broker_edit.text(),
            'port': self.port_edit.value(),
            'username': self.username_edit.text(),
            'password': self.password_edit.text(),
            'use_ssl': self.ssl_check.isChecked(),
            'auto_connect': self.auto_connect.isChecked()
        }
        
    def on_connect_clicked(self):
        """Handle connect button click"""
        broker = self.broker_edit.text().strip()
        if not broker:
            QMessageBox.warning(self, "Error", "Please enter a broker address")
            return
            
        port = self.port_edit.value()
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        use_ssl = self.ssl_check.isChecked()
        
        # Update settings
        self.settings.update({
            'broker': broker,
            'port': port,
            'username': username,
            'password': password,
            'use_ssl': use_ssl,
            'auto_connect': self.auto_connect.isChecked()
        })
        
        # Emit connection request
        self.connection_requested.emit({
            'broker': broker,
            'port': port,
            'username': username if username else None,
            'password': password if password else None,
            'use_ssl': use_ssl
        })
        
        # Update UI
        self.connect_btn.setEnabled(False)
        self.disconnect_btn.setEnabled(True)
    
    def on_disconnect_clicked(self):
        """Handle disconnect button click"""
        self.mqtt.disconnect()
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.status_label.setText("Status: Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def update_connection_status(self, connected, message):
        """Update UI based on connection status"""
        if connected:
            self.status_label.setText(f"Status: Connected to {self.broker_edit.text()}")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
        else:
            self.status_label.setText(f"Status: Disconnected - {message}")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(False)

    def load_themes(self):
        """Load available themes into the combo box"""
        from config.themes import get_theme_list, load_custom_themes

        # Load custom themes first
        load_custom_themes()

        # Get all themes
        themes = get_theme_list()

        # Add themes to combo box
        self.theme_combo.clear()
        for theme_key, theme_name, _ in themes:
            self.theme_combo.addItem(theme_name, theme_key)

    def on_theme_changed(self, theme_display_name):
        """Handle theme change"""
        # Get the theme key from the combo box
        index = self.theme_combo.currentIndex()
        if index >= 0:
            theme_key = self.theme_combo.itemData(index)
            if theme_key:
                self.theme_changed.emit(theme_key)

    def create_custom_theme(self):
        """Open dialog to create a custom theme"""
        from widgets.custom_theme_dialog import CustomThemeDialog

        dialog = CustomThemeDialog(self)
        if dialog.exec():
            # Reload themes to include the new custom theme
            self.load_themes()

    def on_opacity_changed(self, value):
        """Handle opacity slider change"""
        # Convert 0-100 to 0.0-1.0
        opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.opacity_changed.emit(opacity)
