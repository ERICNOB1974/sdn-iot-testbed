#!/bin/bash

source "$(dirname "$0")/../common.sh"

SERVICE="$1"

if [ -z "$SERVICE" ]; then

  echo "Construyendo todo el banco de pruebas..."

  "${COMPOSE[@]}" build

else

  echo "Construyendo servicio $SERVICE..."

  "${COMPOSE[@]}" build "$SERVICE"

fi