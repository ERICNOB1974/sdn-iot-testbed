# Resultados

Los resultados contienen lo generado por cada ejecución de un experimento.

## Ubicación

Los resultados se guardan en:

```text
results/
```

Cada experimento tiene su propia carpeta:

```text
results/expXXX/
```

Cada ejecución del mismo experimento genera un nuevo run:

```text
results/expXXX/run-YYY/
```

Ejemplo:

```text
results/exp008/run-001/
results/exp008/run-002/
results/exp008/run-003/
```

Esto permite ejecutar el mismo experimento varias veces sin sobrescribir resultados anteriores.

## Archivos principales

Una carpeta de resultados puede contener archivos como:

```text
resolved_config.yaml
controller.log
routing_decisions.jsonl
network_state.jsonl
flows.txt
ping.txt / salida D-ITG
metadata.json
```

Los archivos generados pueden variar según el tipo de tráfico, los collectors configurados y los componentes habilitados durante la ejecución.

## `resolved_config.yaml`

resolved_config.yaml es la configuración final usada durante el run.

Este archivo se genera después unificar: Experimento, topología, placement de hosts (si corresponde), perfil de red, perfil de tráfico, algoritmo de ruteo y collectors.

El controlador y el runner usan esta configuración resuelta para ejecutar el experimento.

## `controller.log`

controller.log tiene la salida del controlador SDN durante la ejecución.

Tiene información sobre conexión de switches, aprendizaje de hosts, descubrimiento de topología, eventos OpenFlow, decisiones de ruteo y errores o advertencias del controlador.

## `routing_decisions.jsonl`

routing_decisions.jsonl guarda las decisiones de ruteo tomadas por el controlador en cada línea del archivo que tiene un objeto JSON independiente.

Cada linea representa una decisión tomada para un flujo.

Ejemplo:

```json
{"timestamp":"2026-09-25T04:55:42.406156+00:00","algorithm":"dijkstra","metric":"routing_cost","source_switch":"s1","destination_switch":"s4","flow":{"source_mac":"00:00:00:00:00:01","destination_mac":"00:00:00:00:00:04","eth_type":2048,"source_ip":"10.0.0.1","destination_ip":"10.0.0.4","ip_protocol":17,"source_port":36716,"destination_port":6003},"decision":{"path":["s1","s2","s4"],"cost":20,"candidates":[],"metadata":{}}}
```

Campos principales:

```text
timestamp: instante en que se registró la decisión
algorithm: algoritmo usado para calcular la ruta
metric: métrica usada por el algoritmo
source_switch: switch origen del flujo
destination_switch: switch destino del flujo
flow: identificación del flujo observado
decision: decisión tomada por el algoritmo
```

## `network_state.jsonl`

network_state.jsonl guarda muestras del estado dinámico de la red durante el experimento.

Incluye métricas asociadas a enlaces o puertos, como:

```text
tx_bps
rx_bps
tx_pps
rx_pps
utilization
residual_bandwidth_mbps
```

Este archivo es útil para analizar cómo cambió el estado de la red durante la ejecución.

## `flows.txt`

flows.txt contiene las reglas OpenFlow instaladas en los switches.

Este archivo es generado por el collector de flujos cuando está configurado en el experimento.

## Resultado del tráfico

El resultado del tráfico depende del generador usado.

### Ping

Cuando se usa el generador de ping, el resultado se guarda como:

```text
ping.txt
```

Este archivo contiene la salida del comando ping, con sus paquetes transmitidos, paquetes recibidos, pérdida y tiempos RTT.

### D-ITG

Cuando se usa D-ITG, el sistema ejecuta el tráfico definido en el perfil correspondiente y procesa la salida del generador.

Los resultados pueden incluir métricas como paquetes recibidos, paquetes perdidos, porcentaje de pérdida, bitrate promedio, packet rate promedio, delay mínimo, delay máximo, delay promedio y jitter promedio

## `metadata.json`

metadata.json tiene información útil del run, como el experimento ejecutado, fecha, link del commit, entre otras cosas.