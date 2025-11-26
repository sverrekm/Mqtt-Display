# Ikon-funksjoner i MQTT Display

## Oversikt
MQTT Display støtter nå ikoner for alle widget-typer! Du kan legge til ikoner fra både filer og et innebygd ikon-bibliotek.

## Hvordan legge til ikoner

### 1. Åpne widget-tilpasning
- Høyreklikk på en widget
- Velg "Widget-innstillinger"
- Gå til fanen "Utseende"
- Scroll ned til "Ikon-innstillinger"

### 2. Velg ikon
Klikk på "Velg ikon..." knappen. Du får opp en dialog med to tabs:

#### **Fra fil**
- Velg en ikon-fil fra datamaskinen din
- Støttede formater: PNG, JPG, JPEG, BMP, SVG
- Anbefalt størrelse: 16x16 til 128x128 piksler

#### **Ikon-bibliotek**
Velg fra innebygde ikoner:
- **Basic shapes**: ●, ■, ▲, ★, ♥, ♦
- **Arrows**: ▲, ▼, ◄, ►, ↕, ↔
- **Symbols**: ✓, ✗, +, −, ⚠, ℹ, ⚙
- **Home & Power**: 🏠, ⏻, 💡, 🔋
- **Weather**: ☀, ☁, 🌧, ❄, ⚡, 🌬
- **Temperature**: 🌡, 🔥, ❄
- **Numbers**: 0-9

### 3. Konfigurer ikon
- **Ikonstørrelse**: Velg størrelse fra 8 til 128 piksler
- **Ikonposisjon**: Velg hvor ikonet skal vises
  - **left**: Til venstre for tekst
  - **right**: Til høyre for tekst
  - **top**: Over tekst (kun ResizableWidget title)
  - **bottom**: Under tekst (kun ResizableWidget title)
  - **only**: Bare ikon (kun for button widgets)

### 4. Lagre
Klikk "OK" for å lagre endringene. Ikonet vises nå på widgeten!

## Eksempler på bruk

### Temperature widget
- Velg termometer-ikonet (🌡) fra biblioteket
- Sett størrelse til 24px
- Posisjon: left
- Resultat: "🌡 25.5 °C"

### Light control button
- Velg lyspære-ikonet (💡) fra biblioteket
- Sett størrelse til 32px
- Posisjon: left
- Resultat: Button med lyspære-ikon

### Power button
- Velg power-ikonet (⏻) fra biblioteket
- Sett størrelse til 48px
- Posisjon: only
- Resultat: Button med bare power-ikon (ingen tekst)

### Custom brand icon
- Velg "Fra fil" tab
- Bla til din logo/ikon-fil
- Sett størrelse til 24px
- Posisjon: left

## Andre innstillinger i Widget-innstillinger

### Gjennomsiktighet (Opacity)
I samme dialog kan du også justere widgetens gjennomsiktighet:
- Finn "Gjennomsiktighet" i Utseende-fanen
- Juster verdien fra 0.0 (helt gjennomsiktig) til 1.0 (helt ugjennomsiktig)
- Nyttig for overlay-dashboards og presentasjonsmodus

## Tips
- **Emojis/Unicode**: Ikon-biblioteket bruker Unicode-symboler som fungerer på alle plattformer
- **Filer**: Bruk PNG med gjennomsiktighet for best resultat
- **SVG**: SVG-filer skalerer perfekt til alle størrelser
- **Størrelse**: Start med 16-24px for små widgets, 32-48px for store
- **Konsistens**: Bruk samme størrelse på ikoner for et enhetlig utseende
- **Widget-vindu**: Vinduet "Widget-innstillinger" er nå større (600x700px) for bedre oversikt

## Feilsøking

### Ikonet vises ikke
- Sjekk at filen eksisterer på den angitte plasseringen
- Verifiser at filformatet støttes
- Prøv å velge et ikon fra biblioteket i stedet

### Ikonet er for stort/lite
- Juster "Ikonstørrelse" i Ikon-innstillinger
- For text/emoji-ikoner, juster også widget font-størrelse

### Ikonet har feil farge (text/emoji)
- Text/emoji-ikoner bruker widgetens tekstfarge
- Endre "Tekstfarge" i Utseende-fanen

## Tekniske detaljer
- **Tekst-ikoner**: Lagret som Unicode-strenger, bruker widget font
- **Fil-ikoner**: Lagret som filbane, skalert med Qt
- **Konfigurasjon**: Lagres i widget config som `icon_data`, `icon_is_text`, `icon_size`, `icon_position`
