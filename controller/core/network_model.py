class NetworkModel:
    def __init__(self, config):

        self.config = config

        self.routing_metric = config["routing"]["metric"]

        self.switch_name_by_dpid = {}

        self.dpid_by_switch_name = {}

        self.link_id_by_nodes = {}

        self.network_links = config["network"].get("links", {})

        self._build_switch_maps()

        self._build_link_maps()

    def _build_switch_maps(self):

        for switch in self.config["topology"]["switches"]:
            name = switch["name"]

            dpid_text = switch["dpid"]

            dpid = int(dpid_text, 16)

            self.switch_name_by_dpid[dpid] = name

            self.dpid_by_switch_name[name] = dpid

    def _build_link_maps(self):

        switch_names = set(self.dpid_by_switch_name.keys())

        for link in self.config["topology"]["links"]:
            source = link["source"]

            destination = link["destination"]

            #
            # Para routing solamente interesan
            # enlaces switch-switch.
            #

            if source not in switch_names or destination not in switch_names:
                continue

            link_id = link["id"]

            self.link_id_by_nodes[(source, destination)] = link_id

            self.link_id_by_nodes[(destination, source)] = link_id

    def get_switch_name(self, dpid):

        return self.switch_name_by_dpid.get(dpid)

    def get_switch_dpid(self, name):

        return self.dpid_by_switch_name.get(name)

    def get_link_id(self, source_dpid, destination_dpid):

        source_name = self.get_switch_name(source_dpid)

        destination_name = self.get_switch_name(destination_dpid)

        if source_name is None or destination_name is None:
            return None

        return self.link_id_by_nodes.get((source_name, destination_name))

    def get_link_conditions(self, source_dpid, destination_dpid):

        link_id = self.get_link_id(source_dpid, destination_dpid)

        if link_id is None:
            return {}

        return self.network_links.get(link_id, {})

    def get_routing_cost(self, source_dpid, destination_dpid):

        conditions = self.get_link_conditions(source_dpid, destination_dpid)

        if self.routing_metric not in conditions:
            raise KeyError(
                "La metrica '{}' no esta definida para el enlace {} -> {}".format(
                    self.routing_metric, source_dpid, destination_dpid
                )
            )

        return conditions[self.routing_metric]
