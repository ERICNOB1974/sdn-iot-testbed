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
from controller.core.host_manager import HostManager
from controller.core.network_model import NetworkModel
from controller.core.network_state import NetworkState
from controller.core.result_manager import ResultManager
from controller.core.routing_state import RoutingState
from controller.core.rule_capacity_manager import RuleCapacityManager
from controller.core.topology_manager import TopologyManager
from controller.routing.context import RoutingContext


class RoutingController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    SUPPORTED_DECISION_POLICIES = {
        "sticky",
    }

    SUPPORTED_SCHEDULING_MODES = {
        "per_flow",
    }

    def __init__(self, *args, **kwargs):

        super(RoutingController, self).__init__(*args, **kwargs)

        #
        # Configuracion resuelta.
        #

        config_path = os.environ["RESOLVED_CONFIG"]

        self.config = load_yaml(config_path)

        #
        # Routing.
        #

        routing_config = self.config["routing"]

        self.routing_name = routing_config["name"]

        self.routing_metric = routing_config["metric"]

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
        # Modelo de red.
        #

        self.network_model = NetworkModel(self.config)

        #
        # Topologia descubierta por Ryu.
        #

        self.topology = TopologyManager(self.network_model)

        #
        # Estado generico de la red.
        #

        self.network_state = NetworkState(self.topology)

        #
        # Registro de flujos.
        #

        self.flow_registry = FlowRegistry(self.config)

        #
        # Capacidad de reglas de los switches.
        #
        # Actualmente solamente existe la
        # abstraccion. Algoritmos futuros como
        # SWAY podran utilizarla.
        #

        self.rule_capacity = RuleCapacityManager()

        #
        # Hosts aprendidos dinamicamente.
        #

        self.hosts = HostManager()

        #
        # Administracion de reglas OpenFlow.
        #

        self.flows = FlowManager()

        #
        # Estado de decisiones de routing.
        #
        # Actualmente utilizado por algoritmos
        # con decision_policy = "sticky".
        #

        self.routing_state = RoutingState()

        #
        # Resultados.
        #

        results_dir = os.environ.get("RESULTS_DIR", "/workspace/results")

        self.results = ResultManager(results_dir)

        #
        # Logs iniciales.
        #

        self.logger.info("Configuracion del experimento: %s", config_path)

        self.logger.info("Algoritmo de ruteo: %s", self.routing_name)

        self.logger.info("Metrica de ruteo: %s", self.routing_metric)

        self.logger.info("Politica de decision: %s", self.decision_policy)

        self.logger.info("Modo de planificacion: %s", self.scheduling_mode)

    def _validate_routing_contract(self):

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

        datapath = ev.msg.datapath

        self.topology.register_datapath(datapath)

        self.flows.install_table_miss(datapath)

    @set_ev_cls(event.EventSwitchEnter)
    @set_ev_cls(event.EventLinkAdd)
    def topology_change_handler(self, ev):

        self.topology.update(self)

        self.logger.info("Grafo actual: %s", list(self.topology.graph.edges(data=True)))

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):

        msg = ev.msg

        datapath = msg.datapath

        dpid = datapath.id

        in_port = msg.match["in_port"]

        #
        # Decodificar paquete.
        #

        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        #
        # LLDP es utilizado por Ryu para
        # descubrir la topologia.
        #

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return

        #
        # Crear identidad generica del flujo.
        #

        flow = FlowIdentity.from_packet(pkt)

        if flow is None:
            return

        src = flow.source_mac

        dst = flow.destination_mac

        #
        # Aprender hosts solamente cuando
        # el paquete entra desde un puerto
        # que no conecta con otro switch.
        #

        if not self.topology.is_switch_port(dpid, in_port):
            learned = self.hosts.learn(src, dpid, in_port)

            if learned:
                self.logger.info(
                    "HOST: %s conectado a s%s puerto %s", src, dpid, in_port
                )

        #
        # Si todavia no conocemos el destino,
        # realizar flooding.
        #

        if not self.hosts.is_known(dst):
            self.flows.flood(msg)

            return

        #
        # Obtener switches de acceso.
        #

        src_switch = self.hosts.get_switch(src)

        dst_switch = self.hosts.get_switch(dst)

        #
        # Trafico no IP.
        #
        # ARP y otros protocolos auxiliares
        # NO deben alterar el estado de los
        # algoritmos experimentales.
        #
        # Se utiliza shortest path solamente
        # como forwarding auxiliar.
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
        # Resolver la especificacion declarativa
        # correspondiente al flujo, si existe.
        #
        # Los flujos inversos o auxiliares pueden
        # no tener una FlowSpecification asociada.
        #

        flow_spec = self.flow_registry.resolve(flow)

        #
        # Registrar flujo IP activo.
        #

        self.flow_registry.register_active_flow(flow, specification=flow_spec)

        #
        # Construir contexto generico que sera
        # entregado al algoritmo de routing.
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
        # El controlador actualmente solamente
        # ejecuta algoritmos per-flow.
        #
        # Esta condicion ya fue validada durante
        # __init__, pero se mantiene explicito el
        # comportamiento esperado en esta ruta.
        #

        if self.scheduling_mode != "per_flow":
            raise ValueError(
                "El controlador no puede ejecutar scheduling_mode '{}' mediante PacketIn".format(
                    self.scheduling_mode
                )
            )

        #
        # Obtener decision existente segun la
        # politica declarada por el algoritmo.
        #
        # Actualmente solamente soportamos sticky.
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
        # Una decision solamente es nueva
        # cuando no existe en RoutingState.
        #

        new_decision = decision is None

        #
        # Ejecutar el algoritmo solamente
        # para flujos que todavia no tienen
        # una decision.
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
            # Seguridad:
            # todo algoritmo debe devolver
            # RoutingDecision.
            #

            if decision is None:
                raise ValueError(
                    "El algoritmo '{}' no devolvio una RoutingDecision".format(
                        self.routing_name
                    )
                )

            #
            # Si el algoritmo rechazo el flujo,
            # no instalar reglas.
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
            # Una decision admitida debe tener
            # un camino valido.
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
        # Una decision recuperada del cache
        # tambien debe estar admitida.
        #

        if not decision.admitted:
            return

        path = decision.path

        cost = decision.cost

        #
        # Seguridad adicional para decisiones
        # recuperadas del estado de routing.
        #

        if path is None:
            raise ValueError(
                "El algoritmo '{}' devolvio una decision admitida sin path".format(
                    self.routing_name
                )
            )

        #
        # Log solamente para decisiones nuevas.
        #

        if new_decision:
            self.logger.info(
                "%s: NUEVA DECISION | mac=%s -> %s | ip=%s -> %s | eth_type=%s | proto=%s | sport=%s | dport=%s | s%s -> s%s | path=%s | cost=%s",
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
        # Registrar solamente decisiones nuevas
        # en routing_decisions.jsonl.
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
        # Registrar consumo de reglas solamente
        # para decisiones nuevas.
        #

        if new_decision:
            self.rule_capacity.register_path(path, flow)

        #
        # Instalar reglas OpenFlow.
        #

        self.flows.install_path(path, flow, self.topology, self.hosts)

        #
        # Reenviar el paquete actual.
        #

        self.flows.forward_packet(msg, path, flow, self.topology, self.hosts)
