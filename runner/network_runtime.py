#
# Este modulo administra el ciclo de vida de la red Mininet utilizada
# durante un experimento.
#
# Recibe una topologia ya construida, crea la instancia de Mininet,
# registra el controlador remoto, inicia la infraestructura y verifica
# que todos los switches Open vSwitch hayan sido creados correctamente.
#

from functools import partial

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import RemoteController

from network.scalable_ovs_switch import ScalableOVSSwitch


class NetworkRuntime:
    OPENFLOW_PROTOCOLS = {"1.3": "OpenFlow13"}

    def __init__(self, topology, controller_config, openflow_version):

        self.topology = topology

        self.controller_config = controller_config

        self.openflow_version = openflow_version

        self.net = None

    def start(self):

        #
        # Traducir la version declarada por el experimento al nombre
        # utilizado por Open vSwitch.
        #

        protocol = self.OPENFLOW_PROTOCOLS.get(self.openflow_version)

        if protocol is None:
            raise ValueError(
                "Version OpenFlow no soportada: {}".format(self.openflow_version)
            )

        #
        # Utilizar nuestro switch OVS escalable.
        #
        # El switch conserva el comportamiento de OVSSwitch pero evita
        # utilizar una unica invocacion enorme a ovs-vsctl cuando existe
        # una gran cantidad de puertos.
        #

        switch_class = partial(ScalableOVSSwitch, protocols=protocol)

        #
        # Construir la red Mininet.
        #
        # Las direcciones MAC ya fueron resueltas previamente por
        # host_identity.py, por lo que Mininet no debe generar otras
        # automaticamente.
        #

        self.net = Mininet(
            topo=self.topology,
            controller=None,
            switch=switch_class,
            link=TCLink,
            autoSetMacs=False,
        )

        #
        # Registrar el controlador SDN que se ejecuta externamente
        # respecto de Mininet.
        #

        self.net.addController(
            "c0",
            controller=RemoteController,
            ip=self.controller_config["ip"],
            port=self.controller_config["port"],
        )

        #
        # Iniciar hosts, switches, enlaces y controlador remoto.
        #

        self.net.start()

        #
        # Validar que todos los switches declarados por Mininet
        # existan efectivamente como bridges en Open vSwitch.
        #
        # Un experimento no debe continuar si la infraestructura
        # subyacente fue creada de manera incompleta.
        #

        self._validate_switches()

        return self.net

    def _validate_switches(self):

        failed_switches = []

        for switch in self.net.switches:
            output = switch.cmd(
                "ovs-vsctl br-exists {} >/dev/null 2>&1; echo $?".format(switch.name)
            ).strip()

            if output != "0":
                failed_switches.append(switch.name)

        if failed_switches:
            raise RuntimeError(
                "No se pudieron crear correctamente los bridges OVS: {}".format(
                    ", ".join(failed_switches)
                )
            )

    def stop(self):

        if self.net is not None:
            self.net.stop()

            self.net = None
