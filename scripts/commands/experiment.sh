#!/bin/bash

set -euo pipefail

source "$(dirname "$0")/../common.sh"


EXPERIMENT_ID="${1:-}"


if [ -z "$EXPERIMENT_ID" ]; then

  echo "Uso: ./scripts/testbed.sh experiment <id>"

  exit 1

fi


CONFIG_DIR="$ROOT_DIR/experiments/configs"

CONFIG_FILES=("$CONFIG_DIR"/"${EXPERIMENT_ID}"_*.yaml)


if [ ! -e "${CONFIG_FILES[0]}" ]; then

  echo "No se encontro configuracion para el experimento: $EXPERIMENT_ID"

  exit 1

fi


if [ "${#CONFIG_FILES[@]}" -ne 1 ]; then

  echo "Se encontro mas de una configuracion para: $EXPERIMENT_ID"

  printf '%s\n' "${CONFIG_FILES[@]}"

  exit 1

fi


CONFIG_FILE="${CONFIG_FILES[0]}"

CONFIG_CONTAINER="/workspace/experiments/configs/$(basename "$CONFIG_FILE")"


echo "Configuracion encontrada:"
echo "$CONFIG_FILE"


RESULTS_BASE="$ROOT_DIR/results/$EXPERIMENT_ID"

mkdir -p "$RESULTS_BASE"


LAST_RUN=0


for RUN_DIR in "$RESULTS_BASE"/run-*; do

  if [ -d "$RUN_DIR" ]; then

    RUN_NUMBER="${RUN_DIR##*/run-}"

    if [[ "$RUN_NUMBER" =~ ^[0-9]+$ ]]; then

      RUN_VALUE=$((10#$RUN_NUMBER))

      if [ "$RUN_VALUE" -gt "$LAST_RUN" ]; then

        LAST_RUN="$RUN_VALUE"

      fi

    fi

  fi

done


NEXT_RUN=$((LAST_RUN + 1))

RUN_ID=$(printf "run-%03d" "$NEXT_RUN")

RESULTS_DIR="$RESULTS_BASE/$RUN_ID"

mkdir -p "$RESULTS_DIR"


RESOLVED_CONFIG_HOST="$RESULTS_DIR/resolved_config.yaml"

RESOLVED_CONFIG_CONTAINER="/workspace/results/$EXPERIMENT_ID/$RUN_ID/resolved_config.yaml"


START_TIME="$(date -Iseconds)"

GIT_COMMIT="$(git rev-parse HEAD 2>/dev/null || echo unknown)"


echo
echo "Experimento: $EXPERIMENT_ID"
echo "Run: $RUN_ID"
echo "Resultados: $RESULTS_DIR"
echo


query_config() {

  "${COMPOSE[@]}" run --rm \
    -e PYTHONPATH=/workspace \
    --entrypoint python3 \
    mininet \
    -m runner.config_query \
    --config "$CONFIG_CONTAINER" \
    --get "$1"

}


echo "Leyendo configuracion necesaria para iniciar la infraestructura..."


CONTROLLER_ENV="$(query_config environment.controller)"

CONTROLLER_APP="$(query_config controller.app)"

CONTROLLER_PORT="$(query_config controller.port)"


CONTROLLER_VERSION="${CONTROLLER_ENV%-py*}"


OVS_VERSION="$(
  "${COMPOSE[@]}" run --rm \
    --entrypoint ovs-vsctl \
    mininet \
    --version \
    | head -n 1 \
    | awk '{print $4}'
)"


echo
echo "Entorno del controlador: $CONTROLLER_ENV"
echo "Version del controlador: $CONTROLLER_VERSION"
echo "Aplicacion del controlador: $CONTROLLER_APP"
echo "Puerto OpenFlow: $CONTROLLER_PORT"
echo "Open vSwitch: $OVS_VERSION"


echo
echo "Resolviendo configuracion del experimento..."


"${COMPOSE[@]}" run --rm \
  -e PYTHONPATH=/workspace \
  --entrypoint python3 \
  mininet \
  -m runner.config_resolve \
  --config "$CONFIG_CONTAINER" \
  --output "$RESOLVED_CONFIG_CONTAINER"


if [ ! -f "$RESOLVED_CONFIG_HOST" ]; then

  echo
  echo "ERROR: No se genero la configuracion resuelta:"
  echo "$RESOLVED_CONFIG_HOST"

  exit 1

fi


echo
echo "Configuracion resuelta:"
echo "$RESOLVED_CONFIG_HOST"


CONTROLLER_NAME="sdn-iot-controller-$EXPERIMENT_ID"


cleanup() {

  echo
  echo "Guardando log del controlador..."

  docker logs "$CONTROLLER_NAME" > "$RESULTS_DIR/controller.log" 2>&1 || true


  echo "Deteniendo controlador..."

  docker rm -f "$CONTROLLER_NAME" >/dev/null 2>&1 || true

}


trap cleanup EXIT


echo
echo "Eliminando controlador anterior..."

docker rm -f "$CONTROLLER_NAME" >/dev/null 2>&1 || true


echo
echo "Limpiando Mininet..."

"${COMPOSE[@]}" run --rm mininet mn -c


echo
echo "Iniciando controlador..."


CONTROLLER_ENV="$CONTROLLER_ENV" \
"${COMPOSE[@]}" run -d \
  --name "$CONTROLLER_NAME" \
  -e PYTHONPATH=/workspace \
  -e RESOLVED_CONFIG="$RESOLVED_CONFIG_CONTAINER" \
  -e RESULTS_DIR="/workspace/results/$EXPERIMENT_ID/$RUN_ID" \
  -e CONTROLLER_APP="$CONTROLLER_APP" \
  -e CONTROLLER_PORT="$CONTROLLER_PORT" \
  --entrypoint controller-entrypoint \
  controller


echo
echo "Esperando controlador..."


CONTROLLER_READY=0


for ATTEMPT in $(seq 1 20); do

  if ! docker ps --format '{{.Names}}' | grep -q "^${CONTROLLER_NAME}$"; then

    echo
    echo "ERROR: El controlador termino durante el arranque."
    echo

    docker logs "$CONTROLLER_NAME" || true

    exit 1

  fi


  if ss -ltn | grep -q ":${CONTROLLER_PORT}[[:space:]]"; then

    CONTROLLER_READY=1

    break

  fi


  sleep 0.5

done


if [ "$CONTROLLER_READY" -ne 1 ]; then

  echo
  echo "ERROR: El controlador no comenzo a escuchar en el puerto $CONTROLLER_PORT"
  echo

  docker logs "$CONTROLLER_NAME" || true

  exit 1

fi


echo "Controlador listo."


echo
echo "Ejecutando runner..."
echo


"${COMPOSE[@]}" run --rm \
  -e PYTHONPATH=/workspace \
  mininet \
  python3 \
  -m runner.experiment_runner \
  --config "$RESOLVED_CONFIG_CONTAINER" \
  --results-dir "/workspace/results/$EXPERIMENT_ID/$RUN_ID" \
  --run-id "$RUN_ID" \
  --start-time "$START_TIME" \
  --git-commit "$GIT_COMMIT" \
  --controller-version "$CONTROLLER_VERSION" \
  --openvswitch-version "$OVS_VERSION"


echo
echo "Experimento finalizado correctamente."
echo
echo "Resultados disponibles en:"
echo "$RESULTS_DIR"