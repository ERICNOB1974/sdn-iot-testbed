class FlowSpecification:
    def __init__(
        self,
        flow_id,
        source,
        destination,
        source_ip=None,
        destination_ip=None,
        application=None,
        priority=None,
        qos=None,
        traffic=None,
        metadata=None,
    ):

        self.flow_id = flow_id

        self.source = source
        self.destination = destination

        self.source_ip = source_ip
        self.destination_ip = destination_ip

        self.application = application if application is not None else {}

        self.priority = priority

        self.qos = qos if qos is not None else {}

        self.traffic = traffic if traffic is not None else {}

        self.metadata = metadata if metadata is not None else {}

    def matches(self, flow):

        if flow.source_ip is None:
            return False

        if flow.destination_ip is None:
            return False

        if flow.source_ip != self.source_ip:
            return False

        if flow.destination_ip != self.destination_ip:
            return False

        source_port = self.traffic.get("source_port")

        destination_port = self.traffic.get("destination_port")

        ip_protocol = self.traffic.get("ip_protocol")

        if source_port is not None and flow.source_port != source_port:
            return False

        if destination_port is not None and flow.destination_port != destination_port:
            return False

        if ip_protocol is not None and flow.ip_protocol != ip_protocol:
            return False

        return True

    def to_dict(self):

        return {
            "flow_id": self.flow_id,
            "source": self.source,
            "destination": self.destination,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "application": self.application,
            "priority": self.priority,
            "qos": self.qos,
            "traffic": self.traffic,
            "metadata": self.metadata,
        }
