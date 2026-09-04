from functools import partial

from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.node import RemoteController


class NetworkRuntime:
    OPENFLOW_PROTOCOLS = {"1.3": "OpenFlow13"}

    def __init__(self, topology, controller_config, openflow_version):

        self.topology = topology
        self.controller_config = controller_config
        self.openflow_version = openflow_version

        self.net = None

    def start(self):

        protocol = self.OPENFLOW_PROTOCOLS.get(self.openflow_version)

        if protocol is None:
            raise ValueError(
                "Version OpenFlow no soportada: {}".format(self.openflow_version)
            )

        #
        # Crear switches OVS utilizando el protocolo OpenFlow
        # configurado para el experimento.
        #
        # batch=False fuerza a Mininet a iniciar cada switch de manera
        # independiente en lugar de agrupar la configuracion de todos
        # los switches en una unica operacion de OVS.
        #
        # Esto resulta especialmente importante para topologias con
        # switches que poseen una gran cantidad de puertos.
        #

        switch_class = partial(OVSSwitch, protocols=protocol, batch=False)

        self.net = Mininet(
            topo=self.topology,
            controller=None,
            switch=switch_class,
            link=TCLink,
            autoSetMacs=True,
        )

        #
        # Registrar el controlador remoto utilizado por los switches.
        #

        self.net.addController(
            "c0",
            controller=RemoteController,
            ip=self.controller_config["ip"],
            port=self.controller_config["port"],
        )

        #
        # Construir y arrancar la red completa.
        #

        self.net.start()

        print()
        print("===== INTERFACES POR SWITCH =====")
        print()

        for switch in self.net.switches:
            print("{}: {} interfaces".format(switch.name, len(switch.intfList())))

            print([intf.name for intf in switch.intfList()])

            print()

        #
        # Verificar que todos los switches declarados por Mininet
        # hayan sido creados realmente como bridges OVS.
        #
        # Mininet no siempre convierte un error producido por
        # ovs-vsctl en una excepcion Python, por lo que sin esta
        # comprobacion el experimento podria continuar con una red
        # incompleta y producir resultados invalidos.
        #

        print()
        print("===== DIAGNOSTICO OVS =====")
        print()

        for switch in self.net.switches:
            print(
                "{}: {}".format(
                    switch.name,
                    switch.cmd(
                        "ovs-vsctl br-exists {}; echo $?".format(switch.name)
                    ).strip(),
                )
            )

        print()
        print("Bridges existentes:")
        print(self.net.get("s2").cmd("ovs-vsctl list-br"))

        print()
        print("===== LOG OVS VSWITCHD =====")
        print()

        print(
            self.net.get("s2").cmd(
                "tail -n 100 /var/log/openvswitch/ovs-vswitchd.log 2>/dev/null"
            )
        )

        print()
        print("===== OVS SHOW =====")
        print()

        print(self.net.get("s2").cmd("ovs-vsctl show"))

        print()
        print("===== LOG OVSDB =====")
        print()

        print(
            self.net.get("s2").cmd(
                "tail -n 100 /var/log/openvswitch/ovsdb-server.log 2>/dev/null"
            )
        )

        print()

        self._validate_switches()

        return self.net

    def _validate_switches(self):

        failed_switches = []

        for switch in self.net.switches:
            command = "ovs-vsctl br-exists {}".format(switch.name)

            output = switch.cmd("{} >/dev/null 2>&1; echo $?".format(command)).strip()

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
