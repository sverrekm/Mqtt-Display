from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                           QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, 
                           QColorDialog, QLabel, QComboBox, QCheckBox, QTabWidget, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette

class WidgetCustomizationDialog(QDialog):
    def __init__(self, widget_type, current_config=None, parent=None):
        super().__init__(parent)
        self.widget_type = widget_type
        self.config = current_config or {}
        
        self.setWindowTitle(f"Tilpass {widget_type.capitalize()} Widget")
        self.setModal(True)
        self.setMinimumSize(400, 500)
        
        self.init_ui()
        self.load_current_config()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tabs for different customization categories
        self.tabs = QTabWidget()
        
        # General tab
        self.general_tab = QWidget()
        self.init_general_tab()
        self.tabs.addTab(self.general_tab, "Generelt")
        
        # Appearance tab
        self.appearance_tab = QWidget()
        self.init_appearance_tab()
        self.tabs.addTab(self.appearance_tab, "Utseende")
        
        # Data tab (for gauge and numeric widgets)
        if self.widget_type in ['gauge', 'label']:
            self.data_tab = QWidget()
            self.init_data_tab()
            self.tabs.addTab(self.data_tab, "Data & Enheter")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Forhåndsvis")
        self.preview_btn.clicked.connect(self.preview_changes)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("Avbryt")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def init_general_tab(self):
        layout = QFormLayout(self.general_tab)
        
        # Display name
        self.display_name = QLineEdit()
        self.display_name.setPlaceholderText("Navn som vises på widget")
        layout.addRow("Visningsnavn:", self.display_name)
        
        # Description
        self.description = QLineEdit()
        self.description.setPlaceholderText("Beskrivelse av widget")
        layout.addRow("Beskrivelse:", self.description)
        
        # Show title
        self.show_title = QCheckBox("Vis tittel")
        self.show_title.setChecked(True)
        layout.addRow("", self.show_title)
        
        # Show close button
        self.show_close = QCheckBox("Vis lukkeknapp")
        self.show_close.setChecked(True)
        layout.addRow("", self.show_close)
    
    def init_appearance_tab(self):
        layout = QFormLayout(self.appearance_tab)
        
        # Background color
        self.bg_color_btn = QPushButton()
        self.bg_color_btn.setFixedHeight(30)
        self.bg_color_btn.clicked.connect(lambda: self.choose_color('background'))
        self.bg_color = QColor("#ffffff")
        self.update_color_button(self.bg_color_btn, self.bg_color)
        layout.addRow("Bakgrunnsfarge:", self.bg_color_btn)
        
        # Text color
        self.text_color_btn = QPushButton()
        self.text_color_btn.setFixedHeight(30)
        self.text_color_btn.clicked.connect(lambda: self.choose_color('text'))
        self.text_color = QColor("#000000")
        self.update_color_button(self.text_color_btn, self.text_color)
        layout.addRow("Tekstfarge:", self.text_color_btn)
        
        # Border color
        self.border_color_btn = QPushButton()
        self.border_color_btn.setFixedHeight(30)
        self.border_color_btn.clicked.connect(lambda: self.choose_color('border'))
        self.border_color = QColor("#dee2e6")
        self.update_color_button(self.border_color_btn, self.border_color)
        layout.addRow("Kantfarge:", self.border_color_btn)
        
        # Accent color (for gauges, progress bars etc.)
        if self.widget_type in ['gauge', 'slider']:
            self.accent_color_btn = QPushButton()
            self.accent_color_btn.setFixedHeight(30)
            self.accent_color_btn.clicked.connect(lambda: self.choose_color('accent'))
            self.accent_color = QColor("#0d6efd")
            self.update_color_button(self.accent_color_btn, self.accent_color)
            layout.addRow("Aksentfarge:", self.accent_color_btn)
        
        # Font size
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 48)
        self.font_size.setValue(12)
        self.font_size.setSuffix(" px")
        layout.addRow("Skriftstørrelse:", self.font_size)
        
        # Border width
        self.border_width = QSpinBox()
        self.border_width.setRange(0, 10)
        self.border_width.setValue(2)
        self.border_width.setSuffix(" px")
        layout.addRow("Kanttykkelse:", self.border_width)
        
        # Border radius
        self.border_radius = QSpinBox()
        self.border_radius.setRange(0, 20)
        self.border_radius.setValue(6)
        self.border_radius.setSuffix(" px")
        layout.addRow("Kantavrunding:", self.border_radius)
    
    def init_data_tab(self):
        layout = QFormLayout(self.data_tab)
        
        # Unit
        self.unit = QLineEdit()
        self.unit.setPlaceholderText("f.eks. °C, kW, %")
        layout.addRow("Enhet:", self.unit)
        
        # Decimal places
        self.decimal_places = QSpinBox()
        self.decimal_places.setRange(0, 6)
        self.decimal_places.setValue(1)
        layout.addRow("Desimalplasser:", self.decimal_places)
        
        # Conversion factor
        self.conversion_factor = QDoubleSpinBox()
        self.conversion_factor.setRange(-999999.0, 999999.0)
        self.conversion_factor.setValue(1.0)
        self.conversion_factor.setDecimals(6)
        layout.addRow("Omregningsfaktor:", self.conversion_factor)
        
        # Conversion offset
        self.conversion_offset = QDoubleSpinBox()
        self.conversion_offset.setRange(-999999.0, 999999.0)
        self.conversion_offset.setValue(0.0)
        self.conversion_offset.setDecimals(6)
        layout.addRow("Omregningsoffset:", self.conversion_offset)
        
        # Min/Max values (for gauges)
        if self.widget_type == 'gauge':
            self.min_value = QDoubleSpinBox()
            self.min_value.setRange(-999999.0, 999999.0)
            self.min_value.setValue(0.0)
            layout.addRow("Minimumsverdi:", self.min_value)
            
            self.max_value = QDoubleSpinBox()
            self.max_value.setRange(-999999.0, 999999.0)
            self.max_value.setValue(100.0)
            layout.addRow("Maksimumsverdi:", self.max_value)
            
            # Warning thresholds
            self.warning_enabled = QCheckBox("Aktiver advarselsgrenser")
            layout.addRow("", self.warning_enabled)
            
            self.warning_low = QDoubleSpinBox()
            self.warning_low.setRange(-999999.0, 999999.0)
            self.warning_low.setValue(20.0)
            layout.addRow("Lav advarsel:", self.warning_low)
            
            self.warning_high = QDoubleSpinBox()
            self.warning_high.setRange(-999999.0, 999999.0)
            self.warning_high.setValue(80.0)
            layout.addRow("Høy advarsel:", self.warning_high)
            
            # Warning colors
            self.warning_color_btn = QPushButton()
            self.warning_color_btn.setFixedHeight(30)
            self.warning_color_btn.clicked.connect(lambda: self.choose_color('warning'))
            self.warning_color = QColor("#ffc107")
            self.update_color_button(self.warning_color_btn, self.warning_color)
            layout.addRow("Advarselsfarge:", self.warning_color_btn)
            
            self.critical_color_btn = QPushButton()
            self.critical_color_btn.setFixedHeight(30)
            self.critical_color_btn.clicked.connect(lambda: self.choose_color('critical'))
            self.critical_color = QColor("#dc3545")
            self.update_color_button(self.critical_color_btn, self.critical_color)
            layout.addRow("Kritisk farge:", self.critical_color_btn)
    
    def choose_color(self, color_type):
        """Open color picker dialog"""
        # Map color_type to actual attribute name
        color_map = {
            'background': 'bg_color',
            'text': 'text_color',
            'border': 'border_color',
            'accent': 'accent_color',
            'warning': 'warning_color',
            'critical': 'critical_color'
        }
        
        attr_name = color_map.get(color_type, f"{color_type}_color")
        current_color = getattr(self, attr_name)
        color = QColorDialog.getColor(current_color, self, f"Velg {color_type} farge")
        
        if color.isValid():
            setattr(self, attr_name, color)
            button = getattr(self, f"{attr_name}_btn")
            self.update_color_button(button, color)
    
    def update_color_button(self, button, color):
        """Update button appearance to show selected color"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: 2px solid #333;
                border-radius: 4px;
            }}
        """)
        button.setText(color.name())
    
    def load_current_config(self):
        """Load current widget configuration into dialog"""
        if not self.config:
            return
        
        # General settings
        self.display_name.setText(self.config.get('display_name', ''))
        self.description.setText(self.config.get('description', ''))
        self.show_title.setChecked(self.config.get('show_title', True))
        self.show_close.setChecked(self.config.get('show_close', True))
        
        # Appearance settings
        if 'bg_color' in self.config:
            self.bg_color = QColor(self.config['bg_color'])
            self.update_color_button(self.bg_color_btn, self.bg_color)
        
        if 'text_color' in self.config:
            self.text_color = QColor(self.config['text_color'])
            self.update_color_button(self.text_color_btn, self.text_color)
        
        if 'border_color' in self.config:
            self.border_color = QColor(self.config['border_color'])
            self.update_color_button(self.border_color_btn, self.border_color)
        
        if hasattr(self, 'accent_color') and 'accent_color' in self.config:
            self.accent_color = QColor(self.config['accent_color'])
            self.update_color_button(self.accent_color_btn, self.accent_color)
        
        self.font_size.setValue(self.config.get('font_size', 12))
        self.border_width.setValue(self.config.get('border_width', 2))
        self.border_radius.setValue(self.config.get('border_radius', 6))
        
        # Data settings
        if hasattr(self, 'unit'):
            self.unit.setText(self.config.get('unit', ''))
            self.decimal_places.setValue(self.config.get('decimal_places', 1))
            self.conversion_factor.setValue(self.config.get('conversion_factor', 1.0))
            self.conversion_offset.setValue(self.config.get('conversion_offset', 0.0))
        
        # Gauge specific settings
        if hasattr(self, 'min_value'):
            self.min_value.setValue(self.config.get('min_value', 0.0))
            self.max_value.setValue(self.config.get('max_value', 100.0))
            self.warning_enabled.setChecked(self.config.get('warning_enabled', False))
            self.warning_low.setValue(self.config.get('warning_low', 20.0))
            self.warning_high.setValue(self.config.get('warning_high', 80.0))
            
            if 'warning_color' in self.config:
                self.warning_color = QColor(self.config['warning_color'])
                self.update_color_button(self.warning_color_btn, self.warning_color)
            
            if 'critical_color' in self.config:
                self.critical_color = QColor(self.config['critical_color'])
                self.update_color_button(self.critical_color_btn, self.critical_color)
    
    def get_config(self):
        """Get the current configuration from dialog"""
        config = {
            # General
            'display_name': self.display_name.text(),
            'description': self.description.text(),
            'show_title': self.show_title.isChecked(),
            'show_close': self.show_close.isChecked(),
            
            # Appearance
            'bg_color': self.bg_color.name(),
            'text_color': self.text_color.name(),
            'border_color': self.border_color.name(),
            'font_size': self.font_size.value(),
            'border_width': self.border_width.value(),
            'border_radius': self.border_radius.value(),
        }
        
        # Add accent color if available
        if hasattr(self, 'accent_color'):
            config['accent_color'] = self.accent_color.name()
        
        # Data settings
        if hasattr(self, 'unit'):
            config.update({
                'unit': self.unit.text(),
                'decimal_places': self.decimal_places.value(),
                'conversion_factor': self.conversion_factor.value(),
                'conversion_offset': self.conversion_offset.value(),
            })
        
        # Gauge specific settings
        if hasattr(self, 'min_value'):
            config.update({
                'min_value': self.min_value.value(),
                'max_value': self.max_value.value(),
                'warning_enabled': self.warning_enabled.isChecked(),
                'warning_low': self.warning_low.value(),
                'warning_high': self.warning_high.value(),
                'warning_color': self.warning_color.name(),
                'critical_color': self.critical_color.name(),
            })
        
        return config
    
    def preview_changes(self):
        """Preview the changes (could be implemented to show a preview widget)"""
        # For now, just show a message with the current config
        config = self.get_config()
        print(f"Preview config: {config}")
        # TODO: Implement actual preview functionality
