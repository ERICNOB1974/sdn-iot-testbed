import argparse
from pathlib import Path

import yaml


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Genera un perfil de red a partir de una topologia declarativa."
    )

    parser.add_argument(
        "topology",
        help="Archivo YAML de definicion de topologia.",
    )

    parser.add_argument(
        "output",
        help="Archivo YAML de perfil de red a generar.",
    )

    parser.add_argument(
        "--name",
        help="Nombre del perfil. Por defecto se deriva del archivo de salida.",
    )

    parser.add_argument(
        "--delay-ms",
        type=float,
        required=True,
        help="Retardo asignado a cada enlace switch-switch.",
    )

    parser.add_argument(
        "--bandwidth-mbps",
        type=float,
        required=True,
        help="Ancho de banda asignado a cada enlace switch-switch.",
    )

    parser.add_argument(
        "--routing-cost",
        type=float,
        required=True,
        help="Costo de ruteo asignado a cada enlace switch-switch.",
    )

    return parser.parse_args()


def load_topology(path):
    with Path(path).open("r", encoding="utf-8") as file:
        topology = yaml.safe_load(file)

    if not isinstance(topology, dict):
        raise ValueError("La topologia debe ser un objeto YAML")

    for field in ("hosts", "switches", "links"):
        if field not in topology:
            raise ValueError(
                "La topologia no contiene el campo requerido '{}'".format(field)
            )

    return topology


def get_switch_names(topology):
    switch_names = set()

    for switch in topology["switches"]:
        name = switch.get("name")

        if not name:
            raise ValueError("Existe un switch sin nombre")

        if name in switch_names:
            raise ValueError(
                "Nombre de switch duplicado: {}".format(name)
            )

        switch_names.add(name)

    return switch_names


def generate_profile(
    topology,
    profile_name,
    delay_ms,
    bandwidth_mbps,
    routing_cost,
):
    switch_names = get_switch_names(topology)

    links = {}

    for link in topology["links"]:
        link_id = link.get("id")
        source = link.get("source")
        destination = link.get("destination")

        if not link_id:
            raise ValueError("Existe un enlace sin id")

        if not source or not destination:
            raise ValueError(
                "El enlace '{}' no tiene source/destination".format(link_id)
            )

        if source not in switch_names or destination not in switch_names:
            continue

        if link_id in links:
            raise ValueError(
                "ID de enlace duplicado: {}".format(link_id)
            )

        links[link_id] = {
            "delay_ms": delay_ms,
            "bandwidth_mbps": bandwidth_mbps,
            "routing_cost": routing_cost,
        }

    if not links:
        raise ValueError(
            "La topologia no contiene enlaces switch-switch"
        )

    return {
        "name": profile_name,
        "links": links,
    }


def write_profile(profile, path):
    output_path = Path(path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(
            profile,
            file,
            sort_keys=False,
            allow_unicode=True,
        )


def main():
    args = parse_arguments()

    topology = load_topology(args.topology)

    profile_name = args.name

    if profile_name is None:
        profile_name = Path(args.output).stem.replace("_", "-")

    profile = generate_profile(
        topology=topology,
        profile_name=profile_name,
        delay_ms=args.delay_ms,
        bandwidth_mbps=args.bandwidth_mbps,
        routing_cost=args.routing_cost,
    )

    write_profile(profile, args.output)

    print("Perfil generado: {}".format(args.output))
    print("Nombre: {}".format(profile["name"]))
    print("Enlaces switch-switch: {}".format(len(profile["links"])))


if __name__ == "__main__":
    main()
