import re
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from typing import Callable, Self

from influxdb_client import Point
from influxdb_client.domain.write_precision import WritePrecision

_MQTT_PAYLOAD_REGEX = r"'([lrabc0-9]{1,3})_(\w+)[^\d-]*(-?\d+\.\d+) (\S+)"
_MQTT_PAYLOAD_PATTERN = re.compile(_MQTT_PAYLOAD_REGEX)


@unique
class InputId(StrEnum):
  LEFT = 'l'
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
  RIGHT = 'r'
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

  @classmethod
  def device_ids(cls) -> list[Self]:
    return [cls(device) for device in 'lr']

  @classmethod
  def phase_ids(cls) -> list[Self]:
    return [cls(device + phase) for device in 'lr' for phase in 'abc']

  @classmethod
  def circuit_ids(cls) -> list[Self]:
    return [cls(device + str(circuit + 1)) for device in 'lr' for circuit in range(0, 16)]


@unique
class Measurement(StrEnum):
  DEBUG_BLOCK = 'debug_block'
  DEBUG_FREE = 'debug_free'
  DEBUG_LOOP_TIME = 'debug_loop_time'
  FREQUENCY = 'frequency'
  PHASE_ANGLE = 'phase_angle'
  POWER = 'power'
  UPTIME = 'uptime'
  VOLTAGE = 'voltage'
  WIFI_SIGNAL = 'wifi_signal'


@unique
class ValueUnit(StrEnum):
  BYTES = 'B'
  DECIBEL_MILLIWATT = 'dBm'
  DEGREE = '°'
  DEGREE_1000X = 'degree_1000x'
  HERTZ = 'Hz'
  MILLIHERTZ = 'mHz'
  MILLISECOND = 'ms'
  MILLIVOLT = 'mV'
  MILLIWATT = 'mW'
  SECOND = 's'
  VOLT = 'V'
  WATT = 'W'


@dataclass
class MeasurementInvariant:
  expected_input_ids: list[InputId]
  expected_input_unit: ValueUnit
  unit_converter: Callable[[Decimal], int]
  output_unit: ValueUnit


MEASUREMENT_INVARIANTS: dict[Measurement, MeasurementInvariant] = {
    Measurement.DEBUG_BLOCK:
    MeasurementInvariant(expected_input_ids=InputId.device_ids(),
                         expected_input_unit=ValueUnit.BYTES,
                         unit_converter=lambda v: int(v),
                         output_unit=ValueUnit.BYTES),
    Measurement.DEBUG_FREE:
    MeasurementInvariant(expected_input_ids=InputId.device_ids(),
                         expected_input_unit=ValueUnit.BYTES,
                         unit_converter=lambda v: int(v),
                         output_unit=ValueUnit.BYTES),
    Measurement.DEBUG_LOOP_TIME:
    MeasurementInvariant(expected_input_ids=InputId.device_ids(),
                         expected_input_unit=ValueUnit.MILLISECOND,
                         unit_converter=lambda v: int(v),
                         output_unit=ValueUnit.MILLISECOND),
    Measurement.FREQUENCY:
    MeasurementInvariant(expected_input_ids=InputId.phase_ids(),
                         expected_input_unit=ValueUnit.HERTZ,
                         unit_converter=lambda v: int(v * 1000),
                         output_unit=ValueUnit.MILLIHERTZ),
    Measurement.PHASE_ANGLE:
    MeasurementInvariant(expected_input_ids=InputId.phase_ids(),
                         expected_input_unit=ValueUnit.DEGREE,
                         unit_converter=lambda v: int(v * 1000),
                         output_unit=ValueUnit.DEGREE_1000X),
    Measurement.POWER:
    MeasurementInvariant(expected_input_ids=InputId.phase_ids() + InputId.circuit_ids(),
                         expected_input_unit=ValueUnit.WATT,
                         unit_converter=lambda v: int(v * 1000),
                         output_unit=ValueUnit.MILLIWATT),
    Measurement.UPTIME:
    MeasurementInvariant(expected_input_ids=InputId.device_ids(),
                         expected_input_unit=ValueUnit.SECOND,
                         unit_converter=lambda v: int(v * 1000),
                         output_unit=ValueUnit.MILLISECOND),
    Measurement.VOLTAGE:
    MeasurementInvariant(expected_input_ids=InputId.phase_ids(),
                         expected_input_unit=ValueUnit.VOLT,
                         unit_converter=lambda v: int(v * 1000),
                         output_unit=ValueUnit.MILLIVOLT),
    Measurement.WIFI_SIGNAL:
    MeasurementInvariant(expected_input_ids=InputId.device_ids(),
                         expected_input_unit=ValueUnit.DECIBEL_MILLIWATT,
                         unit_converter=lambda v: int(v),
                         output_unit=ValueUnit.DECIBEL_MILLIWATT),
}


@dataclass
class EmporiaVueRecord:
  timestamp_ns: int
  input_id: InputId
  measurement: Measurement
  input_value: Decimal

  @classmethod
  def from_log_message(cls, timestamp_ns: int, log_message: str) -> Self | None:
    match = _MQTT_PAYLOAD_PATTERN.search(log_message)
    if match is None:
      return None

    groups = match.groups()

    try:
      input_id = InputId(groups[0])
      measurement = Measurement(groups[1])
      input_value = Decimal(groups[2])
      input_unit = ValueUnit(groups[3])
    except ValueError:
      return None

    try:
      assert input_id in MEASUREMENT_INVARIANTS[measurement].expected_input_ids
      assert input_unit == MEASUREMENT_INVARIANTS[measurement].expected_input_unit
    except AssertionError:
      return None

    return cls(timestamp_ns=timestamp_ns,
               input_id=input_id,
               measurement=measurement,
               input_value=input_value)

  def to_influxdb_point(self) -> Point:
    output_value = MEASUREMENT_INVARIANTS[self.measurement].unit_converter(self.input_value)
    output_unit = MEASUREMENT_INVARIANTS[self.measurement].output_unit

    # yapf: disable
    return (Point
        .measurement(self.measurement)
        .tag('input_id', self.input_id)
        .field(f'{self.measurement}_{output_unit}', output_value)
        .time(self.timestamp_ns, write_precision=WritePrecision.NS))  # type: ignore
    # yapf: enable

  def to_influxdb_line_protocol(self) -> str:
    return self.to_influxdb_point().to_line_protocol()
