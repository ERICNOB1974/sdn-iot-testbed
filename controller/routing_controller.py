import os

import networkx as nx

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import packet
from ryu.ofproto import ofproto_v1_3
from ryu.topology import event

from common.component_loader import create_instance
from common.config_loader import load_yaml

from controller.core.flow_identity import FlowIdentity
from controller.core.flow_manager import FlowManager
from controller.core.flow_registry import FlowRegistry
from controller.core.flooding_manager import FloodingManager
from controller.core.host_manager import HostManager
from controller.core.network_model import NetworkModel
from controller.core.network_monitor import NetworkMonitor
from controller.core.network_state import NetworkState
from controller.core.network_state_recorder import NetworkStateRecorder
from controller.core.result_manager import ResultManager
from controller.core.routing_state import RoutingState
from controller.core.rule_capacity_manager import RuleCapacityManager
from controller.core.topology_manager import TopologyManager

from controller.routing.context import RoutingContext


class RoutingController(app_manager.RyuApp):
    """
    Controlador SDN principal del banco de pruebas.

    Sus responsabilidades principales son:

    - cargar la configuracion resuelta del experimento;
    - cargar dinamicamente el algoritmo de routing;
    - mantener la topologia descubierta por Ryu;
    - aprender la ubicacion de los hosts;
    - identificar y registrar los flujos;
    - construir el contexto que reciben los algoritmos;
    - solicitar decisiones de routing;
    - almacenar decisiones sticky;
    - instalar reglas OpenFlow;
    - realizar flooding auxiliar cuando el destino aun no es conocido;
    - monitorear el estado dinamico de los enlaces;
    - almacenar resultados y mediciones para analisis posterior.

    La logica especifica de cada algoritmo de routing NO debe
    implementarse en esta clase.

    Algoritmos como Dijkstra, SWAY, AQRA o MINA deben implementar
    su propia logica dentro de controller/routing/.
    """

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    #
    # Politicas de decision actualmente soportadas
    # por el controlador.
    #

    SUPPORTED_DECISION_POLICIES = {
        "sticky",
    }

    #
    # Modos de planificacion actualmente soportados.
    #

    SUPPORTED_SCHEDULING_MODES = {
        "per_flow",
    }

    def __init__(self, *args, **kwargs):

        super(RoutingController, self).__init__(*args, **kwargs)

        #
        # ============================================================
        # Configuracion resuelta.
        # ============================================================
        #

        config_path = os.environ["RESOLVED_CONFIG"]

        self.config = load_yaml(config_path)

        #
        # ============================================================
        # Algoritmo de routing.
        # ============================================================
        #

        routing_config = self.config["routing"]

        self.routing_name = routing_config["name"]

        self.routing_metric = routing_config["metric"]

        #
        # Crear dinamicamente la instancia del algoritmo.
        #
        # Ejemplo:
        #
        # module:
        #     controller.routing.dijkstra
        #
        # class:
        #     DijkstraRouting
        #

        self.routing = create_instance(
            routing_config["module"], routing_config["class"]
        )

        #
        # Contrato declarado por el algoritmo.
        #

        self.decision_policy = getattr(self.routing, "decision_policy", "sticky")

        self.scheduling_mode = getattr(self.routing, "scheduling_mode", "per_flow")

        self._validate_routing_contract()

        #
        # ============================================================
        # Modelo de red.
        # ============================================================
        #

        self.network_model = NetworkModel(self.config)

        #
        # ============================================================
        # Topologia descubierta por Ryu.
        # ============================================================
        #

        self.topology = TopologyManager(self.network_model)

        #
        # ============================================================
        # Estado de red.
        # ============================================================
        #
        # NetworkState contiene:
        #
        # - metricas estaticas;
        # - metricas dinamicas.
        #

        self.network_state = NetworkState(self.topology)

        #
        # ============================================================
        # Resultados.
        # ============================================================
        #

        results_dir = os.environ.get("RESULTS_DIR", "/workspace/results")

        self.results = ResultManager(results_dir)

        #
        # ============================================================
        # Recorder del estado dinamico.
        # ============================================================
        #
        # Guarda las muestras del NetworkMonitor en:
        #
        #     network_state.jsonl
        #

        self.network_state_recorder = NetworkStateRecorder(results_dir)

        #
        # ============================================================
        # Monitor dinamico de red.
        # ============================================================
        #
        # Solicita estadisticas OpenFlow de los puertos
        # y calcula:
        #
        # - tx_bps;
        # - rx_bps;
        # - tx_pps;
        # - rx_pps;
        # - utilization;
        # - residual_bandwidth_mbps.
        #

        self.network_monitor = NetworkMonitor(
            app=self,
            topology=self.topology,
            network_state=self.network_state,
            recorder=self.network_state_recorder,
            interval=2.0,
        )

        #
        # ============================================================
        # Registro de flujos.
        # ============================================================
        #
        # FlowRegistry necesita la configuracion completa
        # para poder resolver las especificaciones declaradas
        # en traffic.config.flows.
        #

        self.flow_registry = FlowRegistry(self.config)

        #
        # ============================================================
        # Capacidad de reglas.
        # ============================================================
        #
        # Esta abstraccion sera especialmente util para
        # algoritmos como SWAY.
        #

        self.rule_capacity = RuleCapacityManager()

        #
        # ============================================================
        # Hosts.
        # ============================================================
        #

        self.hosts = HostManager()

        #
        # ============================================================
        # Administracion de reglas OpenFlow.
        # ============================================================
        #

        self.flows = FlowManager()

        #
        # ============================================================
        # Flooding.
        # ============================================================
        #
        # Se utiliza cuando todavia no conocemos
        # la ubicacion del host destino.
        #

        self.flooding = FloodingManager(self.topology)

        #
        # ============================================================
        # Estado de decisiones de routing.
        # ============================================================
        #
        # RoutingState conserva las decisiones cuando
        # decision_policy == "sticky".
        #

        self.routing_state = RoutingState()

        #
        # ============================================================
        # Logs iniciales.
        # ============================================================
        #

        self.logger.info("Configuracion del experimento: %s", config_path)

        self.logger.info("Algoritmo de ruteo: %s", self.routing_name)

        self.logger.info("Metrica de ruteo: %s", self.routing_metric)

        self.logger.info("Politica de decision: %s", self.decision_policy)

        self.logger.info("Modo de planificacion: %s", self.scheduling_mode)

        #
        # ============================================================
        # Iniciar monitor.
        # ============================================================
        #
        # Lo hacemos al final del constructor para que
        # todos los componentes del controlador ya existan.
        #

        self.network_monitor.start()

    def _validate_routing_contract(self):
        """
        Verifica que el algoritmo cargado utilice un contrato
        actualmente soportado por RoutingController.
        """

        if self.decision_policy not in self.SUPPORTED_DECISION_POLICIES:
            raise ValueError(
                "Politica de decision no soportada actualmente: '{}'".format(
                    self.decision_policy
                )
            )

        if self.scheduling_mode not in self.SUPPORTED_SCHEDULING_MODES:
            raise ValueError(
                "Modo de planificacion no soportado actualmente: '{}'".format(
                    self.scheduling_mode
                )
            )

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Se ejecuta cuando un switch OpenFlow se conecta
        correctamente al controlador.
        """

        datapath = ev.msg.datapath

        #
        # Registrar datapath para poder enviar posteriormente
        # FlowMod, StatsRequest, PacketOut, etc.
        #

        self.topology.register_datapath(datapath)

        #
        # Instalar table-miss.
        #
        # Los paquetes que no coincidan con una regla
        # seran enviados al controlador.
        #

        self.flows.install_table_miss(datapath)

    @set_ev_cls(event.EventSwitchEnter)
    @set_ev_cls(event.EventLinkAdd)
    def topology_change_handler(self, ev):
        """
        Actualiza el grafo cuando Ryu descubre switches
        o enlaces nuevos.
        """

        self.topology.update(self)

        self.logger.info("Grafo actual: %s", list(self.topology.graph.edges(data=True)))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Procesa paquetes enviados por los switches al controlador.

        Es el punto principal donde:

        - se aprende la ubicacion de los hosts;
        - se identifica el flujo;
        - se resuelve su FlowSpecification;
        - se crea RoutingContext;
        - se consulta el algoritmo;
        - se guarda RoutingDecision;
        - se instalan reglas OpenFlow.
        """

        msg = ev.msg

        datapath = msg.datapath

        dpid = datapath.id

        in_port = msg.match["in_port"]

        #
        # ------------------------------------------------------------
        # Decodificar paquete.
        # ------------------------------------------------------------
        #

        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        #
        # LLDP es utilizado por Ryu para descubrir
        # la topologia.
        #
        # No debe procesarse como trafico normal.
        #

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        #
        # ------------------------------------------------------------
        # Crear identidad generica del flujo.
        # ------------------------------------------------------------
        #

        flow = FlowIdentity.from_packet(pkt)

        if flow is None:
            return

        src = flow.source_mac

        dst = flow.destination_mac

        #
        # ------------------------------------------------------------
        # Esperar topologia completa.
        # ------------------------------------------------------------
        #
        # Evita aprender como hosts direcciones que aparecen
        # temporalmente por puertos switch-switch antes de que
        # Ryu haya terminado de descubrir los enlaces.
        #

        if not self.topology.is_complete():
            return

        #
        # ------------------------------------------------------------
        # Aprender host origen.
        # ------------------------------------------------------------
        #
        # Solo aprendemos un host cuando el paquete entra
        # por un puerto que NO corresponde a un enlace
        # entre switches.
        #

        if not self.topology.is_switch_port(dpid, in_port):
            learned = self.hosts.learn(src, dpid, in_port)

            if learned:
                self.logger.info(
                    "HOST: %s conectado a s%s puerto %s", src, dpid, in_port
                )

        #
        # ------------------------------------------------------------
        # Destino desconocido.
        # ------------------------------------------------------------
        #

        if not self.hosts.is_known(dst):
            self.flooding.flood(msg)

            return

        #
        # ------------------------------------------------------------
        # Obtener switches de acceso.
        # ------------------------------------------------------------
        #

        src_switch = self.hosts.get_switch(src)

        dst_switch = self.hosts.get_switch(dst)

        #
        # ------------------------------------------------------------
        # Trafico no IP.
        # ------------------------------------------------------------
        #
        # ARP y otros protocolos auxiliares no deben modificar
        # el estado de los algoritmos experimentales.
        #
        # Utilizamos shortest path exclusivamente como
        # forwarding auxiliar.
        #

        if not flow.is_ip_flow():
            try:
                path = nx.shortest_path(
                    self.topology.graph,
                    source=src_switch,
                    target=dst_switch,
                    weight="weight",
                )

            except nx.NetworkXNoPath:
                return

            self.flows.install_path(path, flow, self.topology, self.hosts)

            self.flows.forward_packet(msg, path, flow, self.topology, self.hosts)

            return

        #
        # ------------------------------------------------------------
        # Resolver FlowSpecification.
        # ------------------------------------------------------------
        #
        # Busca si el flujo IP observado corresponde a uno
        # declarado en traffic.config.flows.
        #
        # Por ejemplo:
        #
        # flow-1:
        #     h1 -> h3
        #
        # Un flujo de respuesta puede no tener una
        # especificacion declarada.
        #

        flow_spec = self.flow_registry.resolve(flow)

        #
        # Registrar flujo IP activo.
        #

        self.flow_registry.register_active_flow(flow, specification=flow_spec)

        #
        # ------------------------------------------------------------
        # Construir RoutingContext.
        # ------------------------------------------------------------
        #
        # Esta es la informacion comun que reciben todos
        # los algoritmos de routing.
        #

        context = RoutingContext(
            source=src_switch,
            destination=dst_switch,
            source_mac=src,
            destination_mac=dst,
            flow=flow,
            flow_spec=flow_spec,
            network_state=self.network_state,
            active_flows=self.flow_registry.get_active_flows(),
            rule_capacity=self.rule_capacity,
        )

        #
        # ------------------------------------------------------------
        # Verificar modo de planificacion.
        # ------------------------------------------------------------
        #
        # PacketIn actualmente ejecuta decisiones per-flow.
        #

        if self.scheduling_mode != "per_flow":
            raise ValueError(
                "El controlador no puede ejecutar scheduling_mode '{}' mediante PacketIn".format(
                    self.scheduling_mode
                )
            )

        #
        # ------------------------------------------------------------
        # Buscar decision existente.
        # ------------------------------------------------------------
        #

        if self.decision_policy == "sticky":
            decision = self.routing_state.get_decision(src_switch, dst_switch, flow)

        else:
            raise ValueError(
                "Politica de decision no soportada actualmente: '{}'".format(
                    self.decision_policy
                )
            )

        #
        # La decision es nueva solamente cuando no existe
        # dentro de RoutingState.
        #

        new_decision = decision is None

        #
        # ------------------------------------------------------------
        # Ejecutar algoritmo.
        # ------------------------------------------------------------
        #

        if new_decision:
            try:
                decision = self.routing.compute(self.topology.graph, context)

            except nx.NetworkXNoPath:
                self.logger.info(
                    "No existe camino entre s%s y s%s", src_switch, dst_switch
                )

                return

            #
            # Todo algoritmo debe devolver RoutingDecision.
            #

            if decision is None:
                raise ValueError(
                    "El algoritmo '{}' no devolvio una RoutingDecision".format(
                        self.routing_name
                    )
                )

            #
            # --------------------------------------------------------
            # Admission control.
            # --------------------------------------------------------
            #
            # Esto deja preparada la infraestructura para
            # algoritmos que puedan rechazar un flujo.
            #

            if not decision.admitted:
                self.logger.info(
                    "%s: FLUJO NO ADMITIDO | %s -> %s",
                    self.routing_name.upper(),
                    flow.source_ip,
                    flow.destination_ip,
                )

                return

            #
            # Una decision admitida necesita un camino.
            #

            if decision.path is None:
                raise ValueError(
                    "El algoritmo '{}' devolvio una decision admitida sin path".format(
                        self.routing_name
                    )
                )

            #
            # Guardar decision sticky.
            #

            if self.decision_policy == "sticky":
                self.routing_state.save_decision(src_switch, dst_switch, flow, decision)

        #
        # ------------------------------------------------------------
        # Validar decision recuperada.
        # ------------------------------------------------------------
        #

        if not decision.admitted:
            return

        path = decision.path

        cost = decision.cost

        if path is None:
            raise ValueError(
                "El algoritmo '{}' devolvio una decision admitida sin path".format(
                    self.routing_name
                )
            )

        #
        # ------------------------------------------------------------
        # Log de nueva decision.
        # ------------------------------------------------------------
        #

        if new_decision:
            self.logger.info(
                "%s: NUEVA DECISION | "
                "mac=%s -> %s | "
                "ip=%s -> %s | "
                "eth_type=%s | "
                "proto=%s | "
                "sport=%s | "
                "dport=%s | "
                "s%s -> s%s | "
                "path=%s | "
                "cost=%s",
                self.routing_name.upper(),
                flow.source_mac,
                flow.destination_mac,
                flow.source_ip,
                flow.destination_ip,
                flow.eth_type,
                flow.ip_protocol,
                flow.source_port,
                flow.destination_port,
                src_switch,
                dst_switch,
                path,
                cost,
            )

        #
        # ------------------------------------------------------------
        # Guardar decision experimental.
        # ------------------------------------------------------------
        #
        # Una linea por nueva decision en:
        #
        #     routing_decisions.jsonl
        #

        if new_decision:
            self.results.save_routing_decision(
                algorithm=self.routing_name,
                metric=self.routing_metric,
                source=src_switch,
                destination=dst_switch,
                flow=flow,
                decision=decision,
            )

        #
        # ------------------------------------------------------------
        # Registrar consumo de reglas.
        # ------------------------------------------------------------
        #

        if new_decision:
            self.rule_capacity.register_path(path, flow)

        #
        # ------------------------------------------------------------
        # Instalar reglas OpenFlow.
        # ------------------------------------------------------------
        #

        self.flows.install_path(path, flow, self.topology, self.hosts)

        #
        # ------------------------------------------------------------
        # Reenviar paquete actual.
        # ------------------------------------------------------------
        #

        self.flows.forward_packet(msg, path, flow, self.topology, self.hosts)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        """
        Recibe las estadisticas de puertos solicitadas
        periodicamente por NetworkMonitor.

        RoutingController solamente recibe el evento y delega
        el procesamiento al monitor.
        """

        self.network_monitor.process_port_stats(ev.msg.datapath, ev.msg.body)
