"""
Junta las reglas Openflow instaladas en los switches. Consulta a cada switch
y obtiene el contenido actual de sus tablas usando ovs-ofctl.

No modifica las reglas de los switches ni toma decisiones de ruteo.
Su única responsabilidad es devolver como texto el estado de las tablas
Openflow para que el runner pueda almacenarlo como parte de los resultados
del experimento.
"""


def collect_flows(net, config):
    """
    Recorre todos los switches y saca las reglas Openflow actuales que hay en cada uno.
    Devuelve un string con las tablas de flujo de todos los switches.
    """

    # Acumula en un único texto la información de todos los switches
    result = ""

    for switch in net.switches:
        # Agregar un encabezado para identificar a qué switch pertenecen las reglas
        result += "\n\nSWITCH {}\n\n".format(switch.name)

        # Comando que consulta la tabla OpenFlow
        command = "ovs-ofctl -O OpenFlow13 dump-flows {}".format(switch.name)

        # Ejecutar el comando dentro del entorno del switch
        result += switch.cmd(command)

        result += "\n"

    return result
