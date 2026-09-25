import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


GRAPHML_NAMESPACE = "http://graphml.graphdrawing.org/xmlns"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Convierte una topologia GraphML de Topology Zoo al formato del testbed."
    )

    parser.add_argument(
        "input",
        help="Archivo GraphML de Topology Zoo.",
    )

    parser.add_argument(
        "output",
        help="Archivo YAML de salida.",
    )

    parser.add_argument(
        "--internal-only",
        action="store_true",
        help="Importa solamente nodos con Internal=1.",
    )

    return parser.parse_args()


def load_graphml(path):
    tree = ET.parse(path)

    root = tree.getroot()

    namespace = {"g": GRAPHML_NAMESPACE}

    keys = {}

    for key in root.findall("g:key", namespace):
        key_id = key.attrib["id"]
        attribute_name = key.attrib.get("attr.name")

        keys[key_id] = attribute_name

    graph = root.find("g:graph", namespace)

    if graph is None:
        raise ValueError("El archivo no contiene un elemento graph")

    return graph, keys, namespace


def get_data(element, keys, namespace):
    result = {}

    for data in element.findall("g:data", namespace):
        key_id = data.attrib["key"]
        name = keys.get(key_id, key_id)

        result[name] = data.text

    return result


def convert_graphml(path, internal_only=False):
    graph, keys, namespace = load_graphml(path)

    graph_data = get_data(graph, keys, namespace)

    topology_name = graph_data.get("label")

    if topology_name is None:
        topology_name = Path(path).stem

    topology_name = topology_name.strip().lower()

    selected_nodes = {}

    for node in graph.findall("g:node", namespace):
        node_id = node.attrib["id"]

        data = get_data(node, keys, namespace)

        internal = data.get("Internal")

        if internal_only and internal != "1":
            continue

        selected_nodes[node_id] = data

    switches = []

    node_to_switch = {}

    for index, node_id in enumerate(selected_nodes.keys(), start=1):
        switch_name = "s{}".format(index)

        node_to_switch[node_id] = switch_name

        switch = {
            "name": switch_name,
            "dpid": "{:016x}".format(index),
            "metadata": {
                "topology_zoo_id": node_id,
            },
        }

        data = selected_nodes[node_id]

        if data.get("label") is not None:
            switch["metadata"]["label"] = data["label"]

        if data.get("Country") is not None:
            switch["metadata"]["country"] = data["Country"]

        if data.get("Latitude") is not None:
            switch["metadata"]["latitude"] = float(data["Latitude"])

        if data.get("Longitude") is not None:
            switch["metadata"]["longitude"] = float(data["Longitude"])

        if data.get("Internal") is not None:
            switch["metadata"]["internal"] = int(data["Internal"])

        switches.append(switch)

    links = []

    link_index = 1

    for edge in graph.findall("g:edge", namespace):
        source_id = edge.attrib["source"]
        destination_id = edge.attrib["target"]

        if source_id not in selected_nodes:
            continue

        if destination_id not in selected_nodes:
            continue

        source = node_to_switch[source_id]
        destination = node_to_switch[destination_id]

        links.append(
            {
                "id": "{}-{}".format(source, destination),
                "source": source,
                "destination": destination,
            }
        )

        link_index += 1

    topology = {
        "name": topology_name,
        "hosts": [],
        "switches": switches,
        "links": links,
    }

    return topology


def main():
    args = parse_arguments()

    topology = convert_graphml(
        args.input,
        internal_only=args.internal_only,
    )

    output_path = Path(args.output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            topology,
            file,
            sort_keys=False,
            allow_unicode=True,
        )

    print("Topologia generada: {}".format(output_path))
    print("Switches: {}".format(len(topology["switches"])))
    print("Links: {}".format(len(topology["links"])))


if __name__ == "__main__":
    main()
