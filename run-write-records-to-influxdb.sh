#!/bin/bash

OPTIONS=(
  --detach
  --init
  --mount type=volume,src=emporia-vue-logger-data,dst=/app/data
  --name emporia-vue-logger-write-records-to-influxdb

  # Needed for solving an issue where placing InfluxDB behind a reverse proxy causes
  # "dial tcp 192.168.1.2:8086: connect: network is unreachable".
  --network host

  --restart unless-stopped
)

IMAGE=line-protocol-cache-consumer

ARGS=(
  line-protocol-cache-consumer
  --flagfile=data/line-protocol-cache-consumer-flags.txt
  --verbosity=0
)

docker run "${OPTIONS[@]}" ${IMAGE} "${ARGS[@]}"
