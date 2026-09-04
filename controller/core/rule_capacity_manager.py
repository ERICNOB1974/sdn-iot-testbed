class RuleCapacityManager:
    def __init__(self):

        self.capacity = {}
        self.rules = {}

    def set_capacity(self, switch, capacity):

        self.capacity[switch] = capacity

        self.rules.setdefault(switch, set())

    def register_flow(self, switch, flow):

        self.rules.setdefault(switch, set())

        self.rules[switch].add(flow.key())

    def register_path(self, path, flow):

        for switch in path:
            self.register_flow(switch, flow)

    def get_capacity(self, switch):

        return self.capacity.get(switch)

    def get_used(self, switch):

        return len(self.rules.get(switch, set()))

    def get_remaining(self, switch):

        capacity = self.get_capacity(switch)

        if capacity is None:
            return None

        return capacity - self.get_used(switch)
