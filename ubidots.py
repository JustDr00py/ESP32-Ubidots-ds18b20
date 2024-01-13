import time
from umqtt.simple import MQTTClient
import urequests
import machine
import onewire
import ds18x20
import network

def temp_sensor(WIFI_SSID, WIFI_PASSWORD, UBIDOTS_TOKEN, UBIDOTS_DEVICE_LABEL, SENSOR_PIN, SLEEP_TIME):
    # Connect to Wi-Fi
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(WIFI_SSID, WIFI_PASSWORD)
    
    # Wait for Wi-Fi connection
    while not wifi.isconnected():
        pass

    print("Wi-Fi connected. IP address:", wifi.ifconfig()[0])

    # Create a one-wire bus object
    ow = onewire.OneWire(machine.Pin(SENSOR_PIN))  # Example: Pin 2 (D4) as the data line

    # Create a DS18X20 sensor object
    ds = ds18x20.DS18X20(ow)

    # Scan for DS18B20 devices on the bus
    roms = ds.scan()

    # Ubidots MQTT callback function
    def ubidots_callback(topic, msg):
        print("Received message from Ubidots: Topic={}, Message={}".format(topic, msg))
        # You can add custom handling here if required

    # Connect to Ubidots MQTT broker
    client = MQTTClient("homenodeuser-11", "industrial.api.ubidots.com", user=UBIDOTS_TOKEN, password="", port=1883, keepalive=60)
    client.set_callback(ubidots_callback)
    client.connect()
    # Perform temperature conversion for all detected sensors
    ds.convert_temp()

    # Wait for conversion to complete (750ms for the DS18B20)
    time.sleep_ms(750)

    # Read the temperature from each sensor
    for rom in roms:
        temp = ds.read_temp(rom)
        temp = temp * 1.8 + 32
        # Publish temperature data to Ubidots MQTT
        topic = f"/v1.6/devices/{UBIDOTS_DEVICE_LABEL}/temperature"
        payload = '{{"value": {}}}'.format(temp)
        client.publish(topic, payload.encode())

        # Print logs for debugging (optional)
        print("Published data to Ubidots: Topic={}, Payload={}".format(topic, payload))

    # Subscribe to wait for any possible response from Ubidots (optional)
    client.subscribe(topic)

    # Wait for a response from Ubidots (optional)
    client.wait_msg()

    # Disconnect from Ubidots MQTT broker
    # client.disconnect()
    machine.deepsleep(SLEEP_TIME)  # Delay between readings

