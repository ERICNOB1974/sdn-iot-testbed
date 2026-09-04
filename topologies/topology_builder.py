from mininet.topo import Topo


class ConfigurableTopology(Topo):
    def __init__(self, topology_config, link_parameters=None):

        self.topology_config = topology_config

        self.link_parameters = link_parameters if link_parameters is not None else {}

        super().__init__()

    def build(self):

        nodes = {}

        for host_config in self.topology_config["hosts"]:
            name = host_config["name"]

            parameters = {}

            if "ip" in host_config:
                parameters["ip"] = host_config["ip"]

            if "mac" in host_config:
                parameters["mac"] = host_config["mac"]

            nodes[name] = self.addHost(name, **parameters)

        for switch_config in self.topology_config["switches"]:
            name = switch_config["name"]

            parameters = {}

            if "dpid" in switch_config:
                parameters["dpid"] = switch_config["dpid"]

            nodes[name] = self.addSwitch(name, **parameters)

        for link_config in self.topology_config["links"]:
            link_id = link_config["id"]

            source_name = link_config["source"]

            destination_name = link_config["destination"]

            parameters = self.link_parameters.get(link_id, {})

            self.addLink(nodes[source_name], nodes[destination_name], **parameters)
