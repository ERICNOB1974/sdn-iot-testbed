from ryu.lib.packet import ether_types
from ryu.lib.packet import in_proto


class FlowManager:
    def add_flow(self, datapath, priority, match, actions):

        parser = datapath.ofproto_parser

        instructions = [
            parser.OFPInstructionActions(datapath.ofproto.OFPIT_APPLY_ACTIONS, actions)
        ]

        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=instructions
        )

        datapath.send_msg(mod)

    def install_table_miss(self, datapath):

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()

        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]

        self.add_flow(datapath, 0, match, actions)

    def build_flow_match(self, datapath, flow):

        parser = datapath.ofproto_parser

        fields = {
            "eth_src": flow.source_mac,
            "eth_dst": flow.destination_mac,
            "eth_type": flow.eth_type,
        }

        #
        # IPv4
        #

        if flow.eth_type == ether_types.ETH_TYPE_IP:
            if flow.source_ip is not None:
                fields["ipv4_src"] = flow.source_ip

            if flow.destination_ip is not None:
                fields["ipv4_dst"] = flow.destination_ip

        #
        # IPv6
        #

        elif flow.eth_type == ether_types.ETH_TYPE_IPV6:
            if flow.source_ip is not None:
                fields["ipv6_src"] = flow.source_ip

            if flow.destination_ip is not None:
                fields["ipv6_dst"] = flow.destination_ip

        #
        # Protocolo de capa 4.
        #
        # Por ejemplo:
        #
        # ICMP = 1
        # TCP  = 6
        # UDP  = 17
        #

        if flow.ip_protocol is not None:
            fields["ip_proto"] = flow.ip_protocol

        #
        # TCP
        #

        if flow.ip_protocol == in_proto.IPPROTO_TCP:
            if flow.source_port is not None:
                fields["tcp_src"] = flow.source_port

            if flow.destination_port is not None:
                fields["tcp_dst"] = flow.destination_port

        #
        # UDP
        #

        elif flow.ip_protocol == in_proto.IPPROTO_UDP:
            if flow.source_port is not None:
                fields["udp_src"] = flow.source_port

            if flow.destination_port is not None:
                fields["udp_dst"] = flow.destination_port

        return parser.OFPMatch(**fields)

    def install_path(self, path, flow, topology, hosts):

        for i in range(len(path)):
            switch = path[i]

            datapath = topology.datapaths[switch]

            parser = datapath.ofproto_parser

            #
            # Si estamos en el ultimo switch,
            # enviamos hacia el host destino.
            #

            if i == len(path) - 1:
                out_port = hosts.get_port(flow.destination_mac)

            #
            # Si no, enviamos hacia el siguiente
            # switch de la ruta.
            #

            else:
                next_switch = path[i + 1]

                out_port = topology.get_output_port(switch, next_switch)

            #
            # La regla OpenFlow identifica
            # al flujo completo.
            #

            match = self.build_flow_match(datapath, flow)

            actions = [parser.OFPActionOutput(out_port)]

            self.add_flow(datapath, 10, match, actions)

    def forward_packet(self, msg, path, flow, topology, hosts):

        datapath = msg.datapath

        parser = datapath.ofproto_parser

        current_switch = datapath.id

        index = path.index(current_switch)

        #
        # Ultimo switch:
        # enviar al host destino.
        #

        if index == len(path) - 1:
            out_port = hosts.get_port(flow.destination_mac)

        #
        # Switch intermedio:
        # enviar al siguiente switch.
        #

        else:
            next_switch = path[index + 1]

            out_port = topology.get_output_port(current_switch, next_switch)

        actions = [parser.OFPActionOutput(out_port)]

        data = None

        if msg.buffer_id == datapath.ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=msg.match["in_port"],
            actions=actions,
            data=data,
        )

        datapath.send_msg(out)

    def flood(self, msg):

        datapath = msg.datapath

        parser = datapath.ofproto_parser

        actions = [parser.OFPActionOutput(datapath.ofproto.OFPP_FLOOD)]

        data = None

        if msg.buffer_id == datapath.ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=msg.match["in_port"],
            actions=actions,
            data=data,
        )

        datapath.send_msg(out)
