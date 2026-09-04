#!/bin/bash

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

COMPOSE_FILE="$ROOT_DIR/docker/docker-compose.yaml"

COMPOSE=(docker compose --project-directory "$ROOT_DIR" -f "$COMPOSE_FILE")

cd "$ROOT_DIR"