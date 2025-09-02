from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
                           QPushButton, QScrollArea, QFrame, QSizePolicy,
                           QComboBox, QLineEdit, QMessageBox, QInputDialog,
                           QMenu, QMenuBar, QFileDialog, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QMimeData
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QAction, QFont, QPen, QBrush, QConicalGradient
import json
import os
import math

# Import widget classes
from .base_widget import BaseWidget
from .label_widget import LabelWidget
from .button_widget import ButtonWidget
from .slider_widget import SliderWidget
from .gauge_widget import GaugeWidget

class Dashboard(QWidget):
    def __init__(self, mqtt_client, parent=None):
        super().__init__(parent)
        self.mqtt = mqtt_client
        self.widgets = []
        self.subscribed_topics = set()
        self.current_layout_file = None
        
        # Set up the main widget and layout
        self.setAcceptDrops(True)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(240, 240, 240))
        self.setPalette(palette)
        
        # Create a scroll area for the dashboard
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        # Container widget that will hold the grid layout
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Set the container as the widget in the scroll area
        self.scroll.setWidget(self.container)
        
        # Add the scroll area to the main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll)
        
        # Auto-load layout if specified in settings
        if hasattr(parent, 'settings') and 'layout_file' in parent.settings:
            self.load_layout(parent.settings['layout_file'])
            
        # Set up context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def init_ui(self):
        """Initialize the widget's UI elements"""
        # Set default style
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
            QFrame:hover {
                border: 1px solid #6c757d;
            }
        """)
        
    def show_add_widget_dialog(self):
        """Show dialog to add a new widget"""
        dialog = AddWidgetDialog(self)
        if dialog.exec():
            widget_type = dialog.get_selected_widget()
            topic = dialog.get_topic()
            if widget_type and topic:
                self.add_widget(widget_type, topic)
    
    def add_widget(self, widget_type, topic, row=None, col=None, **kwargs):
        """Add a widget to the dashboard
        
        Args:
            widget_type: Type of widget to add ('label', 'button', 'slider', 'gauge')
            topic: MQTT topic to subscribe to
            row: Grid row position (optional, will find next available if not specified)
            col: Grid column position (optional, will find next available if not specified)
            **kwargs: Additional arguments for the widget constructor
            
        Returns:
            The created widget or None if creation failed
        """
        print(f"[DEBUG] Adding widget: type={widget_type}, topic={topic}, row={row}, col={col}, kwargs={kwargs}")
        try:
            # Create the appropriate widget
            print(f"[DEBUG] Creating widget of type: {widget_type}")
            try:
                if widget_type == 'label':
                    print("[DEBUG] Creating LabelWidget")
                    widget = LabelWidget(topic, **kwargs)
                elif widget_type == 'button':
                    print("[DEBUG] Creating ButtonWidget")
                    widget = ButtonWidget(topic, **kwargs)
                elif widget_type == 'slider':
                    print("[DEBUG] Creating SliderWidget")
                    widget = SliderWidget(topic, **kwargs)
                elif widget_type == 'gauge':
                    print("[DEBUG] Creating GaugeWidget")
                    widget = GaugeWidget(topic, **kwargs)
                else:
                    error_msg = f"Unknown widget type: {widget_type}"
                    print(f"[ERROR] {error_msg}")
                    raise ValueError(error_msg)
                
                # Set parent after creation to avoid issues with Qt's parent-child relationship
                if widget is not None:
                    widget.setParent(self)
                    
            except Exception as e:
                print(f"[ERROR] Failed to create widget: {e}")
                raise
                
            if widget is None:
                raise ValueError("Failed to create widget")
                
            print(f"[DEBUG] Widget created: {widget}")
            
            # Set size policy to make widgets expand to fill their grid cell
            try:
                widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            except Exception as e:
                print(f"[ERROR] Failed to set size policy: {e}")
                raise
            
            # Add to layout
            if row is not None and col is not None:
                # Add at specified position
                self.grid_layout.addWidget(widget, row, col, 1, 1)
            else:
                # Find the next available cell
                position = self.find_empty_cell()
                self.grid_layout.addWidget(widget, *position, 1, 1)
            
            # Add to widgets list
            self.widgets.append(widget)
            
            # Subscribe to the topic if we have an MQTT client
            if self.mqtt and topic not in self.subscribed_topics:
                try:
                    self.mqtt.subscribe(topic)
                    self.subscribed_topics.add(topic)
                except Exception as e:
                    print(f"Failed to subscribe to {topic}: {str(e)}")
            
            # Ensure the widget is visible
            widget.show()
            return widget
            
        except Exception as e:
            error_msg = f"Failed to add {widget_type} widget: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return None
    
    def find_empty_cell(self):
        """Find the next empty cell in the grid
        
        Returns:
            tuple: (row, col) of the first empty cell found
        """
        max_cols = 3  # Default number of columns
        
        # First try to find an empty cell in existing rows
        for row in range(self.grid_layout.rowCount()):
            for col in range(max_cols):
                if self.grid_layout.itemAtPosition(row, col) is None:
                    return (row, col)
        
        # If no empty cells found, add a new row
        return (self.grid_layout.rowCount(), 0)
    
    def save_layout(self, file_path=None):
        """Save the current dashboard layout to a file with widget positions and sizes
        
        Args:
            file_path: Path to save the layout to. If None, a file dialog will be shown.
            
        Returns:
            bool: True if the layout was saved successfully, False otherwise
        """
        try:
            if file_path is None:
                # Get the file path with a default .json extension if not provided
                file_path, _ = QFileDialog.getSaveFileName(
                    self, 
                    "Save Layout", 
                    "", 
                    "JSON Files (*.json);;All Files (*)",
                    options=QFileDialog.Option.DontUseNativeDialog
                )
                
                if not file_path:
                    return False  # User cancelled
                
                # Ensure the file has a .json extension
                if not file_path.lower().endswith('.json'):
                    file_path += '.json'
            
            # Create a dictionary to store the layout
            layout_data = {
                'version': 2,  # Version 2: Grid layout
                'widgets': []
            }
            
            # Save each widget's data
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget and hasattr(widget, 'widget_type') and hasattr(widget, 'topic'):
                    # Get the widget's position in the grid
                    index = self.grid_layout.indexOf(widget)
                    row, col, row_span, col_span = self.grid_layout.getItemPosition(index)
                    
                    # Get widget-specific data
                    widget_data = {
                        'type': widget.widget_type,
                        'topic': widget.topic,
                        'position': {
                            'row': row,
                            'col': col,
                            'row_span': row_span,
                            'col_span': col_span
                        },
                        'value': widget.get_value()
                    }
                    
                    # Add widget-specific properties
                    if hasattr(widget, 'min_val') and hasattr(widget, 'max_val'):
                        widget_data['min'] = widget.min_val
                        widget_data['max'] = widget.max_val
                    
                    # Add button state if applicable
                    if hasattr(widget, 'state'):
                        widget_data['state'] = widget.state
                    
                    layout_data['widgets'].append(widget_data)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(layout_data, f, indent=4)
                
            # Update the current layout file
            self.current_layout_file = file_path
            
            # If we have a parent with settings, update the last layout file
            if hasattr(self.parent(), 'settings'):
                if not hasattr(self.parent(), 'settings'):
                    self.parent().settings = {}
                self.parent().settings['layout_file'] = file_path
                
            return True
            
        except Exception as e:
            error_msg = f"Failed to save layout: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return False
    
    def load_layout(self, file_path=None):
        """Load a dashboard layout from a file
        
        Args:
            file_path: Path to the layout file. If None, a file dialog will be shown.
            
        Returns:
            bool: True if the layout was loaded successfully, False otherwise
        """
        try:
            if file_path is None:
                file_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Load Layout",
                    "",
                    "JSON Files (*.json);;All Files (*)",
                    options=QFileDialog.Option.DontUseNativeDialog
                )
                
                if not file_path or not os.path.exists(file_path):
                    return False  # User cancelled or file doesn't exist
            
            # Clear existing widgets
            self.clear_widgets()
            
            # Load the layout data
            with open(file_path, 'r') as f:
                layout_data = json.load(f)
            
            # Check version
            version = layout_data.get('version', 1)
            
            # Create widgets from the layout data
            for widget_data in layout_data.get('widgets', []):
                widget_type = widget_data.get('type')
                topic = widget_data.get('topic')
                position = widget_data.get('position', {})
                
                if not widget_type or not topic:
                    print(f"Skipping widget with missing type or topic: {widget_data}")
                    continue
                
                # Create widget with appropriate parameters
                kwargs = {}
                if 'min' in widget_data and 'max' in widget_data:
                    kwargs['min_val'] = widget_data['min']
                    kwargs['max_val'] = widget_data['max']
                
                # For button widgets, restore the state if available
                if widget_type == 'button' and 'state' in widget_data:
                    kwargs['initial_state'] = bool(widget_data['state'])
                
                # For label widgets, set the initial value
                if widget_type == 'label' and 'value' in widget_data:
                    kwargs['initial_value'] = str(widget_data['value'])
                
                # For slider and gauge widgets, set the initial value if available
                if widget_type in ['slider', 'gauge'] and 'value' in widget_data:
                    try:
                        kwargs['initial_val'] = float(widget_data['value'])
                    except (ValueError, TypeError):
                        pass
                
                # Add the widget to the dashboard
                widget = self.add_widget(
                    widget_type,
                    topic,
                    row=position.get('row'),
                    col=position.get('col'),
                    **kwargs
                )
                
                # Restore additional widget state if needed
                if widget:
                    # For button widgets, restore the checked state
                    if widget_type == 'button' and 'state' in widget_data:
                        try:
                            widget.button.setChecked(bool(widget_data['state']))
                            widget.state = bool(widget_data['state'])
                        except Exception as e:
                            print(f"Failed to restore button state: {str(e)}")
                    
                    # For slider and gauge widgets, ensure the value is set
                    if widget_type in ['slider', 'gauge'] and 'value' in widget_data:
                        try:
                            if hasattr(widget, 'set_value'):
                                widget.set_value(widget_data['value'])
                        except Exception as e:
                            print(f"Failed to set value for {widget_type} widget: {str(e)}")
            
            # Update the current layout file
            self.current_layout_file = file_path
            
            # If we have a parent with settings, update the last layout file
            if hasattr(self.parent(), 'settings'):
                if not hasattr(self.parent(), 'settings'):
                    self.parent().settings = {}
                self.parent().settings['layout_file'] = file_path
            
            return True
            
        except Exception as e:
            error_msg = f"Failed to load layout: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "Error", error_msg)
            return False
    
    def clear_widgets(self):
        """Remove all widgets from the dashboard"""
        # Make a copy of the widgets list to avoid modification during iteration
        for widget in self.widgets[:]:
            try:
                if widget is not None:
                    widget.setParent(None)
                    widget.hide()
                    widget.deleteLater()
            except RuntimeError:
                # Widget already deleted
                pass
        
        # Clear the widgets list and subscriptions
        self.widgets.clear()
        self.subscribed_topics.clear()
    
    def show_context_menu(self, position):
        """Show context menu for the dashboard
        
        Args:
            position: The position where the context menu was triggered
        """
        menu = QMenu(self)
        
        # Add menu items
        add_action = menu.addAction("Add Widget")
        save_action = menu.addAction("Save Layout")
        load_action = menu.addAction("Load Layout")
        clear_action = menu.addAction("Clear All Widgets")
        
        # Show menu and get selected action
        action = menu.exec(self.mapToGlobal(position))
        
        # Handle the selected action
        if action == add_action:
            self.show_add_widget_dialog()
        elif action == save_action:
            self.save_layout()
        elif action == load_action:
            # Ask for confirmation if there are existing widgets
            if self.widgets:
                reply = QMessageBox.question(
                    self,
                    'Confirm Clear',
                    'Loading a layout will remove all current widgets. Continue?',
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.load_layout()
            else:
                self.load_layout()
        elif action == clear_action:
            # Ask for confirmation before clearing
            reply = QMessageBox.question(
                self,
                'Confirm Clear',
                'Are you sure you want to remove all widgets?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.clear_widgets()
    
    def dragEnterEvent(self, event):
        """Handle drag enter event for widget drag and drop"""
        if event.mimeData().hasFormat('application/x-widget'):
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event for widget drag and drop"""
        if event.mimeData().hasFormat('application/x-widget'):
            # Get the widget type from the mime data
            widget_type = event.mimeData().data('application/x-widget').data().decode()
            
            # Get the drop position in grid coordinates
            pos = event.position().toPoint()
            widget_under_cursor = self.childAt(pos)
            
            # Find the drop position in the grid
            if widget_under_cursor:
                # Get the widget that was clicked on (might be a child of the actual widget)
                while widget_under_cursor.parent() and widget_under_cursor.parent() != self.container:
                    widget_under_cursor = widget_under_cursor.parent()
                
                # Get the widget's position in the grid
                index = self.grid_layout.indexOf(widget_under_cursor)
                if index >= 0:
                    row, col, _, _ = self.grid_layout.getItemPosition(index)
                else:
                    # If we couldn't find the widget in the layout, use the mouse position
                    row = pos.y() // 100  # Approximate row height
                    col = pos.x() // 150   # Approximate column width
            else:
                # If no widget was under the cursor, use the mouse position
                row = pos.y() // 100  # Approximate row height
                col = pos.x() // 150   # Approximate column width
            
            # Limit the position to reasonable values
            row = max(0, min(row, 100))  # Limit to 100 rows
            col = max(0, min(col, 10))   # Limit to 10 columns
            
            # Show dialog to get MQTT topic
            topic, ok = QInputDialog.getText(
                self, 
                f"Add {widget_type.capitalize()} Widget", 
                f"Enter MQTT topic for {widget_type}:"
            )
            
            if ok and topic.strip():
                # Add the widget at the calculated position
                self.add_widget(widget_type, topic.strip(), row=row, col=col)
                event.acceptProposedAction()

class AddWidgetDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Widget")
        self.setModal(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Widget type selection
        self.widget_type = QComboBox()
        self.widget_type.addItems(["label", "button", "slider", "gauge"])
        
        # Topic input
        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("Enter MQTT topic")
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        
        # Add widgets to layout
        layout.addWidget(QLabel("Widget Type:"))
        layout.addWidget(self.widget_type)
        layout.addWidget(QLabel("MQTT Topic:"))
        layout.addWidget(self.topic_edit)
        layout.addWidget(button_box)
    
    def get_selected_widget(self):
        return self.widget_type.currentText()
    
    def get_topic(self):
        return self.topic_edit.text().strip()

class BaseWidget(QFrame):
    """Base class for all dashboard widgets"""
    def __init__(self, widget_type, topic, mqtt_client, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.topic = topic
        self.mqtt = mqtt_client
        
        # Set up the widget
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        self.setMinimumSize(100, 80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Main layout with margins
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(2)
        
        # Add title bar
        self.title_bar = QLabel(f"{widget_type}: {topic}")
        self.title_bar.setStyleSheet("""
            background-color: #e0e0e0; 
            padding: 2px 5px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 10px;
        """)
        self.title_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_bar)
        
        # Content area
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.content_layout.setSpacing(2)
        self.layout.addWidget(self.content, 1)  # Add stretch factor to push content to top
        
        # Initialize the widget
        self.init_ui()
        
        # Set up event filter for hover effects
        self.setMouseTracking(True)
        self.enterEvent = self.on_enter
        self.leaveEvent = self.on_leave
        
    def on_enter(self, event):
        # Add hover effect
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #6c757d;
                border-radius: 4px;
            }
        """)
        
    def on_leave(self, event):
        # Remove hover effect
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        
    def mousePressEvent(self, event):
        # Check if the resize handle was clicked
        if self.resize_handle.underMouse():
            self.resizing = True
            self.original_geometry = self.geometry()
            self.mouse_press_pos = event.globalPosition().toPoint()
            event.accept()
        else:
            event.ignore()
            
    def mouseMoveEvent(self, event):
        if self.resizing and self.original_geometry:
            # Calculate new size
            delta = event.globalPosition().toPoint() - self.mouse_press_pos
            new_width = max(50, self.original_geometry.width() + delta.x())
            new_height = max(50, self.original_geometry.height() + delta.y())
            self.resize(new_width, new_height)
            event.accept()
        else:
            event.ignore()
            
    def mouseReleaseEvent(self, event):
        self.resizing = False
        self.original_geometry = None
        event.accept()
        
    def on_title_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.mouse_press_pos = event.globalPosition().toPoint()
            self.original_geometry = self.geometry()
            event.accept()
            
    def on_title_move(self, event):
        if self.dragging and self.original_geometry:
            # Move the widget
            delta = event.globalPosition().toPoint() - self.mouse_press_pos
            self.move(self.original_geometry.topLeft() + delta)
            event.accept()
            
    def on_title_release(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.original_geometry = None
            event.accept()
    
    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.setMinimumSize(200, 100)
        
        # Title bar
        self.title_bar = QWidget()
        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel(self.topic)
        self.title_label.setStyleSheet("font-weight: bold;")
        
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(20, 20)
        self.close_btn.clicked.connect(self.deleteLater)
        
        self.title_layout.addWidget(self.title_label)
        self.title_layout.addStretch()
        self.title_layout.addWidget(self.close_btn)
        
        self.layout.addWidget(self.title_bar)
        
        # Make widget draggable
        self.dragging = False
        self.offset = QPoint()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.offset = event.pos()
    
    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(self.mapToParent(event.pos() - self.offset))
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
    
    def get_value(self):
        """Return the current value of the widget"""
        raise NotImplementedError("Subclasses must implement get_value()")

class LabelWidget(BaseWidget):
    def __init__(self, topic, initial_value="", mqtt_client=None, parent=None):
        super().__init__("label", topic, mqtt_client, parent)
        self.value_label = QLabel(initial_value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.value_label, 1)  # Add stretch to center vertically
        
        # Set font size based on widget size
        font = self.value_label.font()
        font.setPointSize(12)
        self.value_label.setFont(font)
        
        # Set style
        self.value_label.setStyleSheet("""
            QLabel {
                color: #212529;
                font-weight: 500;
            }
        """)
        
        if mqtt_client:
            mqtt_client.message_received.connect(self.on_message_received)
            
    def on_message_received(self, topic, message):
        if topic == self.topic:
            self.value_label.setText(message)
            
    def get_value(self):
        return self.value_label.text()

class ButtonWidget(BaseWidget):
    def __init__(self, topic, label="Toggle", mqtt_client=None, parent=None):
        super().__init__("button", topic, mqtt_client, parent)
        self.state = False
        
        # Create button with styling
        self.button = QPushButton(label)
        self.button.setCheckable(True)
        self.button.setStyleSheet("""
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 5px 10px;
                min-height: 30px;
                font-weight: 500;
            }
            QPushButton:checked {
                background-color: #0d6efd;
                color: white;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:checked:hover {
                background-color: #0b5ed7;
            }
        """)
        
        # Connect signals
        self.button.clicked.connect(self.on_click)
        
        # Add button to layout with stretch to center it
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addStretch(1)
        
    def on_click(self):
        self.state = self.button.isChecked()
        if self.mqtt:
            self.mqtt.publish(self.topic, str(int(self.state)))
            
    def get_value(self):
        return str(int(self.state))

class SliderWidget(BaseWidget):
    def __init__(self, topic, min_val=0, max_val=100, initial_val=0, mqtt_client=None, parent=None):
        super().__init__("slider", topic, mqtt_client, parent)
        from PyQt6.QtWidgets import QSlider
        
        # Create slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_val)
        self.slider.setMaximum(max_val)
        self.slider.setValue(initial_val)
        
        # Create value display
        self.value_label = QLabel(str(initial_val))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Style the slider and label
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ced4da;
                height: 8px;
                background: #e9ecef;
                margin: 0px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0d6efd;
                border: 1px solid #0a58ca;
                width: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #0b5ed7;
            }
        """)
        
        self.value_label.setStyleSheet("""
            QLabel {
                font-weight: 500;
                color: #212529;
                font-size: 12px;
            }
        """)
        
        # Connect signals
        self.slider.valueChanged.connect(self.on_value_changed)
        
        # Add to layout with proper spacing
        self.content_layout.addStretch(1)
        self.content_layout.addWidget(self.value_label, 0, Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.slider)
        self.content_layout.addStretch(1)
        
    def on_value_changed(self, value):
        self.value_label.setText(str(value))
        if self.mqtt:
            self.mqtt.publish(self.topic, str(value))
            
    def get_value(self):
        return str(self.slider.value())
        
    def set_value(self, value):
        try:
            self.slider.setValue(int(value))
        except (ValueError, TypeError):
            pass

class GaugeWidget(BaseWidget):
    def __init__(self, topic, min_val=0, max_val=100, initial_val=0, mqtt_client=None, parent=None):
        super().__init__("gauge", topic, mqtt_client, parent)
        self.min_val = float(min_val)
        self.max_val = float(max_val)
        self.value = float(initial_val)
        
        # Set minimum size
        self.setMinimumSize(120, 80)
        
        # Connect to MQTT if available
        if mqtt_client:
            mqtt_client.message_received.connect(self.on_message_received)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        width = self.width()
        height = self.height()
        margin = 5
        
        # Draw background
        painter.setBrush(QColor(248, 249, 250))  # Light gray background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, width, height, 5, 5)
        
        # Calculate gauge dimensions
        gauge_rect = self.rect().adjusted(margin, margin, -margin, -margin)
        gauge_rect.setHeight(gauge_rect.height() * 0.7)  # Make room for value display
        
        # Draw background arc
        pen = QPen()
        pen.setWidth(8)
        pen.setColor(QColor(233, 236, 239))  # Light gray
        painter.setPen(pen)
        
        # Draw the background arc (semi-circle)
        start_angle = 30 * 16  # Start at 30 degrees (0 is at 3 o'clock)
        span_angle = 120 * 16  # 120 degrees span
        painter.drawArc(gauge_rect, start_angle, span_angle)
        
        # Calculate the value position
        value_range = self.max_val - self.min_val
        normalized_value = max(0, min(1, (self.value - self.min_val) / value_range))
        value_angle = int(start_angle - normalized_value * span_angle)
        
        # Draw the value arc
        pen.setColor(QColor(13, 110, 253))  # Primary blue
        painter.setPen(pen)
        painter.drawArc(gauge_rect, start_angle, value_angle - start_angle)
        
        # Draw the value text
        font = painter.font()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(33, 37, 41))  # Dark gray
        
        value_rect = QRect(gauge_rect)
        value_rect.setTop(gauge_rect.bottom() - 10)
        value_rect.setHeight(height - gauge_rect.bottom() - 5)
        
        painter.drawText(value_rect, Qt.AlignmentFlag.AlignCenter, f"{self.value:.1f}")
        
        # Draw min/max labels
        small_font = painter.font()
        small_font.setPointSize(8)
        small_font.setBold(False)
        painter.setFont(small_font)
        
        # Min label
        min_rect = QRect(gauge_rect.left() + 5, gauge_rect.bottom() - 15, 30, 15)
        painter.drawText(min_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, f"{self.min_val}")
        
        # Max label
        max_rect = QRect(gauge_rect.right() - 35, gauge_rect.bottom() - 15, 30, 15)
        painter.drawText(max_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom, f"{self.max_val}")
        
    def on_message_received(self, topic, message):
        if topic == self.topic:
            try:
                self.set_value(float(message))
            except (ValueError, TypeError):
                pass
    
    def set_value(self, value):
        try:
            self.value = float(value)
            self.update()  # Trigger repaint
        except (ValueError, TypeError):
            pass
            
    def get_value(self):
        return str(self.value)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update()  # Redraw gauge when resized
