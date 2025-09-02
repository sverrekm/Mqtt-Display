from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                           QLineEdit, QPushButton, QLabel, QMessageBox, QSpinBox,
                           QCheckBox, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal

class ConnectionPanel(QWidget):
    connection_requested = pyqtSignal(dict)  # Emits connection settings
    
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
        
        # Add widgets to main layout
        layout.addWidget(connection_group)
        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)
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
