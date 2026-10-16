# Controladores

Los controladores SDN ejecutan el plano de control del testbed.

Su función principal es recibir eventos de la red emulada, decidir rutas e instalar reglas OpenFlow en los switches Open vSwitch.

## Ubicación

Los entornos Docker de controladores están en:

```text
docker/controllers/
```

Ejemplo actual:

```text
docker/controllers/ryu-4.34-py38/
```

La aplicación principal del controlador está en:

```text
controller/routing_controller.py
```

Los algoritmos de ruteo usados por el controlador están en:

```text
controller/routing/
```

## Controlador actual

El controlador Ryu se ejecuta en un contenedor separado del entorno Mininet.

Estructura principal:

```text
docker/controllers/ryu-4.34-py38/Dockerfile
docker/controllers/ryu-4.34-py38/requirements.txt
docker/controllers/ryu-4.34-py38/controller-entrypoint.sh
```

Este entorno contiene las dependencias necesarias para ejecutar Ryu y la aplicación del controlador del testbed.

## Uso dentro de un experimento

Un experimento tiene que indicar la aplicación de controlador que debe ejecutarse.

Ejemplo:

```yaml
controller:
  app: controller.routing_controller
  ip: 127.0.0.1
  port: 6633
```

Campos principales:

```text
app: aplicación Python del controlador
ip: dirección donde escucha el controlador
port: puerto OpenFlow usado por los switches
```

Durante la ejecución, los switches Open vSwitch creados por Mininet se conectan al controlador mediante OpenFlow.

## Rol del controlador

Durante un experimento, el controlador se encarga de leer la configuración resuelta del experimento, recibir eventos OpenFlow desde los switches, aprender hosts y descubrir la topología, identificar flujos de tráfico, consultar el algoritmo de ruteo configurado, instalar reglas OpenFlow en los switches y registrar decisiones de ruteo y métricas cuando corresponde.

## Versiones de Python

Cada controlador puede requerir versiones diferentes de Python y librerías diferentes.

Por este motivo, no se recomienda mezclar varios controladores dentro de la misma imagen Docker.

La convención recomendada es que un controlador tenga una carpeta Docker propia y una versión de Python definida.

Ejemplo:

```text
docker/controllers/ryu-4.34-py38/
```

Esto indica:

```text
Controlador: Ryu
Versión: 4.34
Python: 3.8
```

Si se agrega otro controlador que necesita otra versión de Python, debe crearse otro entorno separado.

Ejemplos de convención:

```text
docker/controllers/osken-3.x-py310/
docker/controllers/floodlight-1.x-java/
```

## Agregar otro controlador

Para agregar otro controlador además de Ryu, se recomienda crear una nueva carpeta dentro de:

```text
docker/controllers/
```

Convención:

```text
docker/controllers/nombreControlador-version-runtime/
```

Ejemplos:

```text
docker/controllers/osken-3.x-py310/
docker/controllers/floodlight-1.x-java/
```

Cada entorno debe tener sus propios archivos.

Ejemplo:

```text
Dockerfile
requirements.txt
controller-entrypoint.sh
```

## Selección del entorno de controlador

El controlador se selecciona desde el archivo .env.

Ejemplo:

```env
CONTROLLER_ENV=ryu-4.34-py38
```

El valor de CONTROLLER_ENV debe coincidir con el nombre de una carpeta existente dentro de:

```text
docker/controllers/
```

De esta forma, para cambiar el entorno del controlador no es necesario modificar nada mas que el valor de CONTROLLER_ENV en .env.
