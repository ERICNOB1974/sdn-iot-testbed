#!/bin/sh

set -eu

exec ryu-manager \
  --default-log-level=20 \
  --ofp-tcp-listen-port "${CONTROLLER_PORT}" \
  --observe-links \
  "${CONTROLLER_APP}"