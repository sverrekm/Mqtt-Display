# Toggle Widget - Brukerveiledning

## Hva er en Toggle Widget?
En toggle widget er en on/off-bryter som sender konfigurerbare MQTT payloads basert på om den er på eller av.

## Legge til en Toggle
1. Klikk **"+"** (Add Widget)
2. Velg **"toggle"** fra dropdown
3. Skriv inn MQTT topic
4. Klikk **OK**

## Konfigurere Toggle Payloads

### Åpne innstillinger:
1. Høyreklikk på toggle widget
2. Velg **"Widget-innstillinger"**
3. Gå til **"Data & Enheter"** fanen

### Tilgjengelige innstillinger:

**ON payload:**
- Dette sendes når togglen slås PÅ
- Standard: "1"
- Eksempler: "ON", "true", "1", '{"state":"on"}'

**OFF payload:**
- Dette sendes når togglen slås AV
- Standard: "0"
- Eksempler: "OFF", "false", "0", '{"state":"off"}'

**MQTT input-topic:** (valgfritt)
- Topic som togglen lytter på for å oppdatere sin state
- Nyttig for å synkronisere toggle med faktisk device-status
- Eksempel: Hvis du sender til `light/kitchen/command`, kan input være `light/kitchen/state`

## Utseende og Farger

I **"Utseende"** fanen kan du konfigurere:

**Aksentfarge (ON):**
- Fargen når togglen er på
- Standard: Blå (#0d6efd)

**Toggle OFF farge:**
- Fargen når togglen er av
- Standard: Grå (#6c757d)

**Toggle håndtak farge:**
- Fargen på håndtaket (ikke synlig i forenklet versjon)
- Standard: Hvit (#ffffff)

## Eksempler på bruk

### 1. Smart Lys
```
Topic: home/livingroom/light/set
ON payload: ON
OFF payload: OFF
Input topic: home/livingroom/light/status
```

### 2. Relé/Bryter
```
Topic: relay/1/command
ON payload: 1
OFF payload: 0
Input topic: relay/1/state
```

### 3. JSON Format
```
Topic: device/esp32/gpio
ON payload: {"pin":12,"state":true}
OFF payload: {"pin":12,"state":false}
Input topic: device/esp32/status
```

### 4. Home Assistant
```
Topic: homeassistant/switch/bedroom/set
ON payload: ON
OFF payload: OFF
Input topic: homeassistant/switch/bedroom/state
```

## Feilsøking

### Togglen reagerer ikke når jeg klikker
- Sjekk at du klikker direkte på toggle-switchen (rund bryter)
- Se i konsoll-output etter `[DEBUG] Toggle toggled!` meldinger
- Restart applikasjonen

### Togglen sender ikke MQTT meldinger
- Sjekk at du er koblet til MQTT broker (grønn status)
- Se i konsoll etter `[DEBUG] Toggle published:` meldinger
- Verifiser topic-navn

### Togglen oppdateres ikke fra MQTT
- Sjekk at "MQTT input-topic" er riktig konfigurert
- Verifiser at payloads matcher (case-sensitive!)
- Se etter `[DEBUG] Toggle state updated from MQTT:` i konsoll

### Jeg ser ikke "Data & Enheter" fanen
- Dette er nå fikset - restart applikasjonen
- Alle toggle widgets skal nå ha denne fanen

## Tips
- Bruk samme payload-format som ditt smart home system
- Test med MQTT Explorer eller lignende tool for å se meldinger
- Bruk input-topic for å holde toggle synkronisert med faktisk tilstand
- Toggle kan brukes for alt som har to states (on/off, open/close, etc.)
