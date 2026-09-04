# Cada host debe tener una direccion IP y una direccion MAC. Este modulo
# genera automaticamente un valor determinista a partir de la posicion del
# host en la lista.
#
# De esta forma, los hosts poseen siempre una IP y una MAC definidas.


def assign_host_identities(hosts):

    result = []

    # Recorrer los hosts de la topologia.

    for index, host in enumerate(hosts, start=1):
        # Crear una copia de la configuracion original

        host_config = dict(host)

        # Si el host no tiene una direccion IP definida,
        # asignar automaticamente una dentro de la red 10.0.0.0/24.

        if "ip" not in host_config:
            host_config["ip"] = "10.0.0.{}".format(index)

        # Si el host no tiene una direccion MAC definida,
        # generar una usando el indice del host.

        if "mac" not in host_config:
            host_config["mac"] = "00:00:00:00:00:{:02x}".format(index)

        result.append(host_config)

    return result
