# Arquitectura general

La arquitectura del testbed separa la definición del experimento, la ejecución en Mininet, el controlador SDN, la generación de tráfico y la recolección de datos.

## Flujo general

El flujo normal de ejecución es:

```text
1. El usuario ejecuta un experimento.
2. El sistema lee el YAML del experimento.
3. Se cargan la topología, el perfil de red, el tráfico y el algoritmo.
4. Se genera la configuración resuelta del run.
5. Se levanta el controlador SDN.
6. Se levanta Mininet con Open vSwitch.
7. Se ejecuta el tráfico configurado.
8. El controlador decide rutas e instala reglas OpenFlow.
9. Se registran métricas, decisiones y resultados.
10. Los archivos se guardan en results/.
```

## Componentes principales

El proyecto está organizado en módulos con responsabilidades separadas.

```text
analysis/: scripts de análisis posterior
collectors/: recolección de datos al finalizar el experimento
common/: carga, validación y resolución de configuraciones
controller/: controlador SDN, estado de red y algoritmos de ruteo
docs:/: documentación detallada del sistema
docker/: entornos reproducibles para Mininet y controladores
experiments/: archivos YAML que definen experimentos
network/: perfiles de red y configuración de enlaces
results/: resultados generados por cada ejecución
runner/: ejecución del experimento en Mininet
scripts/: comandos principales del testbed
tools/: importadores y herramientas auxiliares
topologies/: topologías, placements y archivos GraphML
traffic/: perfiles y generadores de tráfico
```