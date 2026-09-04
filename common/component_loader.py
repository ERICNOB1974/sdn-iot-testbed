"""
Carga componentes de python a partir del modulo y nombre.
Permite que distintos componentes del testbed (algoritmos de ruteo,
generadores de trafico, collectors), puedan ser seleccionados
desde los archivos de configuración sin tener que importarlos directamente
en el código que los usa.
"""

import importlib


def load_object(module_name, object_name):
    """
    Importa un módulo de Python y obtiene uno de los objetos definidos adentro. Por ejemplo,
    una clase o una función.

    Parámetros:
        module_name:
            Nombre completo del módulo que se desea importar.
            Ejemplo: "controller.routing.dijkstra".

        object_name:
            Nombre del objeto que se desea obtener dentro del módulo.
            Ejemplo: "DijkstraRouting".

    Devuelve:
        El objeto encontrado dentro del módulo.
    """

    # Importar dinámicamente el módulo indicado por su nombre.
    module = importlib.import_module(module_name)

    try:
        return getattr(module, object_name)

    except AttributeError as error:
        raise ImportError(
            "El objeto '{}' no existe en el modulo '{}'".format(
                object_name, module_name
            )
        ) from error


def create_instance(module_name, class_name, *args, **kwargs):
    """
    Carga dinámicamente una clase y crea una instancia de ella.

    Se utiliza para componentes que necesitan ser instanciados,
    como los algoritmos de ruteo.
    """

    # Obtener la clase indicada mediante su módulo y nombre.
    component_class = load_object(module_name, class_name)

    # Crear y devolver una instancia de la clase.
    return component_class(*args, **kwargs)


def load_traffic_generator(config):
    """
    Carga la función encargada de generar el tráfico del experimento.

    Devuelve:
        La función generadora de tráfico lista para ser ejecutada.
    """

    # Obtener la configuración correspondiente al generador.
    # Por ejemplo:
    # generator:
    #   module: traffic.generators.ping
    #   function: run_ping
    generator = config["generator"]

    # Carga y devuelve la función indicada en la configuración.
    # No se ejecuta, solamente se obtiene la referencia a la función,
    # el runner es el que la llama posteriormente.
    return load_object(generator["module"], generator["function"])


def load_collectors(configs):
    """
    Carga todos los collectors declarados para el experimento.

    Cada collector está definido mediante un nombre, un módulo y una
    función. Esta función convierte esas definiciones en referencias
    a funciones Python que posteriormente podrá ejecutar el runner

    Devuelve:
        Una lista de tuplas con la forma:

        (nombre_del_collector, funcion_del_collector)
    """

    collectors = []

    # Recorrer las configuraciones de collectors declaradas
    for config in configs:
        # Cargar la función que implementa el collector actual.
        collector = load_object(config["module"], config["function"])

        # Guardar el nombre del collector como la función que debe ejecutarse despues.
        collectors.append((config["name"], collector))

    return collectors
