import time
from queue import Empty, Queue
from typing import Any

from absl import app, flags
from line_protocol_cache.producer import LineProtocolCacheProducer
from paho.mqtt.client import Client, MQTTMessage

from emporia_vue_logger.emporiavuelog import EmporiaVueLog
from emporia_vue_logger.emporiavuerecord import EmporiaVueRecord

_MQTT_CLIENT_ID = flags.DEFINE_string(
    name='mqtt_client_id',
    default='styrbar-to-elgato-key-light-air',
    help='The unique client id string used when connecting to the broker.',
)
_MQTT_USERNAME = flags.DEFINE_string(
    name='mqtt_username',
    default=None,
    required=True,
    help='The username to authenticate with. Need have no relationship to the client id.',
)
_MQTT_PASSWORD = flags.DEFINE_string(
    name='mqtt_password',
    default=None,
    required=True,
    help='The password to authenticate with. Optional, set to None if not required.',
)
_MQTT_BROKER_ADDRESS = flags.DEFINE_string(
    name='mqtt_broker_address',
    default=None,
    required=True,
    help='The hostname or IP address of the remote broker.',
)
_MQTT_BROKER_PORT = flags.DEFINE_integer(
    name='mqtt_broker_port',
    default=1883,
    help='The network port of the server host to connect to.',
)
_MQTT_QOS = flags.DEFINE_integer(
    name='mqtt_qos',
    default=2,
    lower_bound=0,
    upper_bound=2,
    help='The desired quality of service level for the subscription.',
)

_MQTT_TOPICS = flags.DEFINE_multi_string(
    name='mqtt_topics',
    default=None,
    required=True,
    help='A list of strings specifying the subscription topic to subscribe to.',
)


def mqtt_client_on_connect(
    mqtt_client: Client,
    userdata: Any,
    flags: dict[str, Any],
    rc: int,
) -> None:
  for topic in _MQTT_TOPICS.value:
    mqtt_client.subscribe(topic, _MQTT_QOS.value)


def mqtt_client_on_message(
    mqtt_client: Client,
    userdata: Any,
    mqtt_message: MQTTMessage,
    line_protocol_queue: Queue[str],
) -> None:
  mqtt_payload = mqtt_message.payload.decode('utf-8')

  if (record := EmporiaVueRecord.from_mqtt_payload(time.time_ns(), mqtt_payload)) is not None:
    line_protocol_queue.put(record.to_influxdb_line_protocol())
    return

  log = EmporiaVueLog.from_mqtt_payload_and_topic(time.time_ns(), mqtt_payload, mqtt_message.topic)
  line_protocol_queue.put(log.to_influxdb_line_protocol())


def collect_records(args: list[str]) -> None:
  with LineProtocolCacheProducer() as producer:
    line_protocol_queue: Queue[str] = Queue()

    mqtt_client = Client(client_id=_MQTT_CLIENT_ID.value, reconnect_on_failure=True)
    mqtt_client.on_connect = mqtt_client_on_connect
    mqtt_client.on_message = lambda mqtt_client, userdata, mqtt_message: mqtt_client_on_message(
        mqtt_client, userdata, mqtt_message, line_protocol_queue)
    mqtt_client.username_pw_set(username=_MQTT_USERNAME.value, password=_MQTT_PASSWORD.value)

    try:
      mqtt_client.connect(host=_MQTT_BROKER_ADDRESS.value, port=_MQTT_BROKER_PORT.value)
      mqtt_client.loop_start()

      pending_line_protocols: list[str] = []
      while True:
        try:
          pending_line_protocols.append(line_protocol_queue.get(block=False))
        except Empty:
          producer.put(pending_line_protocols)
          pending_line_protocols.clear()
          time.sleep(1)
    finally:
      mqtt_client.disconnect()


def main() -> None:
  app.run(collect_records)
