from network.mininet_profile import build_mininet_link_parameters
from topologies.topology_builder import ConfigurableTopology


def load_topology(resolved_config):

    topology_config = resolved_config["topology"]

    network_config = resolved_config["network"]

    link_parameters = build_mininet_link_parameters(network_config)

    return ConfigurableTopology(topology_config, link_parameters=link_parameters)
