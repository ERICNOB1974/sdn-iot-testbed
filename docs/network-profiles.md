# Perfiles de red

Los perfiles de red definen las condiciones aplicadas sobre los enlaces de una topología durante un experimento.

En el testbed, un perfil de red tiene:

```text
1. Retardo del enlace
2. Ancho de banda
3. Porcentaje de pérdida
4. Costo lógico de ruteo
```

## Ubicación

Los perfiles de red están en:

```text
network/profiles/
```

Ejemplos:

```text
network/profiles/diamond_equal_cost.yaml
network/profiles/iinet_equal.yaml
network/profiles/goodnet_equal.yaml
network/profiles/diamond_multi_congested.yaml
```

## Uso dentro de un experimento

Un experimento referencia el perfil de red en el bloque network.

Ejemplo:

```yaml
network:
  profile: network/profiles/goodnet_equal.yaml
```

El perfil indicado se aplica sobre los enlaces definidos en la topología final del experimento.

## Estructura de un perfil de red

Un perfil de red define condiciones por enlace.

Ejemplo:

```yaml
name: goodnet-equal

links:
  s1-s2:
    delay_ms: 5
    bandwidth_mbps: 100
    loss_percent: 0
    routing_cost: 10

  s2-s3:
    delay_ms: 5
    bandwidth_mbps: 100
    loss_percent: 0
    routing_cost: 10
```

Cada clave dentro de links debe coincidir con el id de un enlace definido en la topología.

## Campos principales

### `delay_ms`

Define el retardo emulado del enlace en milisegundos.

Ejemplo:

```yaml
delay_ms: 5
```

### `bandwidth_mbps`

Define el ancho de banda emulado del enlace en Mbps.

Ejemplo:

```yaml
bandwidth_mbps: 100
```

Este valor permite calcular métricas como utilización y ancho de banda residual.

### `loss_percent`

Define el porcentaje de pérdida emulada del enlace.

Ejemplo:

```yaml
loss_percent: 0
```

El valor debe estar entre `0` y `100`.

### `routing_cost`

Define el costo del enlace para el algoritmo de ruteo.

Ejemplo:

```yaml
routing_cost: 10
```

Este valor no representa necesariamente el retardo real del enlace. Es una métrica usada por el controlador para decidir caminos.

Por ejemplo, si el experimento usa:

```yaml
routing:
  name: dijkstra
  module: controller.routing.dijkstra
  class: DijkstraRouting
  metric: routing_cost
```

entonces el algoritmo utiliza routing_cost para calcular el camino de menor costo.

## Crear un nuevo perfil de red

Para crear un nuevo perfil, agregar un archivo YAML en:

```text
network/profiles/
```

Convención recomendada:

```text
network/profiles/nombreTopologia_nombrePerfil.yaml
```

Ejemplos:

```text
goodnet_equal.yaml
iinet_equal.yaml
diamond_multi_congested.yaml
```

Ejemplo de perfil nuevo:

```yaml
name: my-network-profile

links:
  s1-s2:
    delay_ms: 5
    bandwidth_mbps: 100
    loss_percent: 0
    routing_cost: 10

  s2-s3:
    delay_ms: 10
    bandwidth_mbps: 50
    loss_percent: 0
    routing_cost: 20
```

Luego se referencia desde un experimento:

```yaml
network:
  profile: network/profiles/my-network-profile.yaml
```

## Combinar perfiles existentes

Para probar la misma topología con distintas condiciones de red, se pueden crear varios perfiles para la misma topología.

Ejemplo:

```text
network/profiles/diamond_equal_cost.yaml
network/profiles/diamond_low_delay.yaml
network/profiles/diamond_multi_congested.yaml
```

Después, el experimento es el que decide cuál usar:

```yaml
network:
  profile: network/profiles/diamond_multi_congested.yaml
```

Esto permite comparar el comportamiento de los algoritmos bajo diferentes escenarios de red sin modificar la topología base.

## Validaciones realizadas

Verifica que el perfil de red tenga formato válido, la sección links sea un mapping, los enlaces referenciados existan en la topología, delay_ms sea un número válido, bandwidth_mbps sea un número positivo, loss_percent esté entre 0 y 100, y que la métrica indicada en el apartado de routing (metric) exista en los enlaces switch-switch usados por el algoritmo.

Si alguna validación falla, el experimento no continúa.