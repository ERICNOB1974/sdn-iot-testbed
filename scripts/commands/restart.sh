#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Reiniciando banco de pruebas..."

"${COMPOSE[@]}" down
"${COMPOSE[@]}" up -d