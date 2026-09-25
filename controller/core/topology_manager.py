import networkx as nx

from ryu.topology.api import get_switch
from ryu.topology.api import get_link


class TopologyManager:
    def __init__(self, network_model):

        self.network_model = network_model

        #
        # Grafo dirigido utilizado para routing.
        #
        # Cada enlace fisico switch-switch aparece en ambas
        # direcciones cuando Ryu termina de descubrirlo.
        #

        self.graph = nx.DiGraph()

        #
        # DPID -> datapath Ryu.
        #

        self.datapaths = {}

    def register_datapath(self, datapath):

        self.datapaths[datapath.id] = datapath

    def update(self, app):

        switches = get_switch(app, None)

        links = get_link(app, None)

        #
        # Actualizar switches conocidos.
        #

        for switch in switches:
            dpid = switch.dp.id

            self.graph.add_node(dpid)

            self.datapaths[dpid] = switch.dp

        #
        # Actualizar enlaces descubiertos.
        #

        for link in links:
            src = link.src.dpid

            dst = link.dst.dpid

            link_id = self.network_model.get_link_id(src, dst)

            cost = self.network_model.get_routing_cost(src, dst)

            conditions = self.network_model.get_link_conditions(src, dst)

            self.graph.add_edge(
                src,
                dst,
                weight=cost,
                port=link.src.port_no,
                link_id=link_id,
                metrics=dict(conditions),
            )

    def is_switch_port(self, dpid, port):

        #
        # Determina si un puerto conecta este switch
        # con otro switch conocido por la topologia.
        #

        for _, _, data in self.graph.out_edges(dpid, data=True):
            if data["port"] == port:
                return True

        return False

    def get_switch_ports(self, dpid):

        #
        # Devuelve todos los puertos del switch que
        # conectan con otros switches.
        #

        ports = set()

        for _, _, data in self.graph.out_edges(dpid, data=True):
            ports.add(data["port"])

        return ports

    def get_output_port(self, current_switch, next_switch):

        return self.graph[current_switch][next_switch]["port"]

    def get_discovered_link_ids(self):

        #
        # Obtener los enlaces fisicos switch-switch
        # que Ryu ya descubrio.
        #
        # Como el grafo es dirigido, el mismo link_id
        # puede aparecer dos veces. El set elimina
        # esos duplicados.
        #

        discovered = set()

        for _, _, data in self.graph.edges(data=True):
            link_id = data.get("link_id")

            if link_id is not None:
                discovered.add(link_id)

        return discovered

    def is_complete(self):

        #
        # Verifica que Ryu haya descubierto todos
        # los enlaces switch-switch declarados
        # originalmente en la configuracion.
        #
        # Esto evita comenzar a aprender hosts
        # mientras la topologia todavia esta
        # incompleta.
        #

        expected = self.network_model.get_switch_link_ids()

        discovered = self.get_discovered_link_ids()

        return expected == discovered

    def build_flooding_tree(self):

        #
        # Construye un spanning tree utilizado
        # EXCLUSIVAMENTE para flooding.
        #
        # El grafo completo sigue estando disponible
        # para Dijkstra, SWAY, AQRA, MINA, etc.
        #

        tree_ports = {dpid: set() for dpid in self.graph.nodes()}

        if self.graph.number_of_nodes() == 0:
            return tree_ports

        #
        # Convertimos el grafo dirigido de routing
        # en un grafo no dirigido.
        #

        undirected = nx.Graph()

        undirected.add_nodes_from(self.graph.nodes())

        for src, dst in self.graph.edges():
            undirected.add_edge(src, dst)

        if undirected.number_of_edges() == 0:
            return tree_ports

        #
        # Elegimos de forma determinista el switch
        # con menor DPID como raiz.
        #
        # bfs_tree produce un arbol sin ciclos.
        #

        root = min(undirected.nodes())

        tree = nx.bfs_tree(undirected, root)

        #
        # Para cada enlace perteneciente al arbol,
        # almacenar los puertos correspondientes
        # en ambas direcciones.
        #

        for src, dst in tree.edges():
            if self.graph.has_edge(src, dst):
                tree_ports[src].add(self.get_output_port(src, dst))

            if self.graph.has_edge(dst, src):
                tree_ports[dst].add(self.get_output_port(dst, src))

        return tree_ports

    def get_neighbor_by_port(self, dpid, port):

        #
        # Busca a que switch vecino conduce
        # un determinado puerto.
        #
        # Ejemplo:
        #
        # s1 puerto 101 -> s2
        #

        for _, destination, data in self.graph.out_edges(dpid, data=True):
            if data.get("port") == port:
                return destination

        return None

    def get_link_by_port(self, dpid, port):

        #
        # Devuelve el enlace dirigido asociado
        # a un puerto de salida.
        #
        # Ejemplo:
        #
        # (s1, puerto 101)
        #
        # devuelve:
        #
        # (1, 2)
        #

        destination = self.get_neighbor_by_port(dpid, port)

        if destination is None:
            return None

        return (dpid, destination)
