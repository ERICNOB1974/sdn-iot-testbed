#!/bin/bash

source "$(dirname "$0")/../common.sh"

EXPERIMENT_ID="$1"

if [ -z "$EXPERIMENT_ID" ]; then

  echo "Uso: ./scripts/testbed.sh analyze <id>"

  exit 1

fi

ANALYZER="$ROOT_DIR/analysis/analyze_${EXPERIMENT_ID}.py"

if [ ! -f "$ANALYZER" ]; then

  echo "No existe analizador para: $EXPERIMENT_ID"

  exit 1

fi

python3 "$ANALYZER"