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
        # Create MQTT client with MQTT v5 protocol
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.connected = False
        self.broker = ""
        self.port = 1883
        self.username = ""
        self.password = ""
        self.ssl_enabled = False
        self.subscribed_topics = set()  # Initialize subscribed_topics set

    def on_connect(self, client, userdata, flags, reason_code, properties):
        rc_messages = {
            0: "Connection successful",
            1: "Incorrect protocol version",
            2: "Invalid client identifier",
            3: "Server unavailable",
            4: "Bad username or password",
            5: "Not authorized",
        }
        
        # Convert reason_code to int if it's not already
        if hasattr(reason_code, 'value'):
            reason_code = reason_code.value
            
        print(f"Connection result: {reason_code} - {rc_messages.get(reason_code, 'Unknown error')}")
        
        if reason_code == 0:
            self.connected = True
            status_msg = f"Connected to {self.broker}:{self.port}"
            if self.ssl_enabled:
                status_msg += " (SSL/TLS)"
            self.connection_status.emit(True, status_msg)
            
            # Resubscribe to any topics if needed
            for topic in self.subscribed_topics:
                print(f"Resubscribing to topic: {topic}")
                result, mid = self.client.subscribe(topic)
                if result != 0:
                    print(f"Failed to resubscribe to {topic}: {result}")
        else:
            self.connected = False
            error_msg = rc_messages.get(reason_code, f"Connection failed with code {reason_code}")
            self.connection_status.emit(False, f"Error: {error_msg}")
            print(f"MQTT Connection Error: {error_msg} (Code: {reason_code})")

    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties=None):
        self.connected = False
        # Convert reason_code to int if it's an enum
        if hasattr(reason_code, 'value'):
            reason_code = reason_code.value
            
        if reason_code != 0:
            error_msg = f"Unexpected disconnection: {reason_code}"
            if properties and hasattr(properties, 'reason_string'):
                error_msg += f" - {properties.reason_string}"
            self.connection_status.emit(False, error_msg)
            print(f"Disconnected with error: {error_msg}")
        else:
            self.connection_status.emit(False, "Disconnected")
            print("Disconnected normally")

    def on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            print(f"[DEBUG] Received message - Topic: {topic}, Payload: {payload}")
            self.message_received.emit(topic, payload)
        except Exception as e:
            print(f"[ERROR] Error in on_message: {str(e)}")
            print(f"[DEBUG] Message details - Topic: {msg.topic}, Payload: {msg.payload}")

    def connect(self, broker, port, username="", password="", use_ssl=False):
        try:
            print("\n" + "="*50)
            print(f"[DEBUG] Starting MQTT connection to {broker}:{port}")
            print(f"[DEBUG] SSL: {use_ssl}")
            print(f"[DEBUG] Username: {'Provided' if username else 'Not provided'}")
            
            self.broker = broker
            self.port = port
            self.username = username
            self.password = password
            self.ssl_enabled = use_ssl
            
            # Reset client to clear any previous state
            print("[DEBUG] Initializing new MQTT client...")
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # Enable debug logging
            self.client.enable_logger()
            
            # Set credentials if provided
            if username or password:
                print(f"[DEBUG] Setting username/password: {username}/{'*' * len(password) if password else 'None'}")
                self.client.username_pw_set(username or None, password or None)
            
            # Configure SSL if enabled
            if use_ssl:
                print("[DEBUG] Configuring SSL/TLS...")
                try:
                    self.client.tls_set(cert_reqs=ssl.CERT_NONE)  # For self-signed certificates
                    self.client.tls_insecure_set(True)  # Only for testing with self-signed certs
                    print("[DEBUG] SSL/TLS configured")
                except Exception as e:
                    error_msg = f"[ERROR] Failed to configure SSL: {str(e)}"
                    print(error_msg)
                    self.connection_status.emit(False, error_msg)
                    return
            
            # Set connection timeout
            self.client.connect_timeout = 10  # 10 seconds timeout
            
            # Connect to the broker
            print(f"[DEBUG] Initiating connection to {broker}:{port}...")
            try:
                print(f"[DEBUG] Using MQTT protocol version: {mqtt.CallbackAPIVersion.VERSION2}")
                self.client.connect_async(broker, int(port), 60)
                print("[DEBUG] Starting network loop...")
                self.client.loop_start()
                print("[DEBUG] Connection attempt initiated")
                
                # Keep the connection alive
                import time
                time.sleep(1)  # Give it a moment to connect
                
                if not hasattr(self, 'connected') or not self.connected:
                    print("[DEBUG] Connection not yet established, waiting...")
                    time.sleep(2)  # Wait a bit longer
                
                if hasattr(self, 'connected') and self.connected:
                    print("[DEBUG] Successfully connected to MQTT broker")
                else:
                    print("[WARNING] Connection may not have been established successfully")
                    
            except ValueError as ve:
                error_msg = f"[ERROR] Invalid port number: {port} - {str(ve)}"
                print(error_msg)
                self.connection_status.emit(False, error_msg)
                return
            except Exception as e:
                error_msg = f"[ERROR] Failed to start connection: {str(e)}"
                print(error_msg)
                self.connection_status.emit(False, error_msg)
                return
            
            # Initialize subscribed topics set if it doesn't exist
            if not hasattr(self, 'subscribed_topics'):
                self.subscribed_topics = set()
                
            print("Connect method completed")
            print("="*50 + "\n")
                
        except Exception as e:
            error_msg = f"Connection setup failed: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
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
        print(f"[DEBUG] Initial settings loaded: {self.settings}")
        self.init_ui()
        self.setup_connections()
        self.attempt_auto_connect()
        # Delay startup layout loading more to ensure everything is ready
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, self.load_startup_layout)
        
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
        
        # Layout selection button
        self.btn_select_layout = QPushButton("Select Startup Layout")
        self.btn_select_layout.clicked.connect(self.select_startup_layout)
        
        # Presentation mode button
        self.btn_presentation = QPushButton("Presentation Mode")
        self.btn_presentation.setCheckable(True)
        self.btn_presentation.clicked.connect(self.toggle_presentation_mode)
        
        # Add buttons to sidebar
        self.sidebar_layout.addWidget(self.btn_dashboard)
        self.sidebar_layout.addWidget(self.btn_settings)
        self.sidebar_layout.addWidget(self.btn_select_layout)
        self.sidebar_layout.addWidget(self.btn_presentation)
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
        
        # Initialize presentation mode state
        self.presentation_mode = False
        self.opacity_level = 1.0
        
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

    def load_startup_layout(self):
        """Load the startup layout if one is configured"""
        startup_layout = self.settings.get('startup_layout', '')
        print(f"[DEBUG] Checking startup layout: {startup_layout}")
        if startup_layout and Path(startup_layout).exists():
            print(f"[DEBUG] Startup layout file exists, scheduling load: {startup_layout}")
            from PyQt6.QtCore import QTimer
            # Delay loading to ensure MQTT connection is established
            QTimer.singleShot(1000, lambda: self._load_startup_layout_delayed(startup_layout))
        else:
            print(f"[DEBUG] No startup layout configured or file doesn't exist")
    
    def _load_startup_layout_delayed(self, file_path):
        """Load the startup layout with debug info"""
        print(f"[DEBUG] Loading startup layout: {file_path}")
        try:
            result = self.dashboard.load_layout(file_path)
            print(f"[DEBUG] Startup layout load result: {result}")
        except Exception as e:
            print(f"[DEBUG] Error loading startup layout: {e}")
    
    def select_startup_layout(self):
        """Allow user to select a layout file to load on startup"""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Startup Layout File",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Save the selected layout path to settings
            self.settings['startup_layout'] = file_path
            print(f"[DEBUG] Saving startup layout to settings: {file_path}")
            save_result = save_settings(self.settings)
            print(f"[DEBUG] Settings save result: {save_result}")
            
            # Reload settings to verify
            self.settings = load_settings()
            print(f"[DEBUG] Reloaded settings, startup_layout: {self.settings.get('startup_layout', 'NOT FOUND')}")
            
            # Ask if user wants to load it now
            reply = QMessageBox.question(
                self,
                'Load Layout Now?',
                f'Startup layout set to:\n{Path(file_path).name}\n\nWould you like to load it now?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.dashboard.load_layout(file_path)
                
            QMessageBox.information(
                self,
                'Startup Layout Set',
                f'The layout "{Path(file_path).name}" will now load automatically when the program starts.'
            )
    
    def toggle_presentation_mode(self):
        """Toggle presentation mode - hide/show frames and buttons"""
        self.presentation_mode = not self.presentation_mode
        
        if self.presentation_mode:
            # Hide sidebar and make window transparent
            self.sidebar.hide()
            self.setWindowOpacity(self.opacity_level)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            
            # Hide widget frames and buttons but keep them movable
            self.dashboard.set_presentation_mode(True)
            
            # Create small show button
            self.create_show_button()
            
        else:
            # Show sidebar and restore normal window
            self.sidebar.show()
            self.setWindowOpacity(1.0)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setWindowFlags(Qt.WindowType.Window)
            
            # Show widget frames and buttons
            self.dashboard.set_presentation_mode(False)
            
            # Remove show button
            if hasattr(self, 'show_button'):
                self.show_button.deleteLater()
                delattr(self, 'show_button')
        
        self.show()  # Refresh window
        
    def create_show_button(self):
        """Create small discrete button to exit presentation mode"""
        from PyQt6.QtWidgets import QPushButton
        from PyQt6.QtCore import Qt
        
        self.show_button = QPushButton("⚙", self)
        self.show_button.setFixedSize(30, 30)
        self.show_button.move(10, 10)
        self.show_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 100);
                color: white;
                border: 1px solid rgba(255, 255, 255, 100);
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 150);
            }
        """)
        self.show_button.clicked.connect(self.toggle_presentation_mode)
        self.show_button.show()
        self.show_button.raise_()
    
    def set_opacity(self, opacity):
        """Set window and widget opacity (0.0 to 1.0)"""
        self.opacity_level = max(0.1, min(1.0, opacity))
        if self.presentation_mode:
            self.setWindowOpacity(self.opacity_level)
            self.dashboard.set_widget_opacity(self.opacity_level)

    def closeEvent(self, event):
        # Save settings and clean up
        connection_settings = self.settings_panel.get_settings()
        # Merge connection settings with existing settings to preserve startup_layout
        self.settings.update(connection_settings)
        print(f"[DEBUG] Saving settings on close: {self.settings}")
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
