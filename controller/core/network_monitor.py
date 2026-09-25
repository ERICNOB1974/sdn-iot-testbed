import time

from ryu.lib import hub


class NetworkMonitor:
    """
    Monitorea periodicamente las estadisticas OpenFlow de los puertos
    de los switches y transforma los contadores acumulativos de OVS
    en metricas dinamicas utilizables por los algoritmos de routing.

    OpenFlow entrega valores acumulativos como:

        tx_bytes
        rx_bytes
        tx_packets
        rx_packets

    NetworkMonitor toma muestras periodicas y calcula diferencias entre
    dos muestras consecutivas.

    A partir de esas diferencias obtiene, entre otras metricas:

        tx_bps
        rx_bps
        tx_pps
        rx_pps
        utilization
        residual_bandwidth_mbps

    Las metricas calculadas son:

    1. almacenadas en NetworkState para que puedan ser utilizadas por
       los algoritmos de routing;

    2. opcionalmente persistidas mediante NetworkStateRecorder para
       poder analizar posteriormente la evolucion temporal de la red.

    NetworkMonitor no implementa ninguna politica de routing.
    Su unica responsabilidad es observar el estado de la red.
    """

    def __init__(
        self,
        app,
        topology,
        network_state,
        recorder=None,
        interval=2.0,
    ):

        self.app = app

        self.topology = topology

        self.network_state = network_state

        #
        # Recorder opcional.
        #
        # Si existe, cada muestra calculada sera
        # almacenada en network_state.jsonl.
        #

        self.recorder = recorder

        #
        # Periodo de muestreo en segundos.
        #

        self.interval = float(interval)

        #
        # Muestra anterior de cada puerto.
        #
        # Clave:
        #
        #     (dpid, port_no)
        #
        # Valor:
        #
        #     {
        #         "timestamp": ...,
        #         "tx_bytes": ...,
        #         "rx_bytes": ...,
        #         "tx_packets": ...,
        #         "rx_packets": ...
        #     }
        #
        # Necesitamos conservar una muestra anterior porque
        # OpenFlow entrega contadores acumulativos y no tasas.
        #

        self.previous_port_stats = {}

        #
        # Thread cooperativo de Ryu/eventlet.
        #

        self.monitor_thread = None

    def start(self):

        #
        # Evitar iniciar dos veces el monitor.
        #

        if self.monitor_thread is not None:
            return

        self.monitor_thread = hub.spawn(self._monitor_loop)

    def stop(self):

        #
        # Detener el thread del monitor.
        #

        if self.monitor_thread is None:
            return

        hub.kill(self.monitor_thread)

        self.monitor_thread = None

    def _monitor_loop(self):

        #
        # Bucle principal del monitor.
        #
        # Periodicamente solicita estadisticas de puertos
        # a todos los switches conocidos.
        #

        while True:
            self.request_port_stats()

            hub.sleep(self.interval)

    def request_port_stats(self):

        #
        # Solicitar estadisticas de puertos a todos
        # los switches actualmente registrados.
        #

        for datapath in list(self.topology.datapaths.values()):
            self._request_port_stats(datapath)

    def _request_port_stats(self, datapath):

        #
        # Construir y enviar una solicitud OpenFlow
        # OFPPortStatsRequest a un switch.
        #

        ofproto = datapath.ofproto

        parser = datapath.ofproto_parser

        request = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)

        datapath.send_msg(request)

    def process_port_stats(self, datapath, stats):

        #
        # Procesar la respuesta enviada por un switch.
        #

        dpid = datapath.id

        #
        # time.monotonic() se utiliza para medir intervalos.
        #
        # No depende del reloj del sistema y por lo tanto
        # es apropiado para calcular diferencias temporales.
        #

        timestamp = time.monotonic()

        ofproto = datapath.ofproto

        for stat in stats:
            port_no = stat.port_no

            #
            # Ignorar puertos especiales de OpenFlow.
            #
            # Nos interesan solamente puertos reales
            # asociados a interfaces de la red.
            #

            if port_no >= ofproto.OFPP_MAX:
                continue

            #
            # Determinar si el puerto corresponde a
            # un enlace switch-switch.
            #
            # Los puertos hacia hosts no forman parte
            # del grafo utilizado por los algoritmos
            # de routing y por eso no se monitorean aca.
            #

            link = self.topology.get_link_by_port(dpid, port_no)

            if link is None:
                continue

            source, destination = link

            #
            # Identidad unica de la muestra del puerto.
            #

            key = (dpid, port_no)

            #
            # Contadores actuales entregados por OpenFlow.
            #

            current = {
                "timestamp": timestamp,
                "tx_bytes": stat.tx_bytes,
                "rx_bytes": stat.rx_bytes,
                "tx_packets": stat.tx_packets,
                "rx_packets": stat.rx_packets,
            }

            previous = self.previous_port_stats.get(key)

            #
            # La primera muestra solamente establece
            # la linea base.
            #
            # Todavia no existe una muestra anterior
            # contra la cual calcular una tasa.
            #

            if previous is None:
                self.previous_port_stats[key] = current

                continue

            #
            # Tiempo transcurrido entre ambas muestras.
            #

            elapsed = timestamp - previous["timestamp"]

            if elapsed <= 0:
                self.previous_port_stats[key] = current

                continue

            #
            # Diferencias entre los contadores acumulativos.
            #

            delta_tx_bytes = current["tx_bytes"] - previous["tx_bytes"]

            delta_rx_bytes = current["rx_bytes"] - previous["rx_bytes"]

            delta_tx_packets = current["tx_packets"] - previous["tx_packets"]

            delta_rx_packets = current["rx_packets"] - previous["rx_packets"]

            #
            # Si OVS reinicio los contadores o el puerto
            # fue recreado, las diferencias pueden ser
            # negativas.
            #
            # En ese caso descartamos esta medicion y
            # utilizamos la muestra actual como nueva
            # referencia.
            #

            if (
                delta_tx_bytes < 0
                or delta_rx_bytes < 0
                or delta_tx_packets < 0
                or delta_rx_packets < 0
            ):
                self.previous_port_stats[key] = current

                continue

            #
            # Calcular tasas.
            #
            # bytes/s -> bits/s:
            #
            #     delta_bytes * 8 / elapsed
            #

            tx_bps = delta_tx_bytes * 8.0 / elapsed

            rx_bps = delta_rx_bytes * 8.0 / elapsed

            #
            # Paquetes por segundo.
            #

            tx_pps = delta_tx_packets / elapsed

            rx_pps = delta_rx_packets / elapsed

            #
            # Metricas dinamicas basicas.
            #

            dynamic_metrics = {
                "tx_bps": tx_bps,
                "rx_bps": rx_bps,
                "tx_pps": tx_pps,
                "rx_pps": rx_pps,
                "sample_interval_seconds": elapsed,
                "sample_time_monotonic": timestamp,
            }

            #
            # Obtener la capacidad configurada del enlace.
            #
            # Esta informacion proviene del perfil de red.
            #
            # Ejemplo:
            #
            #     bandwidth_mbps: 100
            #

            bandwidth_mbps = self.network_state.get_static_metric(
                source, destination, "bandwidth_mbps"
            )

            if bandwidth_mbps is not None:
                capacity_bps = float(bandwidth_mbps) * 1_000_000.0

                if capacity_bps > 0:
                    #
                    # Utilizacion del enlace en sentido
                    # source -> destination.
                    #

                    utilization = tx_bps / capacity_bps

                    #
                    # Por bursting o diferencias temporales
                    # puede aparecer momentaneamente un valor
                    # mayor que 1.
                    #
                    # Para representar ocupacion normalizada
                    # limitamos el valor al intervalo [0, 1].
                    #

                    utilization = max(0.0, min(utilization, 1.0))

                    #
                    # Ancho de banda residual.
                    #

                    residual_bandwidth_bps = max(capacity_bps - tx_bps, 0.0)

                    residual_bandwidth_mbps = residual_bandwidth_bps / 1_000_000.0

                    dynamic_metrics.update(
                        {
                            "utilization": utilization,
                            "residual_bandwidth_mbps": (residual_bandwidth_mbps),
                        }
                    )

            #
            # Actualizar NetworkState.
            #
            # A partir de este momento los algoritmos
            # de routing pueden consultar estas metricas
            # mediante RoutingContext.network_state.
            #

            self.network_state.update_dynamic_link_metrics(
                source, destination, dynamic_metrics
            )

            #
            # Persistir la muestra.
            #
            # Guardamos una vista combinada de:
            #
            # - metricas estaticas;
            # - metricas dinamicas.
            #
            # Ejemplo:
            #
            # delay_ms
            # bandwidth_mbps
            # routing_cost
            # tx_bps
            # utilization
            # residual_bandwidth_mbps
            #

            if self.recorder is not None:
                source_name = self.topology.network_model.get_switch_name(source)

                destination_name = self.topology.network_model.get_switch_name(
                    destination
                )

                metrics = self.network_state.get_link_metrics(source, destination)

                self.recorder.record(
                    source=source,
                    destination=destination,
                    source_name=source_name,
                    destination_name=destination_name,
                    metrics=metrics,
                )

            #
            # Log de debugging.
            #
            # No aparece normalmente cuando Ryu se ejecuta
            # con nivel INFO.
            #

            self.app.logger.debug(
                "LINK STATE: s%s -> s%s | "
                "tx=%.2f Mbps | rx=%.2f Mbps | "
                "util=%.4f | residual=%.2f Mbps",
                source,
                destination,
                dynamic_metrics["tx_bps"] / 1_000_000.0,
                dynamic_metrics["rx_bps"] / 1_000_000.0,
                dynamic_metrics.get("utilization", 0.0),
                dynamic_metrics.get("residual_bandwidth_mbps", 0.0),
            )

            #
            # La muestra actual se convierte en
            # referencia para la proxima iteracion.
            #

            self.previous_port_stats[key] = current
