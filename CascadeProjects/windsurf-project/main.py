import sys
import json
import yaml
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
                           QWidget, QPushButton, QStackedWidget, QLabel, QMessageBox, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QSize
from PyQt6.QtGui import QIcon, QAction
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

        # CRITICAL: Set WA_TranslucentBackground FIRST before anything else!
        # This MUST be set before the window is shown for transparency to work on Windows
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set window icon
        from PyQt6.QtGui import QIcon
        import os
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.mqtt = MQTTClient()
        self.settings = load_settings()
        print(f"[DEBUG] Initial settings loaded: {self.settings}")
        self.init_ui()
        self.setup_connections()
        self.setup_system_tray()
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
        self.setMinimumSize(600, 400)

        # Restore window geometry from settings
        self.restore_window_geometry()
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QHBoxLayout(main_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(5, 5, 5, 5)
        self.sidebar_layout.setSpacing(5)
        
        # Dashboard button
        self.btn_dashboard = QPushButton("󰕮 Dashboard")
        self.btn_dashboard.setCheckable(True)
        self.btn_dashboard.setChecked(True)
        
        # Settings button
        self.btn_settings = QPushButton("󰒓 Settings")
        self.btn_settings.setCheckable(True)
        
        # Layout selection button
        self.btn_select_layout = QPushButton("📂 Select Startup Layout")
        self.btn_select_layout.clicked.connect(self.select_startup_layout)
        
        # Presentation mode button
        self.btn_presentation = QPushButton("▶️ Presentation Mode")
        self.btn_presentation.setCheckable(True)
        self.btn_presentation.clicked.connect(self.toggle_presentation_mode)
        
        # Add buttons to sidebar
        self.sidebar_layout.addWidget(self.btn_dashboard)
        self.sidebar_layout.addWidget(self.btn_settings)
        self.sidebar_layout.addStretch(1)
        self.sidebar_layout.addWidget(self.btn_select_layout)
        self.sidebar_layout.addWidget(self.btn_presentation)
        
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

        # Connect opacity and theme signals
        self.settings_panel.opacity_changed.connect(self.set_opacity)
        self.settings_panel.theme_changed.connect(self.apply_theme)

    def setup_system_tray(self):
        """Setup system tray icon with menu"""
        import os

        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Set icon (use same as window icon)
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            # Use default icon if custom icon not found
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))

        # Create tray menu
        tray_menu = QMenu()

        # Show/Hide window action
        show_action = QAction("Vis/Skjul Vindu", self)
        show_action.triggered.connect(self.toggle_window_visibility)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()

        # Presentation mode toggle
        self.presentation_mode_action = QAction("Aktiver Presentasjonsmodus", self)
        self.presentation_mode_action.triggered.connect(self.toggle_presentation_mode)
        tray_menu.addAction(self.presentation_mode_action)

        tray_menu.addSeparator()

        # Dashboard action
        dashboard_action = QAction("Gå til Dashboard", self)
        dashboard_action.triggered.connect(lambda: self.switch_page(0))
        tray_menu.addAction(dashboard_action)

        # Settings action
        settings_action = QAction("Gå til Innstillinger", self)
        settings_action.triggered.connect(lambda: self.switch_page(1))
        tray_menu.addAction(settings_action)

        tray_menu.addSeparator()

        # Quit action
        quit_action = QAction("Avslutt", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)

        # Set the menu to the tray icon
        self.tray_icon.setContextMenu(tray_menu)

        # Show tray icon
        self.tray_icon.show()

        # Connect tray icon activation (single/double click)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

        # Show notification that app is in tray
        self.tray_icon.showMessage(
            "MQTT Dashboard",
            "Programmet kjører i systemstatusfeltet",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def on_tray_icon_activated(self, reason):
        """Handle tray icon click"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Single click - toggle window visibility
            self.toggle_window_visibility()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click - show window and go to dashboard
            self.show()
            self.activateWindow()
            self.switch_page(0)

    def toggle_window_visibility(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def quit_application(self):
        """Quit application properly"""
        # Save and disconnect
        self.save_and_quit()

        # Close all windows
        QApplication.quit()

    def restore_window_geometry(self):
        """Restore window size and position from settings"""
        window_settings = self.settings.get('window', {})

        # Restore size
        width = window_settings.get('width', 800)
        height = window_settings.get('height', 600)
        self.resize(width, height)

        # Restore position if available
        x = window_settings.get('x')
        y = window_settings.get('y')
        if x is not None and y is not None:
            self.move(x, y)

    def save_window_geometry(self):
        """Save current window size and position to settings"""
        geometry = self.geometry()
        self.settings['window'] = {
            'width': geometry.width(),
            'height': geometry.height(),
            'x': geometry.x(),
            'y': geometry.y()
        }

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)
        self.btn_dashboard.setChecked(index == 0)
        self.btn_settings.setChecked(index == 1)
    
    def on_connection_status(self, connected, message):
        status = "Connected" if connected else "Disconnected"
        self.statusBar().showMessage(f"{status}: {message}")
        if connected:
            self.statusBar().setStyleSheet("background-color: #28a745; color: white;")
        else:
            self.statusBar().setStyleSheet("background-color: #dc3545; color: white;")
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2B2B2B;
            }
            QWidget#sidebar {
                background-color: #333333;
                border-right: 1px solid #4A4A4A;
            }
            QPushButton {
                background-color: #4A4A4A;
                color: #E0E0E0;
                border: 1px solid #4A4A4A;
                padding: 10px;
                margin: 2px;
                border-radius: 5px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #5A5A5A;
            }
            QPushButton:checked {
                background-color: #007ACC;
                color: white;
                border: 1px solid #005C99;
            }
            QStackedWidget {
                background-color: #2B2B2B;
            }
            QStatusBar {
                background-color: #333333;
                color: #E0E0E0;
            }
            QStatusBar::item {
                border: none;
            }
        """)

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
            # Save current window geometry before going fullscreen
            self.normal_geometry = self.geometry()

            # Save absolute screen positions of all widgets before going fullscreen
            self.save_widget_screen_positions()

            # Hide sidebar and statusbar
            self.sidebar.setFixedWidth(0)
            self.statusBar().setFixedHeight(0)
            self.setWindowOpacity(self.opacity_level)

            # Make window frameless and fullscreen to cover entire desktop
            # NOTE: WA_TranslucentBackground is already set in __init__, never remove it!
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

            # Apply transparent styling to main window
            self.apply_presentation_styling()

            # Hide widget frames and buttons
            self.dashboard.set_presentation_mode(True)

            # Update tray icon menu
            self.presentation_mode_action.setText("Avslutt Presentasjonsmodus")

            # Show window and make it fullscreen after a short delay
            self.show()
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self.go_fullscreen_presentation)

            # Show message about how to exit
            QMessageBox.information(
                self,
                'Presentasjonsmodus',
                'Presentasjonsmodus aktivert.\n\n'
                'For å gå ut av presentasjonsmodus:\n'
                '• Trykk ESC-tasten\n'
                '• Eller høyreklikk på dashboard og velg "Avslutt Presentasjonsmodus"\n'
                '• Eller bruk ikonet i systemstatusfeltet',
                QMessageBox.StandardButton.Ok
            )

        else:
            # Restore sidebar and statusbar to original size
            self.sidebar.setFixedWidth(200)
            self.statusBar().setMaximumHeight(16777215)  # Reset to no max height
            self.setWindowOpacity(1.0)
            # NOTE: NEVER remove WA_TranslucentBackground - keep it for future toggles!
            self.setWindowFlags(Qt.WindowType.Window)

            # Restore normal styling
            self.restore_normal_styling()

            # Show widget frames and buttons
            self.dashboard.set_presentation_mode(False)

            # Update tray icon menu
            self.presentation_mode_action.setText("Aktiver Presentasjonsmodus")

            # Show window and restore geometry
            self.show()
            if hasattr(self, 'normal_geometry'):
                from PyQt6.QtCore import QTimer
                # First restore window geometry
                QTimer.singleShot(50, lambda: self.setGeometry(self.normal_geometry))
                # Then restore widget positions
                QTimer.singleShot(150, self.restore_widget_positions)

    def save_widget_screen_positions(self):
        """Save absolute screen positions of all widgets"""
        self.widget_screen_positions = {}

        for widget in self.dashboard.widgets:
            if widget is None:
                continue

            # Get widget's position relative to container
            widget_pos = widget.pos()

            # Get scroll offset
            scroll_x = self.dashboard.scroll.horizontalScrollBar().value()
            scroll_y = self.dashboard.scroll.verticalScrollBar().value()

            # Calculate absolute position on screen
            # Container position in window + widget position in container - scroll offset + window position on screen
            container_pos = self.dashboard.container.mapTo(self, widget_pos)
            screen_pos = self.mapToGlobal(container_pos)

            # Store both screen position and original relative position
            self.widget_screen_positions[widget] = {
                'screen_x': screen_pos.x(),
                'screen_y': screen_pos.y(),
                'relative_x': widget_pos.x(),
                'relative_y': widget_pos.y()
            }

    def restore_widget_positions(self):
        """Restore widgets to their original relative positions"""
        if not hasattr(self, 'widget_screen_positions'):
            return

        for widget, positions in self.widget_screen_positions.items():
            if widget is not None and not widget.isHidden():
                # Restore original relative position within container
                widget.move(positions['relative_x'], positions['relative_y'])

    def go_fullscreen_presentation(self):
        """Make window fullscreen for presentation mode"""
        # Get the primary screen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()

        # Set window to cover entire screen
        self.setGeometry(screen_geometry)

        # Make sure the container fills the entire window
        self.dashboard.container.setMinimumSize(screen_geometry.width(), screen_geometry.height())

        # Now reposition widgets to maintain their absolute screen positions
        self.reposition_widgets_for_fullscreen()

    def reposition_widgets_for_fullscreen(self):
        """Reposition widgets to maintain their absolute screen positions when going fullscreen"""
        if not hasattr(self, 'widget_screen_positions'):
            return

        # Get the new window position (should be 0,0 for fullscreen)
        window_screen_pos = self.pos()

        # Get scroll area and container positions
        scroll_offset_x = self.dashboard.scroll.horizontalScrollBar().value()
        scroll_offset_y = self.dashboard.scroll.verticalScrollBar().value()

        for widget, positions in self.widget_screen_positions.items():
            if widget is None or widget.isHidden():
                continue

            # Calculate where the widget should be in the container to maintain screen position
            # screen_position = window_position + container_offset + widget_position - scroll_offset
            # So: widget_position = screen_position - window_position - container_offset + scroll_offset

            # Get container's position within the window
            container_in_window = self.dashboard.container.mapTo(self, widget.pos()).x()

            # Calculate new position to maintain same screen coordinates
            new_x = positions['screen_x'] - window_screen_pos.x() - self.sidebar.width()
            new_y = positions['screen_y'] - window_screen_pos.y() - self.statusBar().height()

            # Move widget to new position
            widget.move(int(new_x), int(new_y))

    def apply_presentation_styling(self):
        """Apply transparent styling to main window for presentation mode."""
        self.setStyleSheet("background-color: transparent;")
        central_widget = self.centralWidget()
        if central_widget:
            central_widget.setStyleSheet("background-color: transparent;")

    def restore_normal_styling(self):
        """Restore normal styling when exiting presentation mode"""
        self.apply_styles()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        from PyQt6.QtCore import Qt

        # ESC to exit presentation mode
        if event.key() == Qt.Key.Key_Escape and self.presentation_mode:
            self.toggle_presentation_mode()
        else:
            super().keyPressEvent(event)

    def set_opacity(self, opacity):
        """Set window and widget opacity (0.0 to 1.0)"""
        self.opacity_level = max(0.1, min(1.0, opacity))
        # Always update widget opacity (works both in normal and presentation mode)
        self.dashboard.set_widget_opacity(self.opacity_level)
        # Only update window opacity in presentation mode
        if self.presentation_mode:
            self.setWindowOpacity(self.opacity_level)

    def apply_theme(self, theme_key):
        """Apply theme to dashboard and all widgets"""
        from config.themes import apply_theme_to_dashboard, get_theme_config

        # Apply theme to dashboard background
        apply_theme_to_dashboard(self.dashboard, theme_key)

        # Apply theme to all widgets, respecting their individual settings
        for widget in self.dashboard.widgets:
            if widget is not None:
                # Only apply the global theme if the widget is not set to 'custom'
                if widget.config.get('theme_selector') != 'custom':
                    theme_config = get_theme_config(theme_key, widget.widget_type)
                    if theme_config:
                        # We update a copy to avoid modifying the base theme config
                        new_config = widget.config.copy()
                        new_config.update(theme_config)
                        widget.config = new_config

                # Always apply the config, which will be either the theme's 
                # or the widget's own custom one.
                widget.apply_config()

    def closeEvent(self, event):
        """Handle window close event - minimize to tray instead of closing"""
        if self.tray_icon.isVisible():
            # Save window geometry before hiding
            self.save_window_geometry()

            # Save settings (but don't disconnect MQTT)
            connection_settings = self.settings_panel.get_settings()
            self.settings.update(connection_settings)
            save_settings(self.settings)

            # Minimize to tray instead of closing
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "MQTT Dashboard",
                "Programmet kjører fortsatt i bakgrunnen.\nBruk systemstatusfeltet for å åpne eller avslutte.",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            # If tray icon is not visible, close normally
            self.save_and_quit()
            event.accept()

    def save_and_quit(self):
        """Save settings and quit application"""
        # Save window geometry
        self.save_window_geometry()

        # Save settings
        connection_settings = self.settings_panel.get_settings()
        # Merge connection settings with existing settings to preserve startup_layout
        self.settings.update(connection_settings)
        print(f"[DEBUG] Saving settings on close: {self.settings}")
        save_settings(self.settings)

        # Disconnect MQTT
        if self.mqtt.connected:
            print("Disconnecting normally")
            self.mqtt.disconnect()

        # Hide tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
