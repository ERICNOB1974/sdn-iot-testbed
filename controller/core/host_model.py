class HostModel:
    def __init__(self, config):

        self.by_name = {}

        self.by_mac = {}

        for host in config["topology"]["hosts"]:
            host_config = dict(host)

            name = host_config["name"]

            mac = host_config["mac"].lower()

            self.by_name[name] = host_config

            self.by_mac[mac] = host_config

    def get_by_name(self, name):

        return self.by_name.get(name)

    def get_by_mac(self, mac):

        return self.by_mac.get(mac.lower())

    def get_mac(self, name):

        host = self.get_by_name(name)

        if host is None:
            return None

        return host["mac"].lower()

    def get_ip(self, name):

        host = self.get_by_name(name)

        if host is None:
            return None

        return host["ip"]
