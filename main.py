# Start Wifi med "Wifi_Manager.py" og "credentials.json"

from Wifi_Manager import WiFiManager
import machine
from servo import Servo
import time
from mqtt_client import MQTTManager
import json

def load_config():
    with open('config.json', 'r') as f:
        return json.loads(f.read())

def rst():
    machine.reset()

# Load configuration
config = load_config()

# Initialize WiFi
WM = WiFiManager('config.json')
wlan = WM.run()
print(wlan.ifconfig())

# Initialize hardware
motor = Servo(pin=config['valve']['pin'])

# Initialize MQTT client
mqtt = MQTTManager("servo_controller")

# Control parameters from config
TARGET_TEMP = config['temperature']['target']
MAX_ADJUSTMENT = config['valve']['max_adjustment']
BACKLASH = config['valve']['backlash']
last_position = 45  # Start at middle position
last_direction = 0  # -1 for closing, 1 for opening, 0 for initial

def mqtt_callback(topic, msg):
    try:
        topic = topic.decode('utf-8')
        if topic == config['mqtt']['topics']['valve_control']:
            value = int(msg)
            if 0 <= value <= 90:  # Ensure value is in valid range
                move_with_backlash(value)
                print(f"Servo moved to position: {value}")
        elif topic == config['mqtt']['topics']['temperature']:
            temp = float(msg)
            adjust_valve_position(temp)
    except Exception as e:
        print(f"Error processing message: {e}")

def move_with_backlash(target_position):
    global last_position, last_direction
    
    # Determine new direction
    new_direction = 1 if target_position > last_position else -1 if target_position < last_position else 0
    
    # If we're changing direction, move an extra BACKLASH degrees
    if new_direction != 0 and last_direction != 0 and new_direction != last_direction:
        print(f"Direction change: moving extra {BACKLASH}° to handle backlash")
        target_position += BACKLASH * new_direction
    
    # Move to position (with backlash compensation if direction changed)
    motor.move(int(target_position))
    
    # Update state
    last_position = target_position
    if new_direction != 0:  # Only update direction if we actually moved
        last_direction = new_direction
    
    # Publish the new position
    mqtt.client.publish(config['mqtt']['topics']['valve_position'], str(target_position))

def adjust_valve_position(current_temp):
    global last_position
    
    # Calculate temperature difference
    temp_diff = current_temp - TARGET_TEMP
    
    # Calculate adjustment (simple proportional control)
    # Positive temp_diff means we need more cold water (valve more open / lower position)
    # Negative temp_diff means we need less cold water (valve more closed / higher position)
    adjustment = min(max(-MAX_ADJUSTMENT, temp_diff), MAX_ADJUSTMENT)
    
    # Invert the adjustment since valve operates in reverse (90=closed, 0=open)
    adjustment = -adjustment
    
    # Calculate new position
    new_position = min(max(0, last_position + adjustment), 90)
    
    # Only move if the change is significant enough
    if abs(new_position - last_position) >= 0.5:  # Minimum 0.5° change to avoid tiny movements
        move_with_backlash(new_position)
        print(f"Temperature: {current_temp:.2f}°C, Adjusting valve to: {new_position:.1f}° {'(more open)' if new_position < last_position else '(more closed)'}")

# Connect to MQTT and set callback
mqtt.client.set_callback(mqtt_callback)
if mqtt.connect():
    mqtt.client.subscribe(config['mqtt']['topics']['valve_control'].encode())
    mqtt.client.subscribe(config['mqtt']['topics']['temperature'].encode())
    print("Subscribed to MQTT topics")
    
    # Initialize valve position
    move_with_backlash(last_position)
    print(f"Initial valve position: {last_position}° (middle)")

def check_mqtt():
    while True:
        try:
            mqtt.client.check_msg()
            time.sleep(0.1)  # Small delay to prevent overwhelming the CPU
        except Exception as e:
            print(f"MQTT Error: {e}")
            time.sleep(5)  # Wait before trying to reconnect
            mqtt.connect()
            mqtt.client.subscribe(config['mqtt']['topics']['valve_control'].encode())
            mqtt.client.subscribe(config['mqtt']['topics']['temperature'].encode())

# Start the MQTT checking loop
check_mqtt()
