from copy import deepcopy


class TopologyPlacementError(ValueError):
    pass


def validate_placement(placement, topology_definition):
    if not isinstance(placement, dict):
        raise TopologyPlacementError("El placement debe ser un mapping")

    if "hosts" not in placement:
        raise TopologyPlacementError(
            "El placement no contiene la seccion requerida 'hosts'"
        )

    if not isinstance(placement["hosts"], list):
        raise TopologyPlacementError("'hosts' del placement debe ser una lista")

    switch_names = {
        switch["name"]
        for switch in topology_definition["switches"]
    }

    existing_node_names = {
        host["name"]
        for host in topology_definition["hosts"]
    }

    existing_node_names.update(switch_names)

    host_names = []

    for host in placement["hosts"]:
        if not isinstance(host, dict):
            raise TopologyPlacementError(
                "Cada host del placement debe ser un mapping"
            )

        if "name" not in host:
            raise TopologyPlacementError(
                "Todos los hosts del placement deben tener un campo 'name'"
            )

        if "switch" not in host:
            raise TopologyPlacementError(
                "Todos los hosts del placement deben tener un campo 'switch'"
            )

        host_name = host["name"]
        switch_name = host["switch"]

        if not isinstance(host_name, str) or not host_name.strip():
            raise TopologyPlacementError(
                "Todos los hosts del placement deben tener un nombre valido"
            )

        if not isinstance(switch_name, str) or not switch_name.strip():
            raise TopologyPlacementError(
                "El host '{}' tiene un switch invalido".format(host_name)
            )

        if host_name in existing_node_names:
            raise TopologyPlacementError(
                "El nombre '{}' del placement ya existe en la topologia".format(
                    host_name
                )
            )

        if switch_name not in switch_names:
            raise TopologyPlacementError(
                "El host '{}' referencia un switch inexistente: '{}'".format(
                    host_name,
                    switch_name,
                )
            )

        host_names.append(host_name)

    if len(host_names) != len(set(host_names)):
        raise TopologyPlacementError(
            "Existen nombres de hosts duplicados en el placement"
        )


def apply_placement(topology_definition, placement):
    validate_placement(
        placement,
        topology_definition,
    )

    result = deepcopy(topology_definition)

    for host in placement["hosts"]:
        host_name = host["name"]
        switch_name = host["switch"]

        host_config = {
            key: value
            for key, value in host.items()
            if key != "switch"
        }

        result["hosts"].append(host_config)

        result["links"].append(
            {
                "id": "{}-{}".format(host_name, switch_name),
                "source": host_name,
                "destination": switch_name,
            }
        )

    return result
