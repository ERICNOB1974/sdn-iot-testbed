from ryu.lib.packet import ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import ipv6
from ryu.lib.packet import tcp
from ryu.lib.packet import udp


class FlowIdentity:
    def __init__(
        self,
        source_mac,
        destination_mac,
        eth_type,
        source_ip=None,
        destination_ip=None,
        ip_protocol=None,
        source_port=None,
        destination_port=None,
    ):

        self.source_mac = source_mac.lower()
        self.destination_mac = destination_mac.lower()

        self.eth_type = eth_type

        self.source_ip = source_ip
        self.destination_ip = destination_ip

        self.ip_protocol = ip_protocol

        self.source_port = source_port
        self.destination_port = destination_port

    @classmethod
    def from_packet(cls, pkt):

        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return None

        source_ip = None
        destination_ip = None
        ip_protocol = None

        source_port = None
        destination_port = None

        ipv4_packet = pkt.get_protocol(ipv4.ipv4)

        ipv6_packet = pkt.get_protocol(ipv6.ipv6)

        if ipv4_packet is not None:
            source_ip = ipv4_packet.src
            destination_ip = ipv4_packet.dst
            ip_protocol = ipv4_packet.proto

        elif ipv6_packet is not None:
            source_ip = ipv6_packet.src
            destination_ip = ipv6_packet.dst
            ip_protocol = ipv6_packet.nxt

        tcp_packet = pkt.get_protocol(tcp.tcp)

        udp_packet = pkt.get_protocol(udp.udp)

        if tcp_packet is not None:
            source_port = tcp_packet.src_port
            destination_port = tcp_packet.dst_port

        elif udp_packet is not None:
            source_port = udp_packet.src_port
            destination_port = udp_packet.dst_port

        return cls(
            source_mac=eth.src,
            destination_mac=eth.dst,
            eth_type=eth.ethertype,
            source_ip=source_ip,
            destination_ip=destination_ip,
            ip_protocol=ip_protocol,
            source_port=source_port,
            destination_port=destination_port,
        )

    def is_ip_flow(self):

        return self.source_ip is not None and self.destination_ip is not None

    def key(self):

        return (
            self.source_mac,
            self.destination_mac,
            self.eth_type,
            self.source_ip,
            self.destination_ip,
            self.ip_protocol,
            self.source_port,
            self.destination_port,
        )

    def to_dict(self):

        return {
            "source_mac": self.source_mac,
            "destination_mac": self.destination_mac,
            "eth_type": self.eth_type,
            "source_ip": self.source_ip,
            "destination_ip": self.destination_ip,
            "ip_protocol": self.ip_protocol,
            "source_port": self.source_port,
            "destination_port": self.destination_port,
        }
