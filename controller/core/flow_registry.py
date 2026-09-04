from controller.core.flow_specification import FlowSpecification


class FlowRegistry:
    def __init__(self, config):

        self.specifications = []
        self.active_flows = {}

        self._load_specifications(config)

    def _load_specifications(self, config):

        hosts = {host["name"]: host for host in config["topology"]["hosts"]}

        traffic_config = config.get("traffic", {}).get("config", {})

        flows = traffic_config.get("flows", [])

        for flow_config in flows:
            source = flow_config["source"]
            destination = flow_config["destination"]

            source_host = hosts[source]

            destination_host = hosts[destination]

            specification = FlowSpecification(
                flow_id=flow_config["id"],
                source=source,
                destination=destination,
                source_ip=source_host["ip"],
                destination_ip=destination_host["ip"],
                application=flow_config.get("application"),
                priority=flow_config.get("priority"),
                qos=flow_config.get("qos"),
                traffic=flow_config.get("traffic"),
                metadata=flow_config.get("metadata"),
            )

            self.specifications.append(specification)

    def resolve(self, flow):

        for specification in self.specifications:
            if specification.matches(flow):
                return specification

        return None

    def register_active_flow(self, flow, specification=None):

        self.active_flows[flow.key()] = {"flow": flow, "specification": specification}

    def get_active_flows(self):

        return list(self.active_flows.values())

    def get_specifications(self):

        return list(self.specifications)
