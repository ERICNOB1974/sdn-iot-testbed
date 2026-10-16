# Tráfico

El tráfico define las comunicaciones que se van a generar durante un experimento.

En el testbed, la configuración de tráfico tiene dos partes principales:

```text
1. Perfil de tráfico
2. Generador de tráfico
```

El perfil describe qué tráfico se quiere generar. El generador indica qué código Python se encarga de ejecutarlo dentro de Mininet.

## Ubicación

Los perfiles de tráfico están en:

```text
traffic/profiles/
```

Ejemplos:

```text
traffic/profiles/ping_iinet.yaml
traffic/profiles/ping_goodnet.yaml
traffic/profiles/ditg_test.yaml
traffic/profiles/ditg_multi.yaml
traffic/profiles/ditg_congestion.yaml
```

Los generadores de tráfico están en:

```text
traffic/generators/
```

Ejemplos:

```text
traffic/generators/ping.py
traffic/generators/ditg.py
```

## Uso dentro de un experimento

Un experimento referencia el tráfico en el bloque `traffic`.

Ejemplo con D-ITG:

```yaml
traffic:
  profile: traffic/profiles/ditg_multi.yaml
  generator:
    module: traffic.generators.ditg
    function: run_ditg
```

Campos principales:

```text
profile: archivo YAML que define los flujos de tráfico
generator: módulo y función Python que ejecutan ese tráfico
```

Esto permite reutilizar el mismo perfil de tráfico con distintos experimentos, o cambiar el generador sin modificar la topología ni el algoritmo.

## Perfil de tráfico

Un perfil de tráfico define los flujos que se van a generar.

La estructura general es:

```yaml
type: tipo_de_trafico

flows:
  - id: flow-1
    source: h1
    destination: h2
```

Campos principales:

```text
type: tipo de tráfico del perfil
flows: lista de flujos a ejecutar
id: identificador del flujo
source: host origen
destination: host destino
```

Los hosts indicados en source y destination deben existir en la topología final del experimento.

## Generador de tráfico

El generador es el código que toma el perfil de tráfico y lo ejecuta sobre la red Mininet.

El experimento indica explícitamente qué generador debe usar:

```yaml
traffic:
  profile: traffic/profiles/ping_test.yaml
  generator:
    module: traffic.generators.ping
    function: run_ping
```

o:

```yaml
traffic:
  profile: traffic/profiles/ditg_test.yaml
  generator:
    module: traffic.generators.ditg
    function: run_ditg
```

## Tráfico con ping

El tráfico `ping` se usa para pruebas simples de conectividad y pérdida básica.

Ejemplo:

```yaml
type: ping

flows:
  - id: ping-1
    source: h1
    destination: h2
    count: 5
    interval: 0.2
```

En este caso:

```text
h1 envía paquetes ICMP hacia h2
count indica la cantidad de paquetes
interval indica el intervalo entre paquetes en segundos
```

Para usar este perfil en un experimento:

```yaml
traffic:
  profile: traffic/profiles/ping_test.yaml
  generator:
    module: traffic.generators.ping
    function: run_ping
```

## Tráfico con D-ITG

D-ITG permite generar tráfico más configurable que ping.

Puede definir parámetros como protocolo, puertos, tamaño de paquete, tasa y duración.

Ejemplo:

```yaml
type: ditg

flows:
  - id: ditg-1
    source: h1
    destination: h2
    traffic:
      ip_protocol: 17
      source_port: 5001
      destination_port: 6001
      packet_size_bytes: 512
      rate_pps: 200
      duration_seconds: 30
      start_seconds: 0
      seed: 1
```

Campos principales dentro de traffic:

```text
ip_protocol: protocolo IP usado por el flujo
source_port: puerto origen
destination_port: puerto destino
packet_size_bytes: tamaño de cada paquete
rate_pps: tasa de envío en paquetes por segundo
duration_seconds: duración del flujo
start_seconds: instante de inicio relativo
seed: semilla usada por el generador
```

En este ejemplo, el flujo envía aproximadamente:

```text
rate_pps * duration_seconds
```

Por ejemplo:

```text
200 paquetes por segundo × 30 segundos = 6000 paquetes
```

Para usar D-ITG en un experimento:

```yaml
traffic:
  profile: traffic/profiles/ditg_multi.yaml
  generator:
    module: traffic.generators.ditg
    function: run_ditg
```

## Flujos de tráfico

Un flujo no representa un único paquete.

Un flujo representa una comunicación identificable entre un origen y un destino.

Por ejemplo:

```yaml
- id: flow-1
  source: h1
  destination: h2
  traffic:
    ip_protocol: 17
    source_port: 5001
    destination_port: 6001
    packet_size_bytes: 512
    rate_pps: 200
    duration_seconds: 30
```

Ese flujo puede generar muchos paquetes durante el experimento.

En D-ITG, la cantidad de paquetes depende de:

```text
rate_pps * duration_seconds
```

En ping, la cantidad de paquetes depende de:

```text
count
```

## Flujos múltiples

Un perfil puede definir más de un flujo.

Ejemplo:

```yaml
flows:
  - id: flow-1
    source: h1
    destination: h2
    traffic:
      ip_protocol: 17
      source_port: 5001
      destination_port: 6001
      packet_size_bytes: 512
      rate_pps: 100
      duration_seconds: 20

  - id: flow-2
    source: h3
    destination: h4
    traffic:
      ip_protocol: 17
      source_port: 5002
      destination_port: 6002
      packet_size_bytes: 512
      rate_pps: 100
      duration_seconds: 20
```

Esto permite generar tráfico simultáneo o escalonado entre distintos hosts.

## Especificaciones solapadas

En perfiles D-ITG, los flujos no deben tener especificaciones solapadas.

Esto significa que dos flujos no deben poder coincidir con los mismos paquetes.

Ejemplo problemático:

```yaml
flows:
  - id: flow-1
    source: h1
    destination: h2
    traffic:
      ip_protocol: 17
      destination_port: 6001

  - id: flow-2
    source: h1
    destination: h2
    traffic:
      ip_protocol: 17
      destination_port: 6001
```

Ambos flujos describen tráfico de h1 a h2 usando UDP hacia el puerto 6001.

Cuando llegue un paquete real, el controlador no podría distinguir si corresponde a `flow-1` o a `flow-2`.

Si se quiere enviar más tráfico, no se debe duplicar el mismo flujo. Se puede aumentar rate_pps, aumentar duration_seconds o crear otro flujo con puertos distintos.

Ejemplo correcto:

```yaml
flows:
  - id: flow-1
    source: h1
    destination: h2
    traffic:
      ip_protocol: 17
      source_port: 5001
      destination_port: 6001
      packet_size_bytes: 512
      rate_pps: 200
      duration_seconds: 30

  - id: flow-2
    source: h1
    destination: h2
    traffic:
      ip_protocol: 17
      source_port: 5002
      destination_port: 6002
      packet_size_bytes: 512
      rate_pps: 200
      duration_seconds: 30
```

## Qué ocurre durante la ejecución

Cuando se ejecuta un experimento, el sistema lee el perfil de tráfico indicado en traffic.profile, carga el generador indicado en traffic.generator, ejecuta los flujos sobre los hosts de Mininet, el tráfico va a generar paquetes dentro de la red emulada, los switches Open vSwitch van a reenviar los paquetes o consultar al controlador, el controlador calcula las rutas e instala reglas OpenFlow cuando corresponde y el resultado del tráfico se guarda en la carpeta del run.

## Validaciones realizadas

Verifica que los hosts referenciados por los flujos existan en la topología final, que los campos requeridos estén presentes, que los valores numéricos sean válidos y que los flujos no tengan especificaciones solapadas cuando corresponde.

Si alguna validación falla, el experimento no continúa.

## Convención recomendada

Para perfiles de tráfico:

```text
traffic/profiles/tipoEscenario_nombreEscenario.yaml
```

Ejemplos:

```text
ping_test.yaml
ping_iinet.yaml
ping_goodnet.yaml
ping_multi.yaml
ditg_test.yaml
ditg_multi.yaml
ditg_congestion.yaml
```

Para generadores:

```text
traffic/generators/nombreGenerador.py
```

Ejemplos:

```text
ping.py
ditg.py
```