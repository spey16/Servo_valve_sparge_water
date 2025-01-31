import network
import json
import ubinascii

class WiFiManager:
    def __init__(self, credentials_file):
        self.credentials_file = credentials_file
        self.sta_if = network.WLAN(network.STA_IF)
        self.sta_if.active(True)

    def scan_networks(self):
        scan_results = self.sta_if.scan()
        available_ssids = [scan[0].decode() for scan in scan_results]
        return available_ssids

    def connect_to_network(self, ssid, password):
        if ssid in self.scan_networks():
            print("Connecting to '{}'...".format(ssid))
            if not self.sta_if.isconnected():
                self.sta_if.connect(ssid, password)
                while not self.sta_if.isconnected():
                    pass
            print("Connected to '{}'".format(ssid))
            return self.sta_if
        else:
            print("Network '{}' not found in available networks.".format(ssid))

    def run(self):
        wifi_creds = self.load_credentials()
        if wifi_creds is not None:
            available_ssids = self.scan_networks()
            for ssid, password in wifi_creds.items():
                if ssid in available_ssids:
                    return self.connect_to_network(ssid, password)
            else:
                print("No matching network found in available networks.")

    def load_credentials(self):
        try:
            with open(self.credentials_file, 'r') as f:
                wifi_creds = json.load(f)
                wifi_creds = wifi_creds['wifi']
            return wifi_creds
        except OSError:
            print("Failed to load credentials file.")
            return None
