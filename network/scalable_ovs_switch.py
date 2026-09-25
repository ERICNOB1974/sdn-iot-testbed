# Open vSwitch preparado para topologias con muchas interfaces por switch.

from mininet.node import OVSSwitch


class ScalableOVSSwitch(OVSSwitch):
    def __init__(self, name, **params):

        params["batch"] = False

        super().__init__(name, **params)

    def _run_ovs_command(self, command, description):

        # Ejecutar un comando ovs-vsctl y comprobar explicitamente
        # su codigo de salida.
        #
        # Node.cmd() devuelve solamente la salida de texto, entonces
        # agregamos un marcador para recuperar tambien el exit status

        marker = "__OVS_EXIT_CODE__"

        output = self.cmd("{} 2>&1; echo {}$?".format(command, marker))

        lines = output.rstrip().splitlines()

        if not lines:
            raise RuntimeError(
                "No se pudo determinar el resultado de OVS durante: {}".format(
                    description
                )
            )

        status_line = lines[-1]

        if not status_line.startswith(marker):
            raise RuntimeError(
                "Respuesta inesperada de OVS durante '{}': {}".format(
                    description, output
                )
            )

        exit_code = int(status_line[len(marker) :])

        command_output = "\n".join(lines[:-1]).strip()

        if exit_code != 0:
            raise RuntimeError(
                "Error OVS durante '{}'. Codigo: {}. Salida: {}".format(
                    description, exit_code, command_output
                )
            )

        return command_output

    def start(self, controllers):

        if self.inNamespace:
            raise RuntimeError(
                "OVS kernel switch no puede ejecutarse dentro de un namespace"
            )

        # Validar que el DPID sea hexadecimal.

        int(self.dpid, 16)

        # Eliminar cualquier bridge anterior con el mismo nombre.

        self._run_ovs_command(
            "ovs-vsctl --if-exists del-br {}".format(self.name),
            "eliminar bridge anterior {}".format(self.name),
        )

        # Crear primero el bridge vacio.

        self._run_ovs_command(
            "ovs-vsctl add-br {}".format(self.name), "crear bridge {}".format(self.name)
        )

        # Aplicar las opciones normales utilizadas por OVSSwitch:

        self._run_ovs_command(
            "ovs-vsctl set Bridge {} {}".format(self.name, self.bridgeOpts().strip()),
            "configurar bridge {}".format(self.name),
        )

        # Configurar los controladores OpenFlow asociados al switch.
        # En nuestro banco de pruebas existe un unico RemoteController,
        # pero se permite una lista porque asi es el contrato de Mininet.

        controller_targets = []

        for controller in controllers:
            target = "{}:{}:{}".format(
                controller.protocol, controller.IP(), controller.port
            )

            controller_targets.append(target)

        # Agregar tambien un controlador pasivo si Mininet hubiera
        # configurado listenPort.

        if self.listenPort:
            controller_targets.append("ptcp:{}".format(self.listenPort))

        if controller_targets:
            self._run_ovs_command(
                "ovs-vsctl set-controller {} {}".format(
                    self.name, " ".join(controller_targets)
                ),
                "configurar controlador de {}".format(self.name),
            )

        # Agregar cada interfaz individualmente.

        for intf in self.intfList():
            port = self.ports[intf]

            if not port:
                continue

            # Una interfaz que ya posee IP no corresponde a un
            # puerto normal de datos del switch.

            if intf.IP():
                continue

            command = ("ovs-vsctl --may-exist add-port {} {}{}").format(
                self.name, intf, self.intfOpts(intf)
            )

            self._run_ovs_command(
                command, "agregar interfaz {} a {}".format(intf, self.name)
            )

        for intf in self.intfList():
            if self.ports[intf]:
                self.TCReapply(intf)
