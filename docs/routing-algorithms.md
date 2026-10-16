# Algoritmos de ruteo

Los algoritmos de ruteo definen cómo el controlador SDN decide el camino que debe seguir un flujo dentro de la red emulada.

## Ubicación

Los algoritmos están en:

```text
controller/routing/
```

Ejemplos:

```text
controller/routing/dijkstra.py
controller/routing/round_robin.py
controller/routing/aqra.py
controller/routing/mina.py
controller/routing/sway.py
```

También existen archivos de soporte para definir la estructura común de los algoritmos:

```text
controller/routing/base.py
controller/routing/context.py
controller/routing/decision.py
```

## Uso dentro de un experimento

Un experimento referencia el algoritmo de ruteo en el bloque routing.

Ejemplo:

```yaml
routing:
  name: dijkstra
  module: controller.routing.dijkstra
  class: DijkstraRouting
  metric: routing_cost
```

Campos principales:

```text
name: nombre lógico del algoritmo
module: módulo Python donde está implementado
class: clase del algoritmo
metric: métrica usada para calcular rutas
```

El controlador usa module y class para cargar dinámicamente el algoritmo indicado en el experimento.

## Rol del controlador

El controlador SDN es el encargado de recibir "eventos" de la red y consultar al algoritmo cuando necesita decidir una ruta.

Basicamente, un host genera tráfico, el paquete llega a un switch Open vSwitch, en el caso de que el switch no tenga una regla instalada, envía un PacketIn al controlador, el controlador va a identificar el flujo, determinar el switch origen y el switch destino y construir el contexto de ruteo. Luego, el algoritmo calcula el camino y el controlador instala reglas OpenFlow para ese camino.

El algoritmo sólo participa en el paso donde se calcula el camino.

## Contrato de un algoritmo

Un algoritmo debe implementar una clase que pueda ser usada por el controlador.

La forma esperada es:

```python
from controller.routing.base import RoutingAlgorithm
from controller.routing.decision import RoutingDecision


class MyRouting(RoutingAlgorithm):
    name = "my-routing"

    def compute(self, graph, context):
        path = ...
        cost = ...

        return RoutingDecision(
            path=path,
            cost=cost,
        )
```

El método principal es:

```text
compute(graph, context)
```

Donde:

```text
graph: grafo de la red usado para calcular rutas
context: información del flujo y del estado de red disponible para la decisión
```

El algoritmo debe devolver un objeto RoutingDecision.

## `RoutingDecision`

RoutingDecision representa la decisión tomada por el algoritmo.

La información principal es:

```text
path: camino elegido
cost: costo del camino
```

Ejemplo conceptual:

```text
path = [1, 2, 4]
cost = 10
```

Esto significa que el flujo debe ir por:

```text
s1 → s2 → s4
```

Luego el controlador toma esa decisión y la transforma en reglas OpenFlow para los switches correspondientes.

## Métrica de ruteo

La métrica indicada en el experimento define qué valor se usa como costo para calcular rutas.

Ejemplo:

```yaml
routing:
  name: dijkstra
  module: controller.routing.dijkstra
  class: DijkstraRouting
  metric: routing_cost
```

En este caso, el algoritmo usa routing_cost como costo lógico de los enlaces.

Ese valor debe estar definido en el perfil de red:

```yaml
links:
  s1-s2:
    delay_ms: 5
    bandwidth_mbps: 100
    loss_percent: 0
    routing_cost: 10
```

La métrica de ruteo no tiene que ser igual al retardo real del enlace.

## Dijkstra

El algoritmo Dijkstra calcula el camino de menor costo entre el switch origen y el switch destino.

Ejemplo:

```text
s1 - costo 10 -> s2 - costo 10 -> s4
s1 - costo 50 -> s3 - costo 10 -> s4
```

Para ir de s1 a s4, Dijkstra elige s1 -> s2 -> s4

El costo usado por Dijkstra depende de la métrica indicada en el experimento.

## Algoritmos existentes

El proyecto puede incluir distintos algoritmos dentro de `controller/routing/`.

Ejemplos:

```text
dijkstra.py
round_robin.py
aqra.py
mina.py
sway.py
```

Cada algoritmo debe respetar la misma idea general: recibir el grafo y el contexto, y devolver una decisión de ruteo.

## Crear un nuevo algoritmo

Para crear un nuevo algoritmo, se debe agregar un archivo Python en:

```text
controller/routing/
```

Convención recomendada:

```text
controller/routing/nombre_algoritmo.py
```

Ejemplo:

```text
controller/routing/my_routing.py
```

El archivo debe definir una clase de algoritmo:

```python
from controller.routing.base import RoutingAlgorithm
from controller.routing.decision import RoutingDecision


class MyRouting(RoutingAlgorithm):
    name = "my-routing"

    def compute(self, graph, context):
        path = ...
        cost = ...

        return RoutingDecision(
            path=path,
            cost=cost,
        )
```

Después se referencia desde un experimento:

```yaml
routing:
  name: my-routing
  module: controller.routing.my_routing
  class: MyRouting
  metric: routing_cost
```

## Comparar algoritmos

Para comparar algoritmos, se recomienda mantener constantes los demás componentes del experimento.

Por ejemplo, usar la misma topología, el mismo perfil de red y el mismo tráfico:

```text
Topología: Goodnet
Perfil de red: goodnet_equal
Tráfico: ditg_multi
```

Y cambiar sólo el algoritmo. De esta forma, las diferencias en los resultados se pueden atribuir principalmente al algoritmo de ruteo usado.

## Relación con OpenFlow

El algoritmo no instala reglas OpenFlow directamente.

El algoritmo calcula el path, devuelve RoutingDecision, el controlador recibe la decisión, FlowManager instala reglas OpenFlow, y por último, Open vSwitch reenvía los siguientes paquetes.

## Validaciones realizadas

Antes de ejecutar el experimento, el sistema valida que el bloque routing indique una métrica de ruteo válida y que esa métrica exista en los enlaces switch-switch usados por el algoritmo.

También debe poder cargarse el módulo y la clase indicada en el experimento.

Si la métrica no existe o el algoritmo no puede cargarse, el experimento no continúa.

## Convención recomendada

Para algoritmos:

```text
controller/routing/nombre_algoritmo.py
```

Ejemplos:

```text
dijkstra.py
round_robin.py
aqra.py
mina.py
sway.py
```

Para clases:

```text
NombreAlgoritmoRouting
```

Ejemplo:

```text
DijkstraRouting
```
