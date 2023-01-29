from dataclasses import dataclass
from typing import Self

from influxdb_client import Point
from influxdb_client.domain.write_precision import WritePrecision


@dataclass
class EmporiaVueLog:
  timestamp_ns: int
  message: str
  mqtt_topic: str

  @classmethod
  def from_mqtt_payload_and_topic(
      cls,
      timestamp_ns: int,
      mqtt_payload: str,
      mqtt_topic: str,
  ) -> Self:
    return cls(timestamp_ns=timestamp_ns, message=mqtt_payload, mqtt_topic=mqtt_topic)

  def to_influxdb_point(self) -> Point:
    # yapf: disable
    return (Point
        .measurement('log')
        .tag('mqtt_topic', self.mqtt_topic)
        .field('message', self.message)
        .time(self.timestamp_ns, write_precision=WritePrecision.NS))  # type: ignore
    # yapf: enable

  def to_influxdb_line_protocol(self) -> str:
    return self.to_influxdb_point().to_line_protocol()
