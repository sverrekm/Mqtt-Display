# Oppdatering til Obsidian-notat: MQTT-Display

Denne filen inneholder informasjon som skal legges til i Obsidian-notatet:
`02-Prosjekter/MQTT-Display - Prosjektanalyse og Videre Utvikling.md`

---

## Nylig Implementerte Løsninger (2025-01-23)

### 1. Transparent Presentasjonsmodus - LØST ✅

**Problem**: Presentasjonsmodus viste svart bakgrunn i stedet for transparent bakgrunn.

**Hovedårsak**: `Qt.WidgetAttribute.WA_TranslucentBackground` ble satt for sent i initieringen.

**Løsning**:
- Flyttet `WA_TranslucentBackground` til første linje i `MainWindow.__init__()` (main.py:288)
- Må settes **før** noen annen initiering eller `show()` kall
- Dette er kritisk på Windows - fungerer ikke hvis satt etter at vinduet er vist

**Teknisk implementasjon**:
```python
def __init__(self):
    super().__init__()
    # CRITICAL: Dette MÅ være først!
    self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    # ... resten av initieringen
```

**Andre nødvendige endringer for transparency**:
- GridContainer: Lagt til `WA_NoSystemBackground` og `WA_TranslucentBackground`
- GridContainer.paintEvent(): Fjernet `super().paintEvent()` og tegner eksplisitt transparent
- Dashboard: Satt `autoFillBackground(False)` på alle nivåer
- Alle containere: Transparent stylesheets kaskadert nedover

**Detaljert dokumentasjon**: Se `TRANSPARENT_PRESENTATION_MODE.md` (360 linjer teknisk referanse)

---

### 2. PyQt6 Signal Handling Bug - LØST ✅

**Problem**: Layout save/load feilet med feilmelding om file path.

**Hovedårsak**: PyQt6's `QAction.triggered` signal sender en boolean parameter (checked state) som default.

**Symptom**: Når man klikket "Save Layout", ble `save_layout(False)` kalt i stedet for `save_layout()`, fordi False-verdien fra triggered-signalet ble sendt til `file_path` parameteren.

**Løsning**:
Bruk lambda for å fange boolean-parameteren og kalle funksjonen uten argumenter:

```python
# FEIL:
save_action.triggered.connect(self.save_layout)

# RIKTIG:
save_action.triggered.connect(lambda checked: self.save_layout())
```

**Påvirket kode**:
- dashboard.py:594-599 - Alle context menu signal connections
- Alle andre `triggered.connect()` kall i applikasjonen

---

### 3. Widget Opacity Kontroll - LØST ✅

**Problem**: Global opacity slider satte alle widgets til 0% i stedet for ønsket verdi.

**Årsak**: Opacity ble dividert med 100 to ganger:
1. I `connection_panel.py` når slider value konverteres (0-100 → 0.0-1.0)
2. I `dashboard.py` når opacity settes på widget

**Løsning**: Fjernet den andre divisjonen i dashboard.py:262

```python
# connection_panel.py
def on_opacity_changed(value):
    opacity = value / 100.0  # Konverter 0-100 til 0.0-1.0
    dashboard.set_widget_opacity(opacity)

# dashboard.py
def set_widget_opacity(self, opacity):
    # opacity er allerede i 0.0-1.0 range
    widget.config['individual_opacity'] = opacity  # IKKE del med 100 igjen!
```

---

### 4. Teknisk Arkitektur: Widget Transparency

**To-lags struktur for korrekt opacity**:
```
ResizableWidget (outer QFrame)
└── background_container (inner QWidget)
    ├── Håndterer rgba bakgrunn med opacity
    └── Inneholder widget-spesifikk innhold
```

**Hvorfor to lag?**:
- Outer frame: Transparent, håndterer resize/drag
- Inner container: Har bakgrunnsfarge med opacity via `rgba()` i stylesheet

**Opacity i stylesheets**:
```python
opacity = float(self.config.get('individual_opacity', 1.0))
qcolor = QColor(bg_color)
rgba_bg = f"rgba({qcolor.red()}, {qcolor.green()}, {qcolor.blue()}, {opacity})"
self.background_container.setStyleSheet(f"background-color: {rgba_bg};")
```

---

## Viktige Filer og Linjenumre

| Fil | Linjer | Beskrivelse |
|-----|--------|-------------|
| main.py | 288 | WA_TranslucentBackground settes først |
| main.py | 1022-1046 | apply_presentation_styling() |
| dashboard.py | 65-133 | set_presentation_mode() |
| dashboard.py | 594-599 | Signal connections med lambda |
| grid_container.py | 6-16 | Transparency attributter |
| grid_container.py | 18-48 | Transparent paintEvent |
| resizable_widget.py | 27-47 | To-lags widget struktur |
| resizable_widget.py | 423-445 | apply_config() med rgba opacity |
| button_widget.py | 110-134 | Button-spesifikk opacity |

---

## Sjekkliste: Transparent Presentasjonsmodus

For fremtidig vedlikehold, husk:

- [x] WA_TranslucentBackground MÅ settes først i __init__
- [x] Transparent palette på main window og central widget
- [x] autoFillBackground(False) på alle nivåer
- [x] Transparent stylesheets på dashboard, scroll area, viewport, container
- [x] GridContainer tegner transparent i paintEvent (ikke kall super)
- [x] Widgets bruker rgba() format med opacity i stylesheet
- [x] Global opacity deles med 100 kun én gang
- [x] Bruk lambda i triggered signal connections
- [x] Behold WA_TranslucentBackground aktivert - ikke fjern ved toggle

---

## Dokumentasjon

**Hovedfil**: `TRANSPARENT_PRESENTATION_MODE.md`
- 9 seksjoner med komplett teknisk referanse
- Vanlige fallgruver med kodeeksempler
- Debugging tips
- Filreferanser med linjenumre

**Status**: Alle kritiske bugs relatert til transparent presentasjonsmodus er løst ✅

---

## Neste Steg / Fremtidige Forbedringer

Forslag til videre utvikling:
1. Persistence av presentation mode state ved oppstart
2. Keyboard shortcuts for rask toggle av presentation mode
3. Multi-monitor støtte for presentation mode
4. Animerte transitions inn/ut av presentation mode
5. Custom opacity presets (fx. "subtle", "normal", "bold")

---

*Sist oppdatert: 2025-01-23*
*Versjon: MQTT Dashboard med fullstendig transparent presentasjonsmodus*
