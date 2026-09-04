#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/../common.sh"

SERVICE="${1:-}"

if [ -z "$SERVICE" ]; then

  echo "Reconstruyendo todo sin cache..."

  "${COMPOSE[@]}" build --no-cache

else

  echo "Reconstruyendo servicio $SERVICE sin cache..."

  "${COMPOSE[@]}" build --no-cache "$SERVICE"

fi