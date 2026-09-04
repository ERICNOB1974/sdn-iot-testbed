class RoutingContext:
    def __init__(
        self,
        source,
        destination,
        source_mac=None,
        destination_mac=None,
        flow=None,
        flow_spec=None,
        network_state=None,
        active_flows=None,
        rule_capacity=None,
        metadata=None,
    ):

        self.source = source
        self.destination = destination

        self.source_mac = source_mac
        self.destination_mac = destination_mac

        self.flow = flow
        self.flow_spec = flow_spec

        self.network_state = network_state

        self.active_flows = active_flows if active_flows is not None else []

        self.rule_capacity = rule_capacity

        self.metadata = metadata if metadata is not None else {}
