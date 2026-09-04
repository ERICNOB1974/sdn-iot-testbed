from traffic.result import TrafficResult


def run_single_ping(net, flow):

    source = flow["source"]
    destination = flow["destination"]

    count = flow.get("count", 20)

    interval = flow.get("interval", 0.2)

    source_host = net.get(source)

    destination_host = net.get(destination)

    destination_ip = destination_host.IP()

    command = "ping -c {} -i {} {}".format(count, interval, destination_ip)

    return source_host.cmd(command)


def run_ping(net, config):

    flows = config.get("flows")

    if flows is None:
        flows = [
            {
                "id": "ping-{}-{}".format(config["source"], config["destination"]),
                "source": config["source"],
                "destination": config["destination"],
                "count": config.get("count", 20),
                "interval": config.get("interval", 0.2),
            }
        ]

    outputs = []

    flow_metadata = []

    for flow in flows:
        flow_id = flow.get("id", "{}-{}".format(flow["source"], flow["destination"]))

        output = run_single_ping(net, flow)

        outputs.append("===== FLOW {} =====\n{}\n".format(flow_id, output))

        flow_metadata.append(
            {
                "id": flow_id,
                "source": flow["source"],
                "destination": flow["destination"],
                "count": flow.get("count", 20),
                "interval_seconds": flow.get("interval", 0.2),
            }
        )

    return TrafficResult(
        raw_output="\n".join(outputs), metadata={"type": "ping", "flows": flow_metadata}
    )
