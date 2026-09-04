#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Iniciando banco de pruebas..."

"${COMPOSE[@]}" up -d