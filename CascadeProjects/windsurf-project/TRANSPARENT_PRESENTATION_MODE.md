# Transparent Presentasjonsmodus - Teknisk Dokumentasjon

Denne guiden forklarer hvordan transparent bakgrunn og widget opacity-justering fungerer i MQTT Dashboard-applikasjonen.

## Oversikt

Presentasjonsmodus gjør applikasjonen frameless med transparent bakgrunn, slik at bare widgets vises over skrivebord eller andre vinduer. Widget opacity kan justeres individuelt eller globalt.

---

## 1. Transparent Bakgrunn - Kritiske Komponenter

### 1.1 WA_TranslucentBackground Attributt

**VIKTIGST:** `Qt.WidgetAttribute.WA_TranslucentBackground` må settes helt først i `MainWindow.__init__()`, før vinduet vises.

```python
# main.py - MainWindow.__init__()
def __init__(self):
    super().__init__()

    # CRITICAL: Set WA_TranslucentBackground FIRST!
    # Must be set before window is shown for transparency to work on Windows
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    # ... rest of initialization
```

**Hvorfor:**
- På Windows fungerer ikke transparent bakgrunn hvis attributtet settes etter at vinduet er vist
- Må settes før `show()`, `setVisible(True)`, eller andre vise-operasjoner
- Kan ikke fjernes og legges til igjen - må være persistent

### 1.2 Window Flags

Når presentasjonsmodus aktiveres, sett frameless og always-on-top flags:

```python
# main.py - toggle_presentation_mode()
self.setWindowFlags(
    Qt.WindowType.Window |
    Qt.WindowType.FramelessWindowHint |
    Qt.WindowType.WindowStaysOnTopHint
)
```

### 1.3 Main Window Transparency

Sett transparent palette og deaktiver auto-fill:

```python
# main.py - apply_presentation_styling()
# Set transparent palette
palette = self.palette()
palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
palette.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0, 0))
palette.setColor(QPalette.ColorRole.AlternateBase, QColor(0, 0, 0, 0))
self.setPalette(palette)
self.setAutoFillBackground(False)

# Also on central widget
central = self.centralWidget()
if central:
    central.setAutoFillBackground(False)
    central_palette = central.palette()
    central_palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0, 0))
    central.setPalette(central_palette)
```

### 1.4 Dashboard Container Transparency

Dashboard og alle containere må settes transparent:

```python
# dashboard.py - set_presentation_mode()
if enabled:
    # Disable auto-fill on all levels
    self.setAutoFillBackground(False)
    self.scroll.setAutoFillBackground(False)
    self.scroll.viewport().setAutoFillBackground(False)
    self.container.setAutoFillBackground(False)

    # Set transparent stylesheets
    self.setStyleSheet("""
        QWidget {
            background-color: transparent;
            background: transparent;
        }
    """)
    self.scroll.setStyleSheet("""
        QScrollArea {
            background-color: transparent;
            background: transparent;
        }
    """)
    self.container.setStyleSheet("""
        #grid_container {
            background-color: transparent;
            background: transparent;
        }
    """)
```

### 1.5 GridContainer PaintEvent

GridContainer må tegne transparent bakgrunn eksplisitt:

```python
# grid_container.py
def __init__(self, grid_size=20, parent=None):
    super().__init__(parent)
    # Set transparent attributes
    self.setAutoFillBackground(False)
    self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

def paintEvent(self, event):
    painter = QPainter(self)

    # Fill with fully transparent first
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
    painter.fillRect(event.rect(), QColor(0, 0, 0, 0))

    if not self.show_grid:
        return

    # Draw grid on top if enabled
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
    # ... draw grid lines
```

**Viktig:** Ikke kall `super().paintEvent()` - det fyller bakgrunnen med standard widget bakgrunn.

---

## 2. Widget Opacity System

### 2.1 Individual Opacity

Hver widget har sin egen `individual_opacity` verdi (0.0 - 1.0) lagret i config:

```python
# resizable_widget.py - apply_config()
opacity = float(self.config.get('individual_opacity', 1.0))

# Convert hex color to rgba with opacity
from PyQt6.QtGui import QColor
qcolor = QColor(bg_color)
rgba_bg = f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {opacity})"

# Apply to background container
self.background_container.setStyleSheet(f"""
    #widget_background {{
        background-color: {rgba_bg};
    }}
""")
```

### 2.2 Global Opacity Slider

Global opacity-slider justerer alle widgets samtidig:

```python
# connection_panel.py
def on_opacity_changed(value):
    # Convert 0-100 to 0.0-1.0
    opacity = value / 100.0
    dashboard.set_widget_opacity(opacity)

# dashboard.py
def set_widget_opacity(self, opacity):
    """Opacity is already in 0.0-1.0 range"""
    for widget in self.widgets:
        if widget is not None:
            # Don't divide by 100 again!
            widget.config['individual_opacity'] = opacity
            widget.apply_config()
```

**Viktig:** Ikke del med 100 to ganger - kun én gang i connection_panel.

### 2.3 Widget Background Structure

Widgets bruker en to-lags struktur for korrekt opacity:

```python
# resizable_widget.py - __init__()
# Outer QFrame is transparent for resize/drag
self.setStyleSheet("QFrame { background: transparent; }")

# Inner container handles appearance
self.background_container = QWidget(self)
self.background_container.setObjectName("widget_background")

# Apply rgba background to inner container
self.background_container.setStyleSheet(f"""
    #widget_background {{
        background-color: {rgba_bg};
        border: {border_width}px solid {border_color};
    }}
""")
```

---

## 3. Button Widget Opacity

Button widgets krever spesiell håndtering siden QPushButton har sin egen styling:

```python
# button_widget.py - apply_button_state_visual()
opacity = float(self.config.get('individual_opacity', 1.0))

if is_on:
    qcolor = QColor(accent_color)
    rgba_accent = f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {opacity})"
    self.button.setStyleSheet(f"background-color: {rgba_accent}; color: {text_color_on};")
else:
    qcolor = QColor(bg_color)
    rgba_bg = f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {opacity})"
    self.button.setStyleSheet(f"background-color: {rgba_bg}; color: {text_color};")
```

---

## 4. PyQt6 Signal Handling Bug

PyQt6's `triggered` signal sender en boolean parameter (checked state) som default:

```python
# FEIL - boolean sendes til file_path parameter:
save_action.triggered.connect(self.save_layout)

# RIKTIG - bruk lambda for å fange checked parameter:
save_action.triggered.connect(lambda checked: self.save_layout())
```

Dette gjelder alle QAction.triggered connections i dashboard context menu.

---

## 5. Viktige Rekkefølger

### Oppstart
1. `MainWindow.__init__()` - Sett `WA_TranslucentBackground` først
2. `init_ui()` - Opprett GUI
3. `show()` - Vis vindu (transparent bakgrunn er nå aktivert)
4. `apply_startup_settings()` - Aktiver presentasjonsmodus hvis konfigurert

### Toggle til Presentasjonsmodus
1. `toggle_presentation_mode()` - Sett window flags
2. `dashboard.set_presentation_mode(True)` - Sett transparent styles på dashboard
3. `apply_presentation_styling()` - Sett transparent styles på main window
4. `show()` - Vis vindu på nytt med nye flags

### Toggle ut av Presentasjonsmodus
1. Gjenopprett window flags
2. `dashboard.set_presentation_mode(False)` - Gjenopprett theme styles
3. Ikke fjern `WA_TranslucentBackground` - behold for fremtidige toggles
4. `show()` - Vis vindu på nytt

---

## 6. Vanlige Fallgruver

### ❌ Setter WA_TranslucentBackground for sent
```python
# FEIL - etter show()
def __init__(self):
    super().__init__()
    self.show()
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)  # For sent!
```

### ❌ Kaller super().paintEvent() i GridContainer
```python
# FEIL - fyller bakgrunn med widget default
def paintEvent(self, event):
    super().paintEvent(event)  # Tegner over transparent bakgrunn!
    # ... draw grid
```

### ❌ Dobbel-divisjon av opacity
```python
# FEIL - deler med 100 to ganger
def on_opacity_changed(value):
    opacity = value / 100.0  # Første divisjon
    dashboard.set_widget_opacity(opacity)

def set_widget_opacity(self, opacity):
    widget.config['individual_opacity'] = opacity / 100.0  # Andre divisjon!
```

### ❌ Glemmer object name selector
```python
# FEIL - påvirker alle child widgets
self.setStyleSheet("QWidget { background-color: transparent; }")

# RIKTIG - påvirker bare parent
self.setObjectName("grid_container")
self.setStyleSheet("#grid_container { background-color: transparent; }")
```

---

## 7. Debugging Tips

### Sjekk om WA_TranslucentBackground er satt
```python
if self.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground):
    print("Transparent bakgrunn er aktivert")
```

### Test GridContainer med farge
```python
# I grid_container.py paintEvent()
painter.fillRect(event.rect(), QColor(0, 255, 0, 128))  # Grønn semi-transparent
```

Hvis du ser grønn bakgrunn, tegner GridContainer. Hvis fortsatt svart, kommer det fra et annet lag.

### Debug opacity verdier
```python
print(f"[DEBUG] Widget {self.topic}: Setting background to rgba({r}, {g}, {b}, {opacity})")
```

Se etter verdier som `rgba(17, 25, 39, 0.0)` (helt transparent) eller feil beregninger.

---

## 8. Oppsummering - Sjekkliste

For å få transparent presentasjonsmodus til å fungere:

- [ ] Sett `WA_TranslucentBackground` først i `MainWindow.__init__()`
- [ ] Sett transparent palette på main window og central widget
- [ ] Deaktiver `autoFillBackground` på alle nivåer
- [ ] Sett transparent stylesheets på dashboard, scroll area, viewport, container
- [ ] GridContainer må tegne transparent i `paintEvent()` (ikke kall super)
- [ ] Widgets bruker rgba() format med opacity i stylesheet
- [ ] Global opacity deles med 100 kun én gang
- [ ] Bruk lambda i signal connections for å unngå boolean parameter
- [ ] Behold `WA_TranslucentBackground` aktivert - ikke fjern ved toggle ut

---

## 9. Filreferanser

- **main.py:288** - WA_TranslucentBackground settes i __init__
- **main.py:1022-1046** - apply_presentation_styling() setter transparent palette
- **dashboard.py:65-133** - set_presentation_mode() håndterer dashboard transparency
- **grid_container.py:6-16** - GridContainer __init__ setter transparent attributter
- **grid_container.py:18-48** - paintEvent tegner transparent bakgrunn
- **resizable_widget.py:27-47** - To-lags struktur for widget opacity
- **resizable_widget.py:423-445** - apply_config() bruker rgba() for opacity
- **button_widget.py:110-134** - Button-spesifikk opacity håndtering
- **dashboard.py:594-599** - Signal connections med lambda

---

## Versjon
Dokumentert: 2025-01-23
Applikasjon versjon: MQTT Dashboard med presentasjonsmodus
