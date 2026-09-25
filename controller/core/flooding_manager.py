class FloodingManager:
    def __init__(self, topology):

        self.topology = topology

    def flood(self, msg):

        datapath = msg.datapath

        parser = datapath.ofproto_parser

        ofproto = datapath.ofproto

        dpid = datapath.id

        in_port = msg.match["in_port"]

        #
        # Construir el spanning tree de flooding.
        #

        tree_ports = self.topology.build_flooding_tree()

        #
        # Puertos switch-switch pertenecientes
        # al spanning tree.
        #

        allowed_switch_ports = tree_ports.get(dpid, set())

        #
        # Todos los puertos que conectan este
        # switch con otros switches.
        #

        all_switch_ports = self.topology.get_switch_ports(dpid)

        output_ports = []

        #
        # datapath.ports contiene los puertos
        # OpenFlow conocidos para este switch.
        #

        for port_no in datapath.ports.keys():
            #
            # Nunca reenviar por el puerto
            # por donde entro el paquete.
            #

            if port_no == in_port:
                continue

            #
            # Ignorar puertos reservados por
            # OpenFlow.
            #

            if port_no >= ofproto.OFPP_MAX:
                continue

            #
            # Si es un puerto switch-switch,
            # solamente puede utilizarse si
            # pertenece al spanning tree.
            #

            if port_no in all_switch_ports:
                if port_no not in allowed_switch_ports:
                    continue

            #
            # Los puertos restantes son puertos
            # de acceso hacia hosts y pueden
            # recibir el broadcast.
            #

            output_ports.append(port_no)

        #
        # No hay ningún puerto válido.
        #

        if not output_ports:
            return

        actions = [parser.OFPActionOutput(port_no) for port_no in output_ports]

        data = None

        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )

        datapath.send_msg(out)
