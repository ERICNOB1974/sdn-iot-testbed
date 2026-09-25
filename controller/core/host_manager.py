class HostManager:
    def __init__(self):

        self.hosts = {}

    def learn(self, mac, switch, port):

        location = {"switch": switch, "port": port}

        if self.hosts.get(mac) == location:
            return False

        self.hosts[mac] = location

        return True

    def is_known(self, mac):

        return mac in self.hosts

    def get_switch(self, mac):

        return self.hosts[mac]["switch"]

    def get_port(self, mac):

        return self.hosts[mac]["port"]
