#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Configuración Docker Compose resuelta:"

"${COMPOSE[@]}" config