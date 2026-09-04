def build_mininet_link_parameters(network_config):

    result = {}

    for link_id, conditions in network_config.get("links", {}).items():
        parameters = {}

        if "delay_ms" in conditions:
            parameters["delay"] = "{}ms".format(conditions["delay_ms"])

        if "bandwidth_mbps" in conditions:
            parameters["bw"] = conditions["bandwidth_mbps"]

        if "loss_percent" in conditions:
            parameters["loss"] = conditions["loss_percent"]

        if parameters:
            result[link_id] = parameters

    return result
