"""
MQTT Client for publishing temperature readings
"""
from umqtt.simple import MQTTClient
import json

def load_config():
    with open('config.json', 'r') as f:
        return json.loads(f.read())

class MQTTManager:
    def __init__(self, client_id):
        # Load MQTT settings from config
        config = load_config()
        self.broker = config['mqtt']['broker']
        self.port = config['mqtt']['port']
        
        # Create MQTT client
        self.client = MQTTClient(
            client_id=client_id,
            server=self.broker,
            port=self.port,
            keepalive=60
        )
        self.connected = False
        self.last_msg = None
        
        # Set up callback for incoming messages
        self.client.set_callback(self._message_callback)
        
    def _message_callback(self, topic, msg):
        """Callback function for incoming MQTT messages."""
        print(f"Received message on topic {topic}: {msg}")
        self.last_msg = type('Message', (), {'topic': topic, 'payload': msg})
        
    def connect(self):
        try:
            self.client.connect()
            self.connected = True
            print(f"Connected to MQTT broker at {self.broker}:{self.port}")
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT: {e}")
            self.connected = False
            return False
            
    def publish(self, topic, data):
        """Publish data to MQTT topic.
        
        Args:
            topic: MQTT topic to publish to
            data: Data to publish (will be converted to JSON)
        """
        if not self.connected:
            if not self.connect():
                return False
                
        try:
            message = json.dumps(data)
            self.client.publish(topic.encode(), message.encode())
            return True
        except Exception as e:
            print(f"Failed to publish to MQTT: {e}")
            self.connected = False
            return False

    def subscribe(self, topic):
        """Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic to subscribe to
        """
        try:
            print(f"Attempting to subscribe to {topic}")
            self.client.subscribe(topic.encode())
            print(f"Successfully subscribed to topic: {topic}")
            return True
        except Exception as e:
            print(f"Failed to subscribe to topic: {e}")
            return False

    def check_msg(self, topic=None):
        """Check for new messages on subscribed topics.
        
        Args:
            topic: Optional topic to check specifically
            
        Returns:
            bool: True if new message was received, False otherwise
        """
        try:
            self.client.check_msg()
            if self.last_msg is not None:
                if topic is None or self.last_msg.topic.decode() == topic:
                    print(f"Found message for topic {topic}")
                    return True
                else:
                    print(f"Message topic {self.last_msg.topic.decode()} doesn't match requested topic {topic}")
            return False
        except Exception as e:
            print(f"Failed to check messages: {e}")
            return False
