# Topologías

Las topologías definen la red que será emulada por Mininet durante un experimento.

En el testbed, una topología puede estar formada por:

```text
1. Switches
2. Hosts
3. Enlaces
4. Placement de hosts, si corresponde
```

La topología final que se ejecuta puede venir directamente de un archivo YAML o puede construirse combinando una topología base con un archivo de placement.

## Ubicación

Las topologías internas del testbed están en:

```text
topologies/definitions/
```

Ejemplos:

```text
topologies/definitions/diamond.yaml
topologies/definitions/iinet.yaml
topologies/definitions/goodnet.yaml
```

Los placements de hosts están en:

```text
topologies/placements/
```

Ejemplos:

```text
topologies/placements/iinet_4_hosts.yaml
topologies/placements/goodnet_4_hosts.yaml
```

Los archivos GraphML originales, cuando se usan topologías de Topology Zoo, están en:

```text
topologies/topology_zoo/
```

## Uso dentro de un experimento

Un experimento referencia la topología en el bloque topology.

Ejemplo:

```yaml
topology:
  definition: topologies/definitions/goodnet.yaml
  placement: topologies/placements/goodnet_4_hosts.yaml
```

Campos principales:

```text
definition: archivo YAML con la topología base
placement: archivo YAML que indica dónde conectar hosts
```

El campo placement puede ser opcional si la topología ya define los hosts directamente.

## Topología base

Una topología base define los nodos y enlaces principales de la red.

Ejemplo mínimo:

```yaml
name: my-topology

hosts: []

switches:
  - name: s1
    dpid: "0000000000000001"

  - name: s2
    dpid: "0000000000000002"

links:
  - id: s1-s2
    source: s1
    destination: s2
```

En este ejemplo, la topología sólo tiene switches y enlaces entre switches. Los hosts pueden agregarse después mediante un placement.

## Switches

Cada switch debe tener un nombre y un DPID.

Ejemplo:

```yaml
switches:
  - name: s1
    dpid: "0000000000000001"
```

El nombre se usa dentro de los archivos YAML del testbed.

El DPID identifica al switch en OpenFlow.

## Hosts

Los hosts pueden estar definidos directamente en la topología o agregarse mediante un placement.

Ejemplo de host definido directamente:

```yaml
hosts:
  - name: h1
```

Cuando los hosts se agregan mediante placement, la topología base puede dejar la lista vacía:

```yaml
hosts: []
```

Luego el sistema asigna las identidades necesarias, como IP y MAC, durante la ejecución.

## Enlaces

Los enlaces conectan nodos de la topología.

Ejemplo:

```yaml
links:
  - id: s1-s2
    source: s1
    destination: s2
```

Campos principales:

```text
id: identificador del enlace. Se usa la convención "origen-destino"
source: nodo origen del enlace
destination: nodo destino del enlace
```

El id del enlace es importante porque se usa para relacionar la topología con el perfil de red.

Por ejemplo, si la topología tiene:

```yaml
links:
  - id: s1-s2
    source: s1
    destination: s2
```

el perfil de red debe usar ese mismo id para definir el tráfico específico:

```yaml
links:
  s1-s2:
    delay_ms: 5
    bandwidth_mbps: 100
    loss_percent: 0
    routing_cost: 10
```

## Placement de hosts

Un placement indica dónde conectar hosts sobre una topología base.

Se usa principalmente cuando la topología original representa sólo la red de switches, como pasa con las topologías importadas desde Topology Zoo.

Ejemplo:

```yaml
name: goodnet-4-hosts

hosts:
  - name: h1
    switch: s1

  - name: h2
    switch: s4

  - name: h3
    switch: s7

  - name: h4
    switch: s10
```

Esto significa:

```text
h1 se conecta al switch s1
h2 se conecta al switch s4
h3 se conecta al switch s7
h4 se conecta al switch s10
```

## Topology Zoo

Los archivos originales de Topology Zoo se guardan en:

```text
topologies/topology_zoo/
```

Ejemplo:

```text
topologies/topology_zoo/Iinet.graphml
```

Estos archivos no se ejecutan directamente en Mininet. Primero deben convertirse al formato YAML interno del testbed.

Para ver el uso del importador:

```bash
python3 tools/topology_zoo_importer.py --help
```

El resultado esperado es un archivo en:

```text
topologies/definitions/
```

Ejemplo:

```text
topologies/definitions/iinet.yaml
```

Después de importar la topología, se debe crear un placement para agregar hosts.

## `internal_only`

Cuando se importa una topología desde GraphML, puede usarse `internal_only` para filtrar nodos.

```text
internal_only = 1
```

significa que el importador debe quedarse sólo con los nodos marcados como internos en el archivo GraphML.

## Validaciones realizadas

Verifica que existan las secciones principales, que los switches tengan nombre y DPID, que no haya nombres duplicados, que no haya DPIDs duplicados, que los enlaces tengan id, source y destination, que los enlaces apunten a nodos existentes, que un enlace no conecte un nodo consigo mismo, que no haya IDs de enlaces duplicados y que el placement use switches válidos

Si alguna validación falla, el experimento no continúa.

## Convención recomendada

Para topologías:

```text
topologies/definitions/<nombre>.yaml
```

Ejemplos:

```text
diamond.yaml
iinet.yaml
goodnet.yaml
```

Para placements:

```text
topologies/placements/nombreTopologia_numeroCantidad_hosts.yaml
```

Ejemplos:

```text
iinet_4_hosts.yaml
goodnet_4_hosts.yaml
```

Para archivos GraphML originales:

```text
topologies/topology_zoo/Nombre.graphml
```

Ejemplos:

```text
Iinet.graphml
Goodnet.graphml
Unpsjb_pm.graphml
```