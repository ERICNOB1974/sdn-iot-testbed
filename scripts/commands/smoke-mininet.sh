#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Probando Mininet + Open vSwitch..."

"${COMPOSE[@]}" run --rm \
  mininet \
  mn --switch ovsbr --test pingall