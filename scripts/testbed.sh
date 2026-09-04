#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/common.sh"

COMMAND="${1:-}"

show_help() {

  echo "Uso:"
  echo
  echo "  $0 build [servicio]"
  echo "  $0 rebuild [servicio]"
  echo "  $0 up"
  echo "  $0 down"
  echo "  $0 restart"
  echo "  $0 config"
  echo "  $0 env"
  echo "  $0 sh <servicio>"
  echo "  $0 smoke-mininet"
  echo "  $0 smoke-controller"
  echo "  $0 controller"
  echo "  $0 mininet"
  echo "  $0 clean"
  echo "  $0 experiment <id>"
  echo "  $0 analyze <id>"
}


if [ -z "$COMMAND" ]; then

  show_help

  exit 1

fi


COMMAND_FILE="$ROOT_DIR/scripts/commands/$COMMAND.sh"


if [ ! -f "$COMMAND_FILE" ]; then

  echo "Comando desconocido: $COMMAND"

  echo

  show_help

  exit 1

fi


shift

exec "$COMMAND_FILE" "$@"