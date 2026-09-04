#!/bin/bash

source "$(dirname "$0")/../common.sh"

echo "Probando controlador..."

"${COMPOSE[@]}" run --rm \
  --entrypoint /bin/sh \
  controller \
  -c '
    echo "Python:"
    python --version

    echo
    echo "Ryu:"
    ryu-manager --version

    echo
    echo "Dependencias:"
    pip freeze | grep -E "^(ryu|networkx|eventlet)=="
  '