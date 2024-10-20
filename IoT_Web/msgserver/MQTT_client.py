from datetime import datetime
from django.utils import timezone
import json
import threading

from awscrt import mqtt
from awsiot import mqtt_connection_builder

from .models import Message

_MQTT_CREDENTIAL = (
    '../connect_device_package/G29-Webapp.cert.pem',
    '../connect_device_package/G29-Webapp.private.key'
)
_MQTT_CONFIG = {
    'endpoint': 'a1c4jlyd81rs41-ats.iot.ap-southeast-2.amazonaws.com',
    'port': 8883,
    'ca_filepath': '../connect_device_package/root-CA.crt',
    'client_id': 'DjangoWebApp',
    'clean_session': False,
    'keep_alive_secs': 30,
}

_TOPIC = "sdk/test/python"

conn = None
received_all_event = threading.Event()

def start_MQTT_client():
    global conn
    conn = mqtt_connection_builder.mtls_from_path(
        *_MQTT_CREDENTIAL,
        **_MQTT_CONFIG,
        on_connection_interrupted=on_connection_interrupted,
        on_connection_resumed=on_connection_resumed,
        on_connection_success=on_connection_success,
        on_connection_failure=on_connection_failure,
        on_connection_closed=on_connection_closed
    )
    connect_future = conn.connect()
    connect_future.result()  # blocking
    print("Connected!")
    subscribe_future, packet_id = conn.subscribe(
        topic=_TOPIC,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message_received)

    subscribe_result = subscribe_future.result()
    print("Subscribed with {}".format(str(subscribe_result['qos'])))
    try:
        received_all_event.wait()
    except KeyboardInterrupt:
        stop_MQTT_client() # Stop the client gracefully



def stop_MQTT_client():
    global conn
    if conn is not None:
        print("Disconnecting...")
        disconnect_future = conn.disconnect()
        disconnect_future.result()
        print("Disconnected!")


def on_connection_resumed(connection, return_code, session_present, **kwargs):
    print("Connection resumed. return_code: {} session_present: {}".format(return_code, session_present))

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        print("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()

        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    print("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            print("Server rejected resubscribe to topic: {}".format(topic))


def on_connection_success(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionSuccessData)
    print("Connection Successful with return code: {} session present: {}".format(callback_data.return_code, callback_data.session_present))


def on_connection_interrupted(connection, error, **kwargs):
    print("Connection interrupted. error: {}".format(error))


def on_connection_failure(connection, callback_data):
    assert isinstance(callback_data, mqtt.OnConnectionFailureData)
    print("Connection failed with error code: {}".format(callback_data.error))


def on_connection_closed(connection, callback_data):
    print("Connection closed")


def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    msg = json.loads(payload)
    message_timestamp = datetime.fromtimestamp(msg['timestamp'])
    aware_datetime = timezone.make_aware(message_timestamp)
    print("Received message from topic '{}': {}".format(topic, payload))
    Message.objects.create(
        payload=msg['payload'],
        timestamp=aware_datetime
    )



