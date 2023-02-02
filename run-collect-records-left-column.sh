#!/bin/bash

OPTIONS=(
  --detach
  --init
  --mount type=volume,src=emporia-vue-logger-data,dst=/app/data
  --name emporia-vue-logger-collect-records-left-column
  --restart unless-stopped
)

IMAGE=emporia-vue-logger

ARGS=(
  emporia-vue-logger-collect-records
  --flagfile=data/collect-records-left-column-flags.txt
  --verbosity=0
)

docker run "${OPTIONS[@]}" ${IMAGE} "${ARGS[@]}"
