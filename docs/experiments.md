# Experimentos

Un experimento define qué escenario se va a ejecutar dentro del testbed.

Cada experimento tiene cuatro componentes principales:

```text
1. Topología
2. Perfil de red
3. Perfil de tráfico
4. Algoritmo de ruteo
```

El sistema toma esos componentes, genera una configuración final del run y luego ejecuta la red Mininet con Open vSwitch y el controlador SDN configurado.

## Ubicación de los experimentos

Los experimentos se definen en:

```text
experiments/configs/
```

La convención recomendada es:

```text
experiments/configs/expXXX_nombreAlgoritmoDeRuteo_nombreTopologia_nombreTrafico.yaml
```

Ejemplo:

```text
exp001_dijkstra_diamond.yaml
exp008_dijkstra_iinet.yaml
exp010_dijkstra_goodnet_ditg.yaml
```

## Ejecutar un experimento

Para ejecutar un experimento existente:

```bash
./scripts/testbed.sh experiment expXXX
```

Donde XXX es el número del experimento.

Por ejemplo, para ejecutar:

```text
experiments/configs/exp008_dijkstra_iinet.yaml
```

se usa:

```bash
./scripts/testbed.sh experiment exp008
```

## Qué hace el sistema al ejecutar

Cuando se ejecuta un experimento, el testbed realiza este flujo:

```text
1. Lee el archivo del experimento.
2. Carga la topología, el perfil de red, el tráfico y el algoritmo.
3. Usa el placement de hosts, si corresponde.
4. Valida que todos los archivos sean consistentes.
5. Genera resolved_config.yaml.
6. Levanta el controlador SDN.
7. Levanta la red emulada en Mininet.
8. Ejecuta el tráfico configurado.
9. Registra decisiones de ruteo y métricas de red.
10. Guarda los resultados del run.
```

## Resultado de una ejecución

Cada ejecución crea una nueva carpeta dentro de `results/`.

Ejemplo:

```text
results/exp008/run-001/
results/exp008/run-002/
results/exp008/run-003/
```

Los archivos principales son:

```text
resolved_config.yaml: configuración final usada por el run
controller.log: log del controlador
routing_decisions.jsonl: decisiones de ruteo tomadas
network_state.jsonl: métricas dinámicas de red
flows.txt: reglas OpenFlow instaladas
ping.txt / salida D-ITG: resultado del tráfico
metadata.json: metadatos del run
```

## Crear un experimento nuevo

Para crear un nuevo experimento, se debe agregar un archivo YAML en:

```text
experiments/configs/
```

Ejemplo:

```text
experiments/configs/exp010_dijkstra_goodnet_ditg.yaml
```

Ese archivo puede reutilizar componentes existentes del proyecto:

```text
topologies/definitions/goodnet.yaml
topologies/placements/goodnet_4_hosts.yaml
network/profiles/goodnet_equal.yaml
traffic/profiles/ditg_multi.yaml
controller/routing/dijkstra.py
```

## Ejemplo mínimo

```yaml
experiment:
  id: exp010
  name: dijkstra-goodnet-ditg

routing:
  name: dijkstra
  module: controller.routing.dijkstra
  class: DijkstraRouting
  metric: routing_cost

topology:
  definition: topologies/definitions/goodnet.yaml
  placement: topologies/placements/goodnet_4_hosts.yaml

network:
  profile: network/profiles/goodnet_equal.yaml

traffic:
  profile: traffic/profiles/ditg_multi.yaml
  generator:
    module: traffic.generators.ditg
    function: run_ditg

collectors:
  - name: flows
    module: collectors.flows
    function: collect_flows
```

Luego se ejecuta con:

```bash
./scripts/testbed.sh experiment exp010
```

## Campos principales

### `experiment`

Identifica el experimento.

```yaml
experiment:
  id: exp010
  name: dijkstra-goodnet-ditg
```

El id es el identificador que se va a usar para ejecutar el experimento.

```bash
./scripts/testbed.sh experiment exp010
```

### `routing`

Se define el algoritmo de ruteo que usará el controlador.

```yaml
routing:
  name: dijkstra
  module: controller.routing.dijkstra
  class: DijkstraRouting
  metric: routing_cost
```

Campos principales:

```text
name: nombre del algoritmo
module: módulo Python donde está implementado
class: clase del algoritmo
metric: métrica usada para calcular rutas
```

Ejemplos de algoritmos existentes:

```text
controller/routing/dijkstra.py
controller/routing/round_robin.py
controller/routing/aqra.py
controller/routing/mina.py
controller/routing/sway.py
```

### `topology`

Define la topología que se va a emular.

```yaml
topology:
  definition: topologies/definitions/goodnet.yaml
  placement: topologies/placements/goodnet_4_hosts.yaml
```

La topología base se define en:

```text
topologies/definitions/
```

El placement indica donde conectar hosts sobre esa topología:

```text
topologies/placements/
```

El campo placement puede ser opcional en caso de que la topología ya defina los hosts directamente.

### `network`

Define el perfil de red aplicado sobre los enlaces.

```yaml
network:
  profile: network/profiles/goodnet_equal.yaml
```

Los perfiles de red están en:

```text
network/profiles/
```

Un perfil de red puede definir:

```text
delay_ms
bandwidth_mbps
loss_percent
routing_cost
```

La métrica (metric) indicada en el apartado de routing debe existir en los enlaces usados por el algoritmo.

### `traffic`

Define el tráfico que se va a ejecutar durante el experimento.

```yaml
traffic:
  profile: traffic/profiles/ditg_multi.yaml
  generator:
    module: traffic.generators.ditg
    function: run_ditg
```

Los perfiles de tráfico están en:

```text
traffic/profiles/
```

Los cuales se encargan de indicar el archivo YAML donde están definidos los flujos de tráfico.

Los generadores están en:

```text
traffic/generators/
```

Estos se encargan de indicar qué módulo Python se encarga de ejecutar ese tráfico dentro de Mininet.

### `collectors`

Define los recolectores que se ejecutan al finalizar el tráfico.

```yaml
collectors:
  - name: flows
    module: collectors.flows
    function: collect_flows
```

Actualmente, el collector de flujos permite guardar las reglas OpenFlow instaladas en los switches.

El resultado se guarda en:

```text
flows.txt
```

## Combinar componentes existentes

Para probar una combinación nueva, solo se debe crear un nuevo archivo de configuración de experimento.

Por ejemplo, si se quiere probar:

```text
Topología: Goodnet
Algoritmo: Dijkstra
Tráfico: D-ITG
Perfil de red: goodnet_equal
```

se crea un nuevo YAML en `experiments/configs/` que apunte a esos archivos:

```yaml
topology:
  definition: topologies/definitions/goodnet.yaml
  placement: topologies/placements/goodnet_4_hosts.yaml

network:
  profile: network/profiles/goodnet_equal.yaml

traffic:
  profile: traffic/profiles/ditg_multi.yaml
  generator:
    module: traffic.generators.ditg
    function: run_ditg

routing:
  name: dijkstra
  module: controller.routing.dijkstra
  class: DijkstraRouting
  metric: routing_cost
```

Después se ejecuta con:

```bash
./scripts/testbed.sh experiment exp010
```

## Validaciones realizadas

Antes de ejecutar Mininet, el sistema valida la configuración.

Verifica que la topología exista, que los enlaces referenciados existan, que los hosts del tráfico existan, que el placement use switches válidos, que el perfil de red coincida con la topología, que la métrica de ruteo esté definida, que los flujos no tengan especificaciones solapadas, que el generador de tráfico exista y que el algoritmo de ruteo exista.

Si alguna validación falla, el experimento no se ejecuta.

## Configuración resuelta

El archivo más importante generado automáticamente por el sistema es:

```text
resolved_config.yaml
```

Ubicación:

```text
results/expXXX/run-YYY/resolved_config.yaml
```