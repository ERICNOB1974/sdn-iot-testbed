#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Deteniendo banco de pruebas..."

"${COMPOSE[@]}" down