class RoutingState:
    def __init__(self):

        self.decisions = {}

    def build_key(self, source_switch, destination_switch, flow):

        return (source_switch, destination_switch, flow.key())

    def has_decision(self, source_switch, destination_switch, flow):

        key = self.build_key(source_switch, destination_switch, flow)

        return key in self.decisions

    def get_decision(self, source_switch, destination_switch, flow):

        key = self.build_key(source_switch, destination_switch, flow)

        return self.decisions.get(key)

    def save_decision(self, source_switch, destination_switch, flow, decision):

        key = self.build_key(source_switch, destination_switch, flow)

        self.decisions[key] = decision

    def clear(self):

        self.decisions.clear()
