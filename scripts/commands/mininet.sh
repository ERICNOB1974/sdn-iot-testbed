#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Iniciando Mininet..."

"${COMPOSE[@]}" run --rm mininet