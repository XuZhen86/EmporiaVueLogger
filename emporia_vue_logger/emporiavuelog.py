from dataclasses import dataclass
from typing import Self

from influxdb_client import Point
from influxdb_client.domain.write_precision import WritePrecision
from paho.mqtt.client import MQTTMessage


@dataclass
class EmporiaVueLog:
  timestamp_ns: int
  message: str

  @classmethod
  def from_mqtt_payload(cls, timestamp_ns: int, mqtt_payload: str) -> Self:
    return cls(timestamp_ns=timestamp_ns, message=mqtt_payload)

  def to_influxdb_points(self) -> list[Point]:
    # yapf: disable
    return  [
        Point
            .measurement('log')
            .field('message', self.message)
            .time(self.timestamp_ns, write_precision=WritePrecision.NS)
    ]
    # yapf: enable

  def to_influxdb_line_protocols(self) -> list[str]:
    return [point.to_line_protocol() for point in self.to_influxdb_points()]
