from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QColorDialog, QFormLayout,
                             QTabWidget, QWidget, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from config.themes import save_custom_theme, PREDEFINED_THEMES


class CustomThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lag Nytt Globalt Tema")
        self.setModal(True)
        self.setMinimumSize(500, 600)

        # Color values
        self.colors = {
            'background': '#181B1F',
            'surface': '#1F2428',
            'primary': '#FF9830',
            'secondary': '#73BF69',
            'accent': '#6E9FFF',
            'text': '#D9D9D9',
            'text_secondary': '#8E8E8E',
            'border': '#2F3338',
            'success': '#73BF69',
            'warning': '#FF9830',
            'error': '#F2495C',
            'info': '#6E9FFF'
        }

        # Apply dark theme
        self.apply_dark_theme()

        self.init_ui()

    def apply_dark_theme(self):
        """Apply dark theme styling to the dialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit {
                background-color: #404040;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 8px;
                border-radius: 3px;
                min-height: 20px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
                min-height: 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #555555;
            }
        """)

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Theme name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Tema Navn:"))
        self.theme_name_edit = QLineEdit()
        self.theme_name_edit.setPlaceholderText("Mitt Custom Tema")
        name_layout.addWidget(self.theme_name_edit)
        layout.addLayout(name_layout)

        # Theme key (for internal use)
        key_layout = QHBoxLayout()
        key_layout.addWidget(QLabel("Tema ID:"))
        self.theme_key_edit = QLineEdit()
        self.theme_key_edit.setPlaceholderText("custom_theme_1")
        key_layout.addWidget(self.theme_key_edit)
        layout.addLayout(key_layout)

        # Description
        desc_layout = QHBoxLayout()
        desc_layout.addWidget(QLabel("Beskrivelse:"))
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Mitt eget tema...")
        desc_layout.addWidget(self.description_edit)
        layout.addLayout(desc_layout)

        # Tabs for color categories
        tabs = QTabWidget()

        # Main colors tab
        main_tab = QWidget()
        main_layout = QFormLayout(main_tab)

        self.color_buttons = {}

        # Background colors
        self.add_color_row(main_layout, 'background', 'Bakgrunn', 'Hovedbakgrunnsfarge')
        self.add_color_row(main_layout, 'surface', 'Overflate', 'Widget bakgrunnsfarge')

        tabs.addTab(main_tab, "Bakgrunn")

        # Accent colors tab
        accent_tab = QWidget()
        accent_layout = QFormLayout(accent_tab)

        self.add_color_row(accent_layout, 'primary', 'Primær', 'Primærfarge')
        self.add_color_row(accent_layout, 'secondary', 'Sekundær', 'Sekundærfarge')
        self.add_color_row(accent_layout, 'accent', 'Aksent', 'Aksentfarge')

        tabs.addTab(accent_tab, "Aksenter")

        # Text colors tab
        text_tab = QWidget()
        text_layout = QFormLayout(text_tab)

        self.add_color_row(text_layout, 'text', 'Tekst', 'Hovedtekstfarge')
        self.add_color_row(text_layout, 'text_secondary', 'Sekundær Tekst', 'Sekundær tekstfarge')
        self.add_color_row(text_layout, 'border', 'Kant', 'Kantfarge')

        tabs.addTab(text_tab, "Tekst og Kanter")

        # Status colors tab
        status_tab = QWidget()
        status_layout = QFormLayout(status_tab)

        self.add_color_row(status_layout, 'success', 'Suksess', 'Farge for suksess')
        self.add_color_row(status_layout, 'warning', 'Advarsel', 'Farge for advarsel')
        self.add_color_row(status_layout, 'error', 'Feil', 'Farge for feil')
        self.add_color_row(status_layout, 'info', 'Info', 'Farge for info')

        tabs.addTab(status_tab, "Status")

        layout.addWidget(tabs)

        # Buttons
        button_layout = QHBoxLayout()

        preview_btn = QPushButton("Forhåndsvis")
        preview_btn.clicked.connect(self.preview_theme)
        button_layout.addWidget(preview_btn)

        button_layout.addStretch()

        save_btn = QPushButton("Lagre")
        save_btn.clicked.connect(self.save_theme)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Avbryt")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def add_color_row(self, layout, color_key, label, tooltip):
        """Add a color picker row"""
        btn = QPushButton()
        btn.setFixedHeight(30)
        btn.setToolTip(tooltip)
        btn.clicked.connect(lambda: self.choose_color(color_key, btn))
        self.update_color_button(btn, QColor(self.colors[color_key]))
        self.color_buttons[color_key] = btn
        layout.addRow(f"{label}:", btn)

    def choose_color(self, color_key, button):
        """Open color picker"""
        current_color = QColor(self.colors[color_key])
        color = QColorDialog.getColor(current_color, self, f"Velg {color_key} farge")

        if color.isValid():
            self.colors[color_key] = color.name()
            self.update_color_button(button, color)

    def update_color_button(self, button, color):
        """Update button to show selected color"""
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color.name()};
                border: 2px solid #555555;
                color: {'#000000' if color.lightnessF() > 0.5 else '#ffffff'};
            }}
        """)
        button.setText(color.name())

    def preview_theme(self):
        """Show preview of the theme"""
        preview_text = f"""
<b>Tema Forhåndsvisning</b><br><br>
<b style='color: {self.colors['text']}'>Tekst:</b> {self.colors['text']}<br>
<b style='color: {self.colors['accent']}'>Aksent:</b> {self.colors['accent']}<br>
<b style='color: {self.colors['success']}'>Suksess:</b> {self.colors['success']}<br>
<b style='color: {self.colors['warning']}'>Advarsel:</b> {self.colors['warning']}<br>
<b style='color: {self.colors['error']}'>Feil:</b> {self.colors['error']}<br>
<br>
<span style='background-color: {self.colors['surface']}; padding: 5px;'>Overflate farge eksempel</span><br>
<span style='background-color: {self.colors['background']}; padding: 5px;'>Bakgrunn farge eksempel</span>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("Tema Forhåndsvisning")
        msg.setText(preview_text)
        msg.setStyleSheet(f"""
            QMessageBox {{
                background-color: {self.colors['background']};
                color: {self.colors['text']};
            }}
            QLabel {{
                color: {self.colors['text']};
            }}
        """)
        msg.exec()

    def save_theme(self):
        """Save the custom theme"""
        theme_name = self.theme_name_edit.text().strip()
        theme_key = self.theme_key_edit.text().strip()
        description = self.description_edit.text().strip()

        if not theme_name:
            QMessageBox.warning(self, "Feil", "Vennligst oppgi et tema navn")
            return

        if not theme_key:
            QMessageBox.warning(self, "Feil", "Vennligst oppgi en tema ID")
            return

        # Check if theme key already exists in predefined themes
        if theme_key in PREDEFINED_THEMES:
            QMessageBox.warning(self, "Feil", "Denne tema ID-en er allerede i bruk av et forhåndsdefinert tema. Vennligst velg en annen ID.")
            return

        # Create theme data structure
        theme_data = {
            "name": theme_name,
            "description": description or f"Custom tema: {theme_name}",
            "colors": self.colors.copy()
        }

        # Save the theme
        try:
            save_custom_theme(theme_key, theme_data)
            QMessageBox.information(self, "Suksess", f"Tema '{theme_name}' ble lagret!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Feil", f"Kunne ikke lagre tema: {str(e)}")
