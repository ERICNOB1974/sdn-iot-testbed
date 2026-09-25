class NetworkState:
    """
    Mantiene el estado de red disponible para los algoritmos de routing.

    NetworkState separa dos tipos de informacion:

    1. Metricas estaticas:
       provienen de la configuracion del experimento y estan almacenadas
       en el grafo de TopologyManager.

       Ejemplos:
           delay_ms
           routing_cost
           bandwidth_mbps

    2. Metricas dinamicas:
       son obtenidas o calculadas durante la ejecucion del experimento.

       Ejemplos:
           tx_bps
           rx_bps
           utilization
           residual_bandwidth_mbps
           measured_delay_ms

    Los algoritmos de routing acceden a esta clase mediante RoutingContext,
    evitando depender directamente de los mecanismos utilizados para
    obtener las mediciones.
    """

    def __init__(self, topology):

        self.topology = topology

        #
        # Estado dinamico independiente del grafo.
        #
        # La clave es:
        #
        #     (source_dpid, destination_dpid)
        #
        # Ejemplo:
        #
        #     (1, 2): {
        #         "tx_bps": 2500000,
        #         "utilization": 0.25
        #     }
        #

        self.dynamic_link_metrics = {}

    def _validate_link(self, source, destination):

        #
        # Verificar que el enlace exista en la
        # topologia descubierta.
        #

        if not self.topology.graph.has_edge(source, destination):
            raise KeyError("No existe el enlace {} -> {}".format(source, destination))

    def get_static_link_metrics(self, source, destination):

        #
        # Metricas provenientes del perfil de red.
        #

        self._validate_link(source, destination)

        return dict(self.topology.graph[source][destination].get("metrics", {}))

    def get_dynamic_link_metrics(self, source, destination):

        #
        # Metricas observadas o calculadas durante
        # la ejecucion del experimento.
        #

        self._validate_link(source, destination)

        return dict(self.dynamic_link_metrics.get((source, destination), {}))

    def get_link_metrics(self, source, destination):

        #
        # Devuelve una vista combinada de las
        # metricas estaticas y dinamicas.
        #

        metrics = self.get_static_link_metrics(source, destination)

        metrics.update(self.get_dynamic_link_metrics(source, destination))

        return metrics

    def get_metric(self, source, destination, name, default=None):

        #
        # Consultar cualquier metrica disponible
        # para un enlace.
        #

        metrics = self.get_link_metrics(source, destination)

        return metrics.get(name, default)

    def get_static_metric(self, source, destination, name, default=None):

        #
        # Consultar especificamente una metrica
        # configurada en el escenario.
        #

        metrics = self.get_static_link_metrics(source, destination)

        return metrics.get(name, default)

    def get_dynamic_metric(self, source, destination, name, default=None):

        #
        # Consultar especificamente una metrica
        # obtenida durante la ejecucion.
        #

        metrics = self.get_dynamic_link_metrics(source, destination)

        return metrics.get(name, default)

    def set_dynamic_metric(self, source, destination, name, value):

        #
        # Actualizar una unica metrica dinamica.
        #

        self._validate_link(source, destination)

        key = (source, destination)

        metrics = self.dynamic_link_metrics.setdefault(key, {})

        metrics[name] = value

    def update_dynamic_link_metrics(self, source, destination, metrics):

        #
        # Actualizar varias metricas dinamicas
        # del mismo enlace.
        #

        self._validate_link(source, destination)

        key = (source, destination)

        current = self.dynamic_link_metrics.setdefault(key, {})

        current.update(metrics)

    def clear_dynamic_link_metrics(self, source=None, destination=None):

        #
        # Sin argumentos:
        #     limpia todo el estado dinamico.
        #
        # Con source y destination:
        #     limpia solamente ese enlace.
        #

        if source is None and destination is None:
            self.dynamic_link_metrics.clear()

            return

        if source is None or destination is None:
            raise ValueError("source y destination deben indicarse juntos")

        self.dynamic_link_metrics.pop((source, destination), None)

    def get_path_additive_metric(self, path, metric):

        #
        # Calcula una metrica acumulativa a lo
        # largo de todo el camino.
        #
        # Ejemplo:
        #
        # s1 --5 ms--> s2 --10 ms--> s4
        #
        # delay total = 15 ms
        #

        total = 0

        for index in range(len(path) - 1):
            source = path[index]

            destination = path[index + 1]

            value = self.get_metric(source, destination, metric)

            if value is None:
                return None

            total += value

        return total

    def get_path_bottleneck_metric(self, path, metric):

        values = []

        for index in range(len(path) - 1):
            source = path[index]
            destination = path[index + 1]

            value = self.get_metric(source, destination, metric)

            if value is None:
                return None

            values.append(value)

        if not values:
            return None

        return min(values)

    def get_path_max_metric(self, path, metric):

        values = []

        for index in range(len(path) - 1):
            source = path[index]
            destination = path[index + 1]

            value = self.get_metric(source, destination, metric)

            if value is None:
                return None

            values.append(value)

        if not values:
            return None

        return max(values)

    def snapshot(self):

        #
        # Obtener una fotografia completa del
        # estado actual de la red.
        #
        # Mas adelante esto nos servira para:
        #
        # - debugging;
        # - collectors;
        # - resultados;
        # - registrar que estado observo un
        #   algoritmo al tomar una decision.
        #

        result = {}

        for source, destination in self.topology.graph.edges():
            key = "{}->{}".format(source, destination)

            result[key] = self.get_link_metrics(source, destination)

        return result
