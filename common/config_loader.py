"""
Carga y realiza validaciones básicas sobre los archivos YAML de configuración.

Evita que cada componente del testbed tenga que abrir y validar archivos YAML.

Las validaciones más detalladas sobre coherencia entre topología, red, tráfico
y otros componentes pertenecen al config_resolver.
"""

from pathlib import Path

import yaml

# Directorio raíz del proyecto.
# Es como hacer un cd .. & cd ..
#
# Esto es porque las rutas relativas de los YAML se interpretan siempre respecto
# de la raíz del repositorio.
ROOT_DIR = Path(__file__).resolve().parent.parent


def load_yaml(file_path):
    """
    Carga un archivo YAML y devuelve su contenido como una estructura Python.

    Parámetros:
        file_path:
            Ruta absoluta o relativa al archivo YAML que se desea cargar.

    Devuelve:
        La conversión Python del archivo YAML.

    Lanza:
        FileNotFoundError:
            Si el archivo indicado no existe.

        ValueError:
            Si el archivo existe pero está vacío.
    """

    path = Path(file_path)

    # Si la ruta no es absoluta, interpretarla respecto de la raíz del proyecto.
    if not path.is_absolute():
        path = ROOT_DIR / path

    if not path.is_file():
        raise FileNotFoundError(
            "No existe el archivo de configuracion: {}".format(path)
        )

    # Abrir el archivo y convertir su contenido YAML a estructuras de Python.
    with path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    # Un YAML vacío produce None
    if data is None:
        raise ValueError("El archivo de configuracion esta vacio: {}".format(path))

    return data


def load_experiment_config(file_path):
    """
    Carga la configuración base de un experimento y verifica que tenga
    las secciones y campos mínimos requeridos.

    Valida solamente la estructura básica del archivo de experimento.

    Parámetros:
        file_path:
            Ruta al archivo YAML del experimento.

    Devuelve:
        La configuración del experimento como diccionario.

    Lanza:
        ValueError:
            Si falta alguna sección o campo obligatorio.
    """

    config = load_yaml(file_path)

    # Secciones minimas que tiene que tener cualquier experimento.
    required_sections = [
        "experiment",
        "environment",
        "controller",
        "routing",
        "topology",
        "network",
        "traffic",
    ]

    # Verificar que estas existan.
    for section in required_sections:
        if section not in config:
            raise ValueError(
                "Falta la seccion '{}' en la configuracion del experimento".format(
                    section
                )
            )

    # Validar identificación del experimento.
    experiment_required = ["id", "name"]

    for field in experiment_required:
        if field not in config["experiment"]:
            raise ValueError(
                "Falta experiment.{} en la configuracion del experimento".format(field)
            )

    # Validar el entorno reproducible usado por el experimento
    environment_required = ["controller", "mininet", "openflow"]

    for field in environment_required:
        if field not in config["environment"]:
            raise ValueError(
                "Falta environment.{} en la configuracion del experimento".format(field)
            )

    # Validar la configuración necesaria para iniciar el controlador.
    controller_required = ["app", "ip", "port"]

    for field in controller_required:
        if field not in config["controller"]:
            raise ValueError(
                "Falta controller.{} en la configuracion del experimento".format(field)
            )

    # Validar la definición del algoritmo de ruteo.
    routing_required = ["name", "module", "class", "metric"]

    for field in routing_required:
        if field not in config["routing"]:
            raise ValueError(
                "Falta routing.{} en la configuracion del experimento".format(field)
            )

    # Validar la definición de topología a utilizar.
    topology_required = ["definition"]

    for field in topology_required:
        if field not in config["topology"]:
            raise ValueError(
                "Falta topology.{} en la configuracion del experimento".format(field)
            )

    # Validar que exista una referencia al perfil de condiciones de red.
    network_required = ["profile"]

    for field in network_required:
        if field not in config["network"]:
            raise ValueError(
                "Falta network.{} en la configuracion del experimento".format(field)
            )

    # Validar la configuración principal de tráfico. Profile indica que tráfico ejecutar.
    # Generator indica que implementación Python sabe generarlo.
    traffic_required = ["profile", "generator"]

    for field in traffic_required:
        if field not in config["traffic"]:
            raise ValueError(
                "Falta traffic.{} en la configuracion del experimento".format(field)
            )

    # Validar la referencia al generador de tráfico.
    generator_required = ["module", "function"]

    for field in generator_required:
        if field not in config["traffic"]["generator"]:
            raise ValueError(
                "Falta traffic.generator.{} en la configuracion del experimento".format(
                    field
                )
            )

    # Si todas las validaciones pasan, la configuracion del experimento es valida.
    return config


def load_traffic_profile(file_path):
    """
    Carga un perfil de tráfico y devuelve específicamente su sección "traffic".

    Los perfiles de tráfico tienen una estructura:

        traffic:
            type: ping
            flows:
                ...

    Parámetros:
        file_path:
            Ruta al archivo YAML que contiene el perfil de tráfico.

    Devuelve:
        El contenido de la sección "traffic".

    Lanza:
        ValueError:
            Si el archivo no contiene dicha sección.
    """

    # Cargar el archivo YAML del perfil
    profile = load_yaml(file_path)

    if "traffic" not in profile:
        raise ValueError("El perfil de trafico no contiene la seccion 'traffic'")

    return profile["traffic"]
