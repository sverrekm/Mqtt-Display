# MQTT Display

A customizable dashboard application for displaying and interacting with MQTT data.

## Features

- Real-time MQTT data visualization
- Multiple widget types (Label, Button, Slider, Gauge)
- Customizable dashboard layout
- Save and load dashboard configurations
- Responsive design

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/sverrekm/Mqtt-Display.git
   cd Mqtt-Display
   ```

2. Create a virtual environment (recommended):
   ```
   python -m venv venv
   .\venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```
   python main.py
   ```

2. Connect to your MQTT broker using the connection panel
3. Add widgets to your dashboard by right-clicking and selecting "Add Widget"
4. Configure each widget with an MQTT topic
5. Save your dashboard layout when you're done

## Widget Types

- **Label**: Displays text or numeric values from MQTT topics
- **Button**: Sends MQTT messages when toggled
- **Slider**: Sends MQTT messages when adjusted
- **Gauge**: Displays numeric values on a semi-circular gauge

## Requirements

- Python 3.8+
- PyQt6
- paho-mqtt

## License

MIT
