import sys
import json
import yaml
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                           QWidget, QPushButton, QStackedWidget, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QIcon
from widgets.connection_panel import ConnectionPanel
from widgets.dashboard import Dashboard
from config.settings import load_settings, save_settings

import paho.mqtt.client as mqtt
import ssl

class MQTTClient(QObject):
    message_received = pyqtSignal(str, str)  # topic, message
    connection_status = pyqtSignal(bool, str)  # connected, message

    def __init__(self):
        super().__init__()
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False
        self.broker = ""
        self.port = 1883
        self.username = ""
        self.password = ""
        self.ssl_enabled = False

    def on_connect(self, client, userdata, flags, rc, properties=None):
        rc_messages = {
            0: "Connection successful",
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized",
        }
        
        if rc == 0:
            self.connected = True
            status_msg = f"Connected to {self.broker}:{self.port}"
            if self.ssl_enabled:
                status_msg += " (SSL/TLS)"
            self.connection_status.emit(True, status_msg)
            
            # Resubscribe to any topics if needed
            if hasattr(self, 'subscribed_topics') and self.subscribed_topics:
                for topic in self.subscribed_topics:
                    self.client.subscribe(topic)
        else:
            self.connected = False
            error_msg = rc_messages.get(rc, f"Connection failed with code {rc}")
            self.connection_status.emit(False, f"Error: {error_msg}")
            print(f"MQTT Connection Error: {error_msg} (Code: {rc})")

    def on_disconnect(self, client, userdata, rc):
        self.connected = False
        if rc != 0:
            self.connection_status.emit(False, f"Unexpected disconnection: {rc}")
        else:
            self.connection_status.emit(False, "Disconnected")

    def on_message(self, client, userdata, msg):
        self.message_received.emit(msg.topic, msg.payload.decode())

    def connect(self, broker, port, username="", password="", use_ssl=False):
        try:
            print(f"Attempting to connect to {broker}:{port}...")
            print(f"SSL: {use_ssl}, Username: {'Provided' if username else 'Not provided'}")
            
            self.broker = broker
            self.port = port
            self.username = username
            self.password = password
            self.ssl_enabled = use_ssl
            
            # Reset client to clear any previous state
            self.client = mqtt.Client()
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # Set credentials if provided
            if username or password:
                print("Setting username/password")
                self.client.username_pw_set(username or None, password or None)
            
            # Configure SSL if enabled
            if use_ssl:
                print("Configuring SSL/TLS")
                self.client.tls_set(cert_reqs=ssl.CERT_NONE)  # For self-signed certificates
                self.client.tls_insecure_set(True)  # Only for testing with self-signed certs
            
            # Set connection timeout
            self.client.connect_timeout = 10  # 10 seconds timeout
            
            # Connect to the broker
            print("Initiating connection...")
            try:
                self.client.connect_async(broker, int(port), 60)
                self.client.loop_start()
                print("Connection attempt started")
            except ValueError as ve:
                error_msg = f"Invalid port number: {port}"
                print(error_msg)
                self.connection_status.emit(False, error_msg)
                return
            except Exception as e:
                error_msg = f"Failed to start connection: {str(e)}"
                print(error_msg)
                self.connection_status.emit(False, error_msg)
                return
            
            # Initialize subscribed topics set if it doesn't exist
            if not hasattr(self, 'subscribed_topics'):
                self.subscribed_topics = set()
                
        except Exception as e:
            error_msg = f"Connection setup failed: {str(e)}"
            print(error_msg)
            self.connection_status.emit(False, error_msg)

    def disconnect(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            self.connection_status.emit(False, "Disconnected")
        except Exception as e:
            self.connection_status.emit(False, f"Error disconnecting: {str(e)}")

    def publish(self, topic, message, qos=0, retain=False):
        if not self.connected:
            return False
        try:
            result = self.client.publish(topic, message, qos=qos, retain=retain)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"Publish error: {e}")
            return False

    def subscribe(self, topic, qos=0):
        if not self.connected:
            return False
        try:
            result, mid = self.client.subscribe(topic, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                if not hasattr(self, 'subscribed_topics'):
                    self.subscribed_topics = set()
                self.subscribed_topics.add(topic)
                return True
            return False
        except Exception as e:
            print(f"Subscribe error: {e}")
            return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mqtt = MQTTClient()
        self.settings = load_settings()
        self.init_ui()
        self.setup_connections()
        self.attempt_auto_connect()
        
    def attempt_auto_connect(self):
        """Attempt to connect automatically if settings allow"""
        if self.settings.get('auto_connect', False):
            # Small delay to ensure UI is fully loaded
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(500, self._perform_auto_connect)
            
    def _perform_auto_connect(self):
        """Perform the actual auto-connection"""
        try:
            settings = {
                'broker': self.settings.get('broker', ''),
                'port': int(self.settings.get('port', 1883)),
                'username': self.settings.get('username', ''),
                'password': self.settings.get('password', ''),
                'use_ssl': self.settings.get('use_ssl', False)
            }
            if settings['broker']:  # Only try to connect if we have a broker address
                self.mqtt.connect(**settings)
        except Exception as e:
            print(f"Auto-connect failed: {e}")

    def init_ui(self):
        self.setWindowTitle("MQTT Dashboard")
        self.setMinimumSize(1024, 768)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout(main_widget)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        
        # Dashboard button
        self.btn_dashboard = QPushButton("Dashboard")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        
        # Settings button
        self.btn_settings = QPushButton("Settings")
        self.btn_settings.setCheckable(True)
        
        # Add buttons to sidebar
        self.sidebar_layout.addWidget(self.btn_dashboard)
        self.sidebar_layout.addWidget(self.btn_settings)
        self.sidebar_layout.addStretch()
        
        # Main content area
        self.stacked_widget = QStackedWidget()
        
        # Create pages
        self.dashboard = Dashboard(self.mqtt)
        self.settings_panel = ConnectionPanel(self.mqtt, self.settings)
        
        # Add pages to stacked widget
        self.stacked_widget.addWidget(self.dashboard)
        self.stacked_widget.addWidget(self.settings_panel)
        
        # Add widgets to main layout
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.stacked_widget, 1)
        
        # Apply styles
        self.apply_styles()

    def setup_connections(self):
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0))
        self.btn_settings.clicked.connect(lambda: self.switch_page(1))
        self.mqtt.connection_status.connect(self.on_connection_status)
        
        # Connect the connection panel's signal to the MQTT client's connect method
        self.settings_panel.connection_requested.connect(
            lambda settings: self.mqtt.connect(
                broker=settings['broker'],
                port=settings['port'],
                username=settings['username'],
                password=settings['password'],
                use_ssl=settings['use_ssl']
            )
        )
        
    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_dashboard.setChecked(index == 0)
        self.btn_settings.setChecked(index == 1)
    
    def on_connection_status(self, connected, message):
        status = "Connected" if connected else "Disconnected"
        self.statusBar().showMessage(f"{status}: {message}")
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                padding: 8px;
                margin: 2px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #f6f7fa, stop:1 #dadbde);
            }
            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #6a9eda, stop:1 #4a7bc8);
                color: white;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #e7e7e7, stop:1 #d7d7d7);
            }
            QPushButton:checked:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                          stop:0 #5d8fd4, stop:1 #3a6cb7);
            }
            #sidebar {
                background-color: #e0e0e0;
                border-right: 1px solid #ccc;
            }
        """)
        self.sidebar.setObjectName("sidebar")

    def closeEvent(self, event):
        # Save settings and clean up
        self.settings = self.settings_panel.get_settings()
        save_settings(self.settings)
        self.mqtt.disconnect()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
