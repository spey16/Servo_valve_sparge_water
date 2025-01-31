import paho.mqtt.client as mqtt
import time
import random
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

# MQTT settings from environment
MQTT_BROKER = os.getenv('MQTT_BROKER')
MQTT_PORT = int(os.getenv('MQTT_PORT'))
CLIENT_ID = "temp_simulator"

# Temperature simulation parameters from environment
HOT_WATER_TEMP = float(os.getenv('HOT_WATER_TEMP'))
COLD_WATER_TEMP = float(os.getenv('COLD_WATER_TEMP'))
NOISE_FACTOR = float(os.getenv('NOISE_FACTOR'))
THERMAL_INERTIA = float(os.getenv('THERMAL_INERTIA'))
TARGET_TEMP = float(os.getenv('TARGET_TEMP'))

# Topics from environment
TOPIC_TEMPERATURE = os.getenv('MQTT_TOPIC_TEMPERATURE')
TOPIC_VALVE_POSITION = os.getenv('MQTT_TOPIC_VALVE_POSITION')

# Valve parameters
VALVE_CENTER = 45.0  # Position where we want target temperature
VALVE_SCALE = 1.0    # How much each degree of valve movement affects temperature
VALVE_BACKLASH = float(os.getenv('VALVE_BACKLASH'))

class TemperatureSimulator:
    def __init__(self):
        self.client = mqtt.Client(CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.current_temp = TARGET_TEMP  # Start at target temperature
        self.valve_position = VALVE_CENTER  # Current valve position (90=closed, 0=open)
        self.last_position = VALVE_CENTER   # Track last position to detect direction changes
        self.last_direction = 0   # Track movement direction
    
    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code "+str(rc))
        # Subscribe to valve position updates
        client.subscribe(TOPIC_VALVE_POSITION)
    
    def on_message(self, client, userdata, msg):
        if msg.topic == TOPIC_VALVE_POSITION:
            try:
                new_position = float(msg.payload.decode())
                
                # Calculate actual valve position by removing backlash compensation
                if self.last_direction != 0:
                    new_direction = 1 if new_position > self.last_position else -1
                    if new_direction != self.last_direction:
                        # If direction changed, the actual position is 15° less in that direction
                        new_position -= VALVE_BACKLASH * new_direction
                
                self.valve_position = new_position
                print(f"Valve position updated to: {self.valve_position}° (received: {float(msg.payload.decode())}°)")
                
                # Update tracking variables
                if new_position != self.last_position:
                    self.last_direction = 1 if new_position > self.last_position else -1
                    self.last_position = new_position
                
            except Exception as e:
                print(f"Invalid valve position received: {e}")
    
    def calculate_mixed_temp(self):
        # Calculate temperature based on valve position relative to center point
        valve_offset = self.valve_position - VALVE_CENTER
        
        # Temperature offset from target based on valve position
        # Positive offset (valve > 45) makes it hotter
        # Negative offset (valve < 45) makes it colder
        temp_offset = valve_offset * VALVE_SCALE
        
        # Calculate ideal temperature (target ± offset)
        ideal_temp = TARGET_TEMP + temp_offset
        
        # Clamp temperature between cold and hot water limits
        ideal_temp = min(max(ideal_temp, COLD_WATER_TEMP), HOT_WATER_TEMP)
        
        # Add thermal inertia (slow change) and noise
        noise = (random.random() - 0.5) * NOISE_FACTOR
        self.current_temp = (self.current_temp * THERMAL_INERTIA + 
                           ideal_temp * (1 - THERMAL_INERTIA) + noise)
        
        return round(self.current_temp, 2)
    
    def run(self):
        print("Starting temperature simulator...")
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            # Start the MQTT loop in a background thread
            self.client.loop_start()
            
            print(f"Initial valve position: {self.valve_position}° (middle)")
            print(f"Target temperature: {TARGET_TEMP}°C")
            print(f"Hot water: {HOT_WATER_TEMP}°C, Cold water: {COLD_WATER_TEMP}°C")
            print(f"Valve calibration: {TARGET_TEMP}°C at {VALVE_CENTER}° valve position")
            print(f"Temperature change per degree: {VALVE_SCALE}°C")
            print("Publishing temperatures every second...")
            
            while True:
                # Calculate and publish new temperature
                temp = self.calculate_mixed_temp()
                self.client.publish(TOPIC_TEMPERATURE, str(temp))
                print(f"Published temperature: {temp}°C (valve: {self.valve_position}°)")
                
                # Wait before next update
                time.sleep(1)
                
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait before retry
            self.run()  # Retry connection
        finally:
            self.client.loop_stop()

if __name__ == '__main__':
    simulator = TemperatureSimulator()
    simulator.run()
