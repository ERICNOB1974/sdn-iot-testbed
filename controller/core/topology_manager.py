import networkx as nx

from ryu.topology.api import get_switch
from ryu.topology.api import get_link


class TopologyManager:
    def __init__(self, network_model):

        self.network_model = network_model

        self.graph = nx.DiGraph()

        self.datapaths = {}

    def register_datapath(self, datapath):

        self.datapaths[datapath.id] = datapath

    def update(self, app):

        switches = get_switch(app, None)

        links = get_link(app, None)

        for switch in switches:
            dpid = switch.dp.id

            self.graph.add_node(dpid)

            self.datapaths[dpid] = switch.dp

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

        for _, _, data in self.graph.out_edges(dpid, data=True):
            if data["port"] == port:
                return True

        return False

    def get_output_port(self, current_switch, next_switch):

        return self.graph[current_switch][next_switch]["port"]
