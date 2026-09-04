#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Iniciando controlador..."

"${COMPOSE[@]}" run --rm controller