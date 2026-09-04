#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Limpiando contenedores del banco..."

"${COMPOSE[@]}" down --remove-orphans