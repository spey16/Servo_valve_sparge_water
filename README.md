# Temperature Control System

A MicroPython-based temperature control system that uses a servo-operated valve to maintain water temperature at a target value (default 78°C).

## Components

1. **Main Controller** (`main.py`): Runs on ESP32, controls the servo valve based on temperature readings
2. **Temperature Simulator** (`simulator.py`): Runs on PC, simulates temperature changes based on valve position
3. **Servo Control** (`servo.py`): Library for controlling the servo motor
4. **WiFi Manager** (`Wifi_Manager.py`): Handles WiFi connection for ESP32

## Configuration

The system uses two configuration files:

1. `config.json` (for ESP32):
   - WiFi credentials
   - MQTT broker settings
   - Temperature targets
   - Valve configuration
   
2. `.env` (for simulator):
   - MQTT settings
   - Temperature simulation parameters
   - Valve parameters

Create these files from the example templates:
```bash
cp config.example.json config.json
cp .env.example .env
```

## Installation

1. ESP32 Setup:
   ```bash
   # Upload files to ESP32
   ampy -p COM_PORT put main.py
   ampy -p COM_PORT put servo.py
   ampy -p COM_PORT put mqtt_client.py
   ampy -p COM_PORT put Wifi_Manager.py
   ampy -p COM_PORT put config.json
   ```

2. Simulator Setup:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Run simulator
   python simulator.py
   ```

## How it Works

1. The ESP32 reads temperature values from MQTT topic `hlt/out/temperature`
2. Based on the temperature, it adjusts the valve position
3. The valve position is published to `valve/position`
4. The simulator reads the valve position and calculates new temperatures
5. The system aims to maintain 78°C by mixing hot (92°C) and cold (15°C) water
