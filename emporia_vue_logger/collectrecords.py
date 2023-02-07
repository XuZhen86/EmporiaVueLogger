import asyncio
import time
from queue import Empty, Queue

from absl import app, flags
from aioesphomeapi import LogLevel
from aioesphomeapi.api_pb2 import SubscribeLogsResponse
from aioesphomeapi.client import APIClient
from aioesphomeapi.reconnect_logic import ReconnectLogic
from line_protocol_cache.asyncproducer import AsyncLineProtocolCacheProducer
from zeroconf.asyncio import AsyncZeroconf

from emporia_vue_logger.emporiavuelog import EmporiaVueLog
from emporia_vue_logger.emporiavuerecord import EmporiaVueRecord

_ESPHOME_ADDRESS = flags.DEFINE_string(
    name='esphome_address',
    default=None,
    required=True,
    help='The address to connect to; for example an IP address or .local name for mDNS lookup.',
)

_ESPHOME_PORT = flags.DEFINE_integer(
    name='esphome_port',
    default=6053,
    help='The port to connect to.',
)

_ESPHOME_PASSWORD = flags.DEFINE_string(
    name='esphome_password',
    default='',
    help='Optional password to send to the device for authentication',
)

_ESPHOME_NOISE_PSK = flags.DEFINE_string(
    name='esphome_noise_psk',
    default=None,
    required=True,
    help='Encryption preshared key for noise transport encrypted sessions.',
)


def on_log(response: SubscribeLogsResponse, device_name: str,
           line_protocol_queue: Queue[str]) -> None:
  timestamp_ns = time.time_ns()

  try:
    message = response.message.decode('utf-8')  # type: ignore
  except:
    return

  if (record := EmporiaVueRecord.from_log_message(timestamp_ns, message)) is not None:
    line_protocol_queue.put(record.to_influxdb_line_protocol())
    return

  log = EmporiaVueLog.from_log_message(timestamp_ns, message, device_name)
  line_protocol_queue.put(log.to_influxdb_line_protocol())


async def on_connect(api_client: APIClient, line_protocol_queue: Queue[str]) -> None:
  try:
    device_info = await api_client.device_info()
    await api_client.subscribe_logs(
        on_log=lambda r: on_log(r, device_info.name, line_protocol_queue),
        log_level=LogLevel.LOG_LEVEL_DEBUG,
        dump_config=True)
  except:
    await api_client.disconnect()


async def on_disconnect() -> None:
  pass


# Adapted from:
# https://github.com/esphome/esphome/blob/e847766514957f6ceb81de0b678399918ed532a2/esphome/components/api/client.py#L16
async def collect_records(args: list[str]) -> None:
  api_client = APIClient(address=_ESPHOME_ADDRESS.value,
                         port=_ESPHOME_PORT.value,
                         password=_ESPHOME_PASSWORD.value,
                         noise_psk=_ESPHOME_NOISE_PSK.value)

  async with AsyncZeroconf() as async_zeroconf, AsyncLineProtocolCacheProducer() as producer:
    line_protocol_queue: Queue[str] = Queue()

    reconnect_logic = ReconnectLogic(client=api_client,
                                     on_connect=lambda: on_connect(api_client, line_protocol_queue),
                                     on_disconnect=on_disconnect,
                                     zeroconf_instance=async_zeroconf.zeroconf)
    await reconnect_logic.start()

    line_protocols: list[str] = []
    while True:
      try:
        line_protocols.append(line_protocol_queue.get(block=False))
      except Empty:
        await producer.put(line_protocols)
        line_protocols.clear()
        await asyncio.sleep(2)


def main() -> None:
  app.run(lambda args: asyncio.run(collect_records(args), debug=True))
