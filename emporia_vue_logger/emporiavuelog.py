from dataclasses import dataclass
from typing import Self

from influxdb_client import Point
from influxdb_client.domain.write_precision import WritePrecision


@dataclass
class EmporiaVueLog:
  timestamp_ns: int
  log_message: str
  device_name: str

  @classmethod
  def from_log_message(cls, timestamp_ns: int, log_message: str, device_name: str) -> Self:
    return cls(timestamp_ns=timestamp_ns, log_message=log_message, device_name=device_name)

  def to_influxdb_point(self) -> Point:
    # yapf: disable
    return (Point
        .measurement('log')
        .tag('device_name', self.device_name)
        .field('log_message', self.log_message)
        .time(self.timestamp_ns, write_precision=WritePrecision.NS))  # type: ignore
    # yapf: enable

  def to_influxdb_line_protocol(self) -> str:
    return self.to_influxdb_point().to_line_protocol()
