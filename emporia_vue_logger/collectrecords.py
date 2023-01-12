import time
from typing import Any

from absl import app, flags, logging
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

_MQTT_TOPICS = flags.DEFINE_multi_string(
    name='mqtt_topics',
    default=None,
    required=True,
    help='A list of strings specifying the subscription topic to subscribe to.',
)


def mqtt_client_on_message(
    mqtt_client: Client,
    userdata: Any,
    mqtt_message: MQTTMessage,
    producer: LineProtocolCacheProducer,
) -> None:
  mqtt_payload = mqtt_message.payload.decode('utf-8')

  if (record := EmporiaVueRecord.from_mqtt_payload(time.time_ns(), mqtt_payload)) is not None:
    producer.put(record.to_influxdb_line_protocols())
    return

  producer.put(
      EmporiaVueLog.from_mqtt_payload(time.time_ns(), mqtt_payload).to_influxdb_line_protocols())


def get_mqtt_client(on_message) -> Client:
  mqtt_client = Client(client_id=_MQTT_CLIENT_ID.value)
  mqtt_client.username_pw_set(username=_MQTT_USERNAME.value, password=_MQTT_PASSWORD.value)
  mqtt_client.connect(host=_MQTT_BROKER_ADDRESS.value, port=_MQTT_BROKER_PORT.value, keepalive=10)
  for topic in _MQTT_TOPICS.value:
    mqtt_client.subscribe(topic)
  mqtt_client.on_message = on_message
  return mqtt_client


def collect_records(args: list[str]) -> None:
  with LineProtocolCacheProducer() as producer:
    on_message = lambda mc, u, mm: mqtt_client_on_message(mc, u, mm, producer)
    mqtt_client = get_mqtt_client(on_message)

    try:
      mqtt_client.loop_forever()
    finally:
      mqtt_client.disconnect()


def main() -> None:
  app.run(collect_records)