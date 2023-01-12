import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Self

from influxdb_client import Point
from influxdb_client.domain.write_precision import WritePrecision

_MQTT_PAYLOAD_REGEX = r"'(?:phase|circuit)_([lrab0-9]+)_(voltage|power)': Sending state (-?\d+\.\d+) [VW] with \d+ decimals of accuracy"
_MQTT_PAYLOAD_PATTERN = re.compile(_MQTT_PAYLOAD_REGEX)


class InputId(StrEnum):
  LEFT_PHASE_A = 'la'
  LEFT_PHASE_B = 'lb'
  LEFT_PHASE_C = 'lc'
  LEFT_CIRCUIT_1 = 'l1'
  LEFT_CIRCUIT_2 = 'l2'
  LEFT_CIRCUIT_3 = 'l3'
  LEFT_CIRCUIT_4 = 'l4'
  LEFT_CIRCUIT_5 = 'l5'
  LEFT_CIRCUIT_6 = 'l6'
  LEFT_CIRCUIT_7 = 'l7'
  LEFT_CIRCUIT_8 = 'l8'
  LEFT_CIRCUIT_9 = 'l9'
  LEFT_CIRCUIT_10 = 'l10'
  LEFT_CIRCUIT_11 = 'l11'
  LEFT_CIRCUIT_12 = 'l12'
  LEFT_CIRCUIT_13 = 'l13'
  LEFT_CIRCUIT_14 = 'l14'
  LEFT_CIRCUIT_15 = 'l15'
  LEFT_CIRCUIT_16 = 'l16'
  RIGHT_PHASE_A = 'ra'
  RIGHT_PHASE_B = 'rb'
  RIGHT_PHASE_C = 'rc'
  RIGHT_CIRCUIT_1 = 'r1'
  RIGHT_CIRCUIT_2 = 'r2'
  RIGHT_CIRCUIT_3 = 'r3'
  RIGHT_CIRCUIT_4 = 'r4'
  RIGHT_CIRCUIT_5 = 'r5'
  RIGHT_CIRCUIT_6 = 'r6'
  RIGHT_CIRCUIT_7 = 'r7'
  RIGHT_CIRCUIT_8 = 'r8'
  RIGHT_CIRCUIT_9 = 'r9'
  RIGHT_CIRCUIT_10 = 'r10'
  RIGHT_CIRCUIT_11 = 'r11'
  RIGHT_CIRCUIT_12 = 'r12'
  RIGHT_CIRCUIT_13 = 'r13'
  RIGHT_CIRCUIT_14 = 'r14'
  RIGHT_CIRCUIT_15 = 'r15'
  RIGHT_CIRCUIT_16 = 'r16'


class ValueType(StrEnum):
  VOLTAGE = 'voltage'
  POWER = 'power'


@dataclass
class EmporiaVueRecord:
  timestamp_ns: int
  input_id: InputId
  value_type: ValueType
  value: Decimal

  @classmethod
  def from_mqtt_payload(cls, timestamp_ns: int, mqtt_payload: str) -> Self | None:
    match = _MQTT_PAYLOAD_PATTERN.search(mqtt_payload)
    if match is None:
      return None

    groups = match.groups()

    return cls(
        timestamp_ns=timestamp_ns,
        input_id=InputId(groups[0]),
        value_type=ValueType(groups[1]),
        value=Decimal(groups[2]),
    )

  def to_influxdb_points(self) -> list[Point]:
    if self.value_type == ValueType.POWER:
      # yapf: disable
      return  [
          Point
              .measurement('power')
              .tag('input_id', self.input_id)
              .field('power_mw', int(self.value * 1000))
              .time(self.timestamp_ns, write_precision=WritePrecision.NS)
      ]
      # yapf: enable

    if self.value_type == ValueType.VOLTAGE:
      # yapf: disable
      return [
          Point
              .measurement('voltage')
              .tag('input_id', self.input_id)
              .field('voltage_mv', int(self.value * 1000))
              .time(self.timestamp_ns, write_precision=WritePrecision.NS)
      ]
      # yapf: enable

    raise NotImplementedError()

  def to_influxdb_line_protocols(self) -> list[str]:
    return [point.to_line_protocol() for point in self.to_influxdb_points()]
