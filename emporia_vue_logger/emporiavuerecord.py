import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Self

from influxdb_client import Point
from influxdb_client.domain.write_precision import WritePrecision

# Tested on https://regex101.com with 123 strings.
# r"'(?:phase|circuit)_([lrab0-9]+)_(voltage|power)': Sending state (-?\d+\.\d+) [VW] with \d+ decimals of accuracy"  # 9528 steps.
# r"'(?:phase|circuit)_([lrab0-9]{2,3})_(voltage|power).{17}(-?\d+\.\d+)"  # 3870 steps.
# r"_([lrab0-9]{2,3})_(voltage|power).{17}(-?\d+\.\d+)"  # 2595 steps.
# r"_([lrab0-9]{2,3})_[^\d-]*(-?\d+\.\d+) (V|W)"  # 2202 steps.
_MQTT_PAYLOAD_REGEX = r"_([ablr0-9]{2,3})_[^\d-]*(-?\d+\.\d+) ([VW])"  # 2091 steps.
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


class ValueUnit(StrEnum):
  VOLTAGE_V = 'V'
  POWER_W = 'W'


@dataclass
class EmporiaVueRecord:
  timestamp_ns: int
  input_id: InputId
  value: Decimal
  value_unit: ValueUnit

  @classmethod
  def from_mqtt_payload(cls, timestamp_ns: int, mqtt_payload: str) -> Self | None:
    match = _MQTT_PAYLOAD_PATTERN.search(mqtt_payload)
    if match is None:
      return None

    groups = match.groups()

    return cls(
        timestamp_ns=timestamp_ns,
        input_id=InputId(groups[0]),
        value=Decimal(groups[1]),
        value_unit=ValueUnit(groups[2]),
    )

  def to_influxdb_points(self) -> list[Point]:
    if self.value_unit == ValueUnit.POWER_W:
      # yapf: disable
      return  [
          Point
              .measurement('power')
              .tag('input_id', self.input_id)
              .field('power_mw', int(self.value * 1000))
              .time(self.timestamp_ns, write_precision=WritePrecision.NS)
      ]
      # yapf: enable

    if self.value_unit == ValueUnit.VOLTAGE_V:
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
