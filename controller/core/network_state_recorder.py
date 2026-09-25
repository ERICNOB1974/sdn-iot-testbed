import json
import os

from datetime import datetime
from datetime import timezone


class NetworkStateRecorder:
    """
    Persiste las mediciones dinamicas de los enlaces durante
    la ejecucion de un experimento.

    Cada medicion se almacena como una linea JSON independiente
    dentro de:

        network_state.jsonl

    El formato JSON Lines es conveniente porque:

    - permite escribir incrementalmente;
    - no es necesario mantener todas las muestras en memoria;
    - si el experimento termina inesperadamente, las muestras
      anteriores siguen siendo validas;
    - resulta sencillo procesarlo posteriormente con Python,
      pandas u otras herramientas.

    Cada registro representa el estado observado de un enlace
    dirigido en un instante determinado.
    """

    def __init__(self, results_dir):

        self.results_dir = results_dir

        os.makedirs(self.results_dir, exist_ok=True)

        self.file_path = os.path.join(self.results_dir, "network_state.jsonl")

    def record(self, source, destination, source_name, destination_name, metrics):

        #
        # Timestamp absoluto UTC.
        #
        # Esto permite posteriormente relacionar
        # las mediciones de red con decisiones de
        # routing y otros eventos del experimento.
        #

        timestamp = datetime.now(timezone.utc).isoformat()

        record = {
            "timestamp": timestamp,
            "source_switch": source_name,
            "destination_switch": destination_name,
            "source_dpid": source,
            "destination_dpid": destination,
            "metrics": dict(metrics),
        }

        #
        # JSONL:
        # una estructura JSON por linea.
        #

        with open(self.file_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, sort_keys=False))

            file.write("\n")
