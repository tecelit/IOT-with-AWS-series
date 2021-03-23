from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import threading
import time as t
import json

# Define ENDPOINT, CLIENT_ID, PATH_TO_CERT, PATH_TO_KEY, PATH_TO_ROOT, TOPIC
ENDPOINT = "a1elv3zi1wh3o2-ats.iot.ap-south-1.amazonaws.com"
CLIENT_ID = "mylaptop2"
PATH_TO_CERT = "certs/certificate.pem.crt"
PATH_TO_KEY = "certs/private.pem.key"
PATH_TO_ROOT = "certs/AmazonRootCA1.pem"
TOPIC = "mytopic"

count = 5 # end after receiving 5 msgs
received_count = 0
received_all_event = threading.Event()


# Callback when the subscribed topic receives a message
def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    print("Received message from topic '{}': {}".format(topic, payload))
    global received_count
    received_count += 1
    if received_count == count:
        received_all_event.set()


if __name__=='__main__':

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
    mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=ENDPOINT,
                cert_filepath=PATH_TO_CERT,
                pri_key_filepath=PATH_TO_KEY,
                client_bootstrap=client_bootstrap,
                ca_filepath=PATH_TO_ROOT,
                client_id=CLIENT_ID,
                clean_session=False,
                keep_alive_secs=6
                )

    print("Connecting to {} with client ID '{}'...".format(
            ENDPOINT, CLIENT_ID))
    # Make the connect() call
    connect_future = mqtt_connection.connect()
    # Future.result() waits until a result is available
    connect_future.result()
    print("Connected!")

    try:
        print("Subscribing to topic : " + TOPIC)
        subscribe_future, packet_id = mqtt_connection.subscribe(
            topic=TOPIC,
            qos=mqtt.QoS.AT_LEAST_ONCE,
            callback=on_message_received
        )

        subscribe_result = subscribe_future.result()
        print("Subscribed with {}".format(str(subscribe_result['qos'])))

        if not received_all_event.is_set():
            print("Waiting for messages.....")

        received_all_event.wait()
        print("{} message(s) received.".format(received_count))

        # Disconnect
        print("Disconnecting...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")

    except KeyboardInterrupt:
        # Disconnect
        print("Disconnecting...")
        disconnect_future = mqtt_connection.disconnect()
        disconnect_future.result()
        print("Disconnected!")