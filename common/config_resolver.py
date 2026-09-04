"""
Valida la configuracion completa de un experimento. Agarra el archivo
YAML principal de un experimento y junta las distintas configuraciones que este
referencia, como por ejemeplo, la definicion de topologia, el perfil de condiciones de
red, perfil de trafico, identidades de los hosts y metrica utilizada por el algoritmo
de ruteo.

Valida que todas esas configuraciones sean validas antes de iniciar Mininet y el
controlador. Verifica: que la topologia tenga hosts, switches y enlaces validos, que no
existan nombres, DPID o enlaces duplicados, que los enlaces referenciados por el perfil
de red existan, que los valores numericos de red sean validos, que la metrica
seleccionada para routing exista en todos los enlaces, que las IP y MAC
asignadas a los hosts sean unicas, que los flujos de trafico utilicen hosts existentes,
que los parametros de aplicacion, QoS y trafico tengan valores validos, y, por ultimo,
que no se mezclen formatos incompatibles de definicion de trafico.

Una vez que todas las validaciones pasan, genera una unica configuracion
que contiene toda la informacion necesaria para ejecutar el experimento.

El resultado de este modulo se usa despues para generar resolved_config.yaml, que
actua como fuente comun de configuracion para Mininet, el runner y el controlador SDN.
"""

import math

from copy import deepcopy

from common.config_loader import load_experiment_config
from common.config_loader import load_traffic_profile
from common.config_loader import load_yaml
from common.host_identity import assign_host_identities


class ConfigurationError(Exception):
    pass


def validate_number(
    value,
    field_name,
    minimum=None,
    maximum=None,
    strictly_positive=False,
):

    if isinstance(value, bool) or not isinstance(
        value,
        (int, float),
    ):
        raise ConfigurationError("'{}' debe ser numerico".format(field_name))

    if not math.isfinite(value):
        raise ConfigurationError("'{}' debe ser un numero finito".format(field_name))

    if strictly_positive and value <= 0:
        raise ConfigurationError("'{}' debe ser mayor que 0".format(field_name))

    if minimum is not None and value < minimum:
        raise ConfigurationError(
            "'{}' debe ser mayor o igual que {}".format(
                field_name,
                minimum,
            )
        )

    if maximum is not None and value > maximum:
        raise ConfigurationError(
            "'{}' debe ser menor o igual que {}".format(
                field_name,
                maximum,
            )
        )


def validate_topology_definition(
    topology_definition,
):

    if not isinstance(
        topology_definition,
        dict,
    ):
        raise ConfigurationError("La definicion de topologia debe ser un mapping")

    required_sections = [
        "name",
        "hosts",
        "switches",
        "links",
    ]

    for section in required_sections:
        if section not in topology_definition:
            raise ConfigurationError(
                "La topologia no contiene la seccion requerida '{}'".format(section)
            )

    if not isinstance(
        topology_definition["hosts"],
        list,
    ):
        raise ConfigurationError("'hosts' debe ser una lista")

    if not isinstance(
        topology_definition["switches"],
        list,
    ):
        raise ConfigurationError("'switches' debe ser una lista")

    if not isinstance(
        topology_definition["links"],
        list,
    ):
        raise ConfigurationError("'links' debe ser una lista")

    host_names = []

    for host in topology_definition["hosts"]:
        if not isinstance(
            host,
            dict,
        ):
            raise ConfigurationError("Cada host debe ser un mapping")

        if "name" not in host:
            raise ConfigurationError("Todos los hosts deben tener un campo 'name'")

        host_name = host["name"]

        if (
            not isinstance(
                host_name,
                str,
            )
            or not host_name.strip()
        ):
            raise ConfigurationError("Todos los hosts deben tener un nombre valido")

        host_names.append(host_name)

    switch_names = []
    switch_dpids = []

    for switch in topology_definition["switches"]:
        if not isinstance(
            switch,
            dict,
        ):
            raise ConfigurationError("Cada switch debe ser un mapping")

        if "name" not in switch:
            raise ConfigurationError("Todos los switches deben tener un campo 'name'")

        switch_name = switch["name"]

        if (
            not isinstance(
                switch_name,
                str,
            )
            or not switch_name.strip()
        ):
            raise ConfigurationError("Todos los switches deben tener un nombre valido")

        if "dpid" not in switch:
            raise ConfigurationError("El switch '{}' no tiene DPID".format(switch_name))

        dpid = switch["dpid"]

        if (
            not isinstance(
                dpid,
                str,
            )
            or not dpid.strip()
        ):
            raise ConfigurationError(
                "El switch '{}' tiene un DPID invalido".format(switch_name)
            )

        switch_names.append(switch_name)

        switch_dpids.append(dpid)

    if len(host_names) != len(set(host_names)):
        raise ConfigurationError("Existen nombres de hosts duplicados")

    if len(switch_names) != len(set(switch_names)):
        raise ConfigurationError("Existen nombres de switches duplicados")

    if len(switch_dpids) != len(set(switch_dpids)):
        raise ConfigurationError("Existen DPID de switches duplicados")

    all_node_names = host_names + switch_names

    if len(all_node_names) != len(set(all_node_names)):
        raise ConfigurationError(
            "Un nombre de nodo esta utilizado tanto por un host como por un switch"
        )

    known_nodes = set(all_node_names)

    link_ids = []

    endpoint_pairs = set()

    for link in topology_definition["links"]:
        if not isinstance(
            link,
            dict,
        ):
            raise ConfigurationError("Cada enlace debe ser un mapping")

        if "id" not in link:
            raise ConfigurationError("Todos los enlaces deben tener un campo 'id'")

        link_id = link["id"]

        if (
            not isinstance(
                link_id,
                str,
            )
            or not link_id.strip()
        ):
            raise ConfigurationError("Todos los enlaces deben tener un ID valido")

        if "source" not in link:
            raise ConfigurationError("El enlace '{}' no tiene source".format(link_id))

        if "destination" not in link:
            raise ConfigurationError(
                "El enlace '{}' no tiene destination".format(link_id)
            )

        source = link["source"]

        destination = link["destination"]

        link_ids.append(link_id)

        if source not in known_nodes:
            raise ConfigurationError(
                "El enlace '{}' referencia un nodo source inexistente: '{}'".format(
                    link_id,
                    source,
                )
            )

        if destination not in known_nodes:
            raise ConfigurationError(
                "El enlace '{}' referencia un nodo destination inexistente: '{}'".format(
                    link_id,
                    destination,
                )
            )

        if source == destination:
            raise ConfigurationError(
                "El enlace '{}' conecta un nodo consigo mismo".format(link_id)
            )

        endpoint_pair = frozenset(
            (
                source,
                destination,
            )
        )

        if endpoint_pair in endpoint_pairs:
            raise ConfigurationError(
                "Existe mas de un enlace entre '{}' y '{}'".format(
                    source,
                    destination,
                )
            )

        endpoint_pairs.add(endpoint_pair)

    if len(link_ids) != len(set(link_ids)):
        raise ConfigurationError("Existen IDs de enlaces duplicados")


def validate_network_profile(
    topology_definition,
    network_profile,
):

    if not isinstance(
        network_profile,
        dict,
    ):
        raise ConfigurationError("El perfil de red debe ser un mapping")

    topology_link_ids = {link["id"] for link in topology_definition["links"]}

    network_links = network_profile.get(
        "links",
        {},
    )

    if not isinstance(
        network_links,
        dict,
    ):
        raise ConfigurationError("'links' del perfil de red debe ser un mapping")

    for link_id, conditions in network_links.items():
        if link_id not in topology_link_ids:
            raise ConfigurationError(
                "El perfil de red referencia un enlace inexistente: '{}'".format(
                    link_id
                )
            )

        if not isinstance(
            conditions,
            dict,
        ):
            raise ConfigurationError(
                "Las condiciones del enlace '{}' deben ser un mapping".format(link_id)
            )

        if "delay_ms" in conditions:
            validate_number(
                conditions["delay_ms"],
                "delay_ms del enlace '{}'".format(link_id),
                minimum=0,
            )

        if "loss_percent" in conditions:
            validate_number(
                conditions["loss_percent"],
                "loss_percent del enlace '{}'".format(link_id),
                minimum=0,
                maximum=100,
            )

        if "bandwidth_mbps" in conditions:
            validate_number(
                conditions["bandwidth_mbps"],
                "bandwidth_mbps del enlace '{}'".format(link_id),
                strictly_positive=True,
            )


def validate_routing_metric(
    experiment_config,
    topology_definition,
    network_profile,
):

    routing_config = experiment_config.get(
        "routing",
        {},
    )

    if "metric" not in routing_config:
        raise ConfigurationError("La configuracion de routing no define 'metric'")

    routing_metric = routing_config["metric"]

    if (
        not isinstance(
            routing_metric,
            str,
        )
        or not routing_metric.strip()
    ):
        raise ConfigurationError("La metrica de routing debe ser un string no vacio")

    switch_names = {switch["name"] for switch in topology_definition["switches"]}

    network_links = network_profile.get(
        "links",
        {},
    )

    for link in topology_definition["links"]:
        source = link["source"]

        destination = link["destination"]

        #
        # Solamente los enlaces switch-switch
        # forman parte del grafo de routing.
        #

        if source not in switch_names or destination not in switch_names:
            continue

        link_id = link["id"]

        if link_id not in network_links:
            raise ConfigurationError(
                "El enlace switch-switch '{}' no esta definido en el perfil de red".format(
                    link_id
                )
            )

        conditions = network_links[link_id]

        if routing_metric not in conditions:
            raise ConfigurationError(
                "La metrica de routing '{}' no esta definida para el enlace '{}'".format(
                    routing_metric,
                    link_id,
                )
            )

        metric_value = conditions[routing_metric]

        validate_number(
            metric_value,
            "metrica de routing '{}' del enlace '{}'".format(
                routing_metric,
                link_id,
            ),
            minimum=0,
        )


def validate_host_identities(
    hosts,
):

    ips = []
    macs = []

    for host in hosts:
        if "ip" not in host:
            raise ConfigurationError(
                "El host '{}' no tiene IP resuelta".format(host["name"])
            )

        if "mac" not in host:
            raise ConfigurationError(
                "El host '{}' no tiene MAC resuelta".format(host["name"])
            )

        ips.append(host["ip"])

        macs.append(host["mac"].lower())

    if len(ips) != len(set(ips)):
        raise ConfigurationError("Existen direcciones IP de hosts duplicadas")

    if len(macs) != len(set(macs)):
        raise ConfigurationError("Existen direcciones MAC de hosts duplicadas")


def validate_application_config(
    application,
    flow_id,
):

    if application is None:
        return

    if not isinstance(
        application,
        dict,
    ):
        raise ConfigurationError(
            "El campo 'application' del flujo '{}' debe ser un mapping".format(flow_id)
        )

    if "type" in application:
        application_type = application["type"]

        if (
            not isinstance(
                application_type,
                str,
            )
            or not application_type.strip()
        ):
            raise ConfigurationError(
                "application.type del flujo '{}' debe ser un string no vacio".format(
                    flow_id
                )
            )

    if "class" in application:
        application_class = application["class"]

        if (
            not isinstance(
                application_class,
                str,
            )
            or not application_class.strip()
        ):
            raise ConfigurationError(
                "application.class del flujo '{}' debe ser un string no vacio".format(
                    flow_id
                )
            )


def validate_qos_config(
    qos,
    flow_id,
):

    if qos is None:
        return

    if not isinstance(
        qos,
        dict,
    ):
        raise ConfigurationError(
            "El campo 'qos' del flujo '{}' debe ser un mapping".format(flow_id)
        )

    non_negative_fields = [
        "max_delay_ms",
        "max_jitter_ms",
    ]

    for field in non_negative_fields:
        if field in qos:
            validate_number(
                qos[field],
                "qos.{} del flujo '{}'".format(
                    field,
                    flow_id,
                ),
                minimum=0,
            )

    if "max_loss_percent" in qos:
        validate_number(
            qos["max_loss_percent"],
            "qos.max_loss_percent del flujo '{}'".format(flow_id),
            minimum=0,
            maximum=100,
        )

    positive_fields = [
        "min_bandwidth_mbps",
        "min_throughput_mbps",
    ]

    for field in positive_fields:
        if field in qos:
            validate_number(
                qos[field],
                "qos.{} del flujo '{}'".format(
                    field,
                    flow_id,
                ),
                strictly_positive=True,
            )


def validate_flow_traffic_config(
    traffic,
    flow_id,
):

    if traffic is None:
        return

    if not isinstance(
        traffic,
        dict,
    ):
        raise ConfigurationError(
            "El campo 'traffic' del flujo '{}' debe ser un mapping".format(flow_id)
        )

    if "ip_protocol" in traffic:
        ip_protocol = traffic["ip_protocol"]

        if isinstance(
            ip_protocol,
            bool,
        ) or not isinstance(
            ip_protocol,
            int,
        ):
            raise ConfigurationError(
                "traffic.ip_protocol del flujo '{}' debe ser entero".format(flow_id)
            )

        if not 0 <= ip_protocol <= 255:
            raise ConfigurationError(
                "traffic.ip_protocol del flujo '{}' debe estar entre 0 y 255".format(
                    flow_id
                )
            )

    for field in [
        "source_port",
        "destination_port",
    ]:
        if field not in traffic:
            continue

        port = traffic[field]

        if isinstance(
            port,
            bool,
        ) or not isinstance(
            port,
            int,
        ):
            raise ConfigurationError(
                "traffic.{} del flujo '{}' debe ser entero".format(
                    field,
                    flow_id,
                )
            )

        if not 1 <= port <= 65535:
            raise ConfigurationError(
                "traffic.{} del flujo '{}' debe estar entre 1 y 65535".format(
                    field,
                    flow_id,
                )
            )

    if "packet_size_bytes" in traffic:
        validate_number(
            traffic["packet_size_bytes"],
            "traffic.packet_size_bytes del flujo '{}'".format(flow_id),
            strictly_positive=True,
        )

    if "rate_pps" in traffic:
        validate_number(
            traffic["rate_pps"],
            "traffic.rate_pps del flujo '{}'".format(flow_id),
            strictly_positive=True,
        )

    if "start_seconds" in traffic:
        validate_number(
            traffic["start_seconds"],
            "traffic.start_seconds del flujo '{}'".format(flow_id),
            minimum=0,
        )


def validate_flow_config(
    flow,
    index,
    host_names,
):

    if not isinstance(
        flow,
        dict,
    ):
        raise ConfigurationError("El flujo {} debe ser un mapping".format(index))

    if "id" not in flow:
        raise ConfigurationError("El flujo {} no define 'id'".format(index))

    flow_id = flow["id"]

    if (
        not isinstance(
            flow_id,
            str,
        )
        or not flow_id.strip()
    ):
        raise ConfigurationError("El flujo {} tiene un 'id' invalido".format(index))

    if "source" not in flow:
        raise ConfigurationError("El flujo '{}' no define 'source'".format(flow_id))

    if "destination" not in flow:
        raise ConfigurationError(
            "El flujo '{}' no define 'destination'".format(flow_id)
        )

    source = flow["source"]

    destination = flow["destination"]

    if source not in host_names:
        raise ConfigurationError(
            "El source '{}' del flujo '{}' no existe como host".format(
                source,
                flow_id,
            )
        )

    if destination not in host_names:
        raise ConfigurationError(
            "El destination '{}' del flujo '{}' no existe como host".format(
                destination,
                flow_id,
            )
        )

    if source == destination:
        raise ConfigurationError(
            "El flujo '{}' tiene el mismo host como source y destination".format(
                flow_id
            )
        )

    if "priority" in flow:
        priority = flow["priority"]

        if isinstance(
            priority,
            bool,
        ) or not isinstance(
            priority,
            int,
        ):
            raise ConfigurationError(
                "La prioridad del flujo '{}' debe ser un entero".format(flow_id)
            )

        if priority < 0:
            raise ConfigurationError(
                "La prioridad del flujo '{}' debe ser mayor o igual que 0".format(
                    flow_id
                )
            )

    validate_application_config(
        flow.get("application"),
        flow_id,
    )

    validate_qos_config(
        flow.get("qos"),
        flow_id,
    )

    validate_flow_traffic_config(
        flow.get("traffic"),
        flow_id,
    )

    #
    # Campos utilizados actualmente por ping.
    #

    if "count" in flow:
        count = flow["count"]

        if (
            isinstance(
                count,
                bool,
            )
            or not isinstance(
                count,
                int,
            )
            or count <= 0
        ):
            raise ConfigurationError(
                "'count' del flujo '{}' debe ser un entero mayor que 0".format(flow_id)
            )

    if "interval" in flow:
        validate_number(
            flow["interval"],
            "interval del flujo '{}'".format(flow_id),
            strictly_positive=True,
        )


def validate_traffic_profile(
    traffic_profile,
    resolved_hosts,
):

    if not isinstance(
        traffic_profile,
        dict,
    ):
        raise ConfigurationError("El perfil de trafico debe ser un mapping")

    host_names = {host["name"] for host in resolved_hosts}

    flows = traffic_profile.get("flows")

    #
    # Evitar mezclar el formato antiguo
    # con el formato moderno.
    #

    if flows is not None and (
        "source" in traffic_profile or "destination" in traffic_profile
    ):
        raise ConfigurationError(
            "El perfil de trafico no puede mezclar 'flows' con 'source/destination' de nivel superior"
        )

    #
    # Formato moderno de multiples flujos.
    #

    if flows is not None:
        if not isinstance(
            flows,
            list,
        ):
            raise ConfigurationError("'flows' debe ser una lista")

        if len(flows) == 0:
            raise ConfigurationError(
                "El perfil de trafico contiene una lista 'flows' vacia"
            )

        flow_ids = []

        for index, flow in enumerate(
            flows,
            start=1,
        ):
            validate_flow_config(
                flow,
                index,
                host_names,
            )

            flow_ids.append(flow["id"])

        if len(flow_ids) != len(set(flow_ids)):
            raise ConfigurationError("Existen IDs de flujos duplicados")

        return

    #
    # Compatibilidad con el formato antiguo
    # de un unico flujo.
    #

    if "source" not in traffic_profile:
        raise ConfigurationError("El perfil de trafico no define 'source' ni 'flows'")

    if "destination" not in traffic_profile:
        raise ConfigurationError("El perfil de trafico no define 'destination'")

    source = traffic_profile["source"]

    destination = traffic_profile["destination"]

    if source not in host_names:
        raise ConfigurationError(
            "El source de trafico '{}' no existe como host".format(source)
        )

    if destination not in host_names:
        raise ConfigurationError(
            "El destination de trafico '{}' no existe como host".format(destination)
        )

    if source == destination:
        raise ConfigurationError(
            "El source y destination del trafico no pueden ser el mismo host"
        )


def resolve_experiment_config(
    experiment_config_path,
):

    experiment_config = load_experiment_config(experiment_config_path)

    resolved = deepcopy(experiment_config)

    topology_path = experiment_config["topology"]["definition"]

    topology_definition = load_yaml(topology_path)

    validate_topology_definition(topology_definition)

    network_profile_path = experiment_config["network"]["profile"]

    network_profile = load_yaml(network_profile_path)

    validate_network_profile(
        topology_definition,
        network_profile,
    )

    validate_routing_metric(
        experiment_config,
        topology_definition,
        network_profile,
    )

    traffic_profile_path = experiment_config["traffic"]["profile"]

    traffic_profile = load_traffic_profile(traffic_profile_path)

    resolved_hosts = assign_host_identities(topology_definition["hosts"])

    validate_host_identities(resolved_hosts)

    validate_traffic_profile(
        traffic_profile,
        resolved_hosts,
    )

    resolved["topology"] = {
        "definition": topology_path,
        "name": topology_definition["name"],
        "hosts": resolved_hosts,
        "switches": topology_definition["switches"],
        "links": topology_definition["links"],
    }

    resolved["network"] = {
        "profile": network_profile_path,
        "name": network_profile.get(
            "name",
            "unnamed",
        ),
        "links": network_profile.get(
            "links",
            {},
        ),
    }

    resolved["traffic"]["config"] = traffic_profile

    return resolved
