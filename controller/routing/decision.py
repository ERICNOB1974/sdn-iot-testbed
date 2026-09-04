class RoutingDecision:
    def __init__(
        self,
        path=None,
        cost=None,
        candidates=None,
        metadata=None,
        admitted=True,
    ):

        self.path = path
        self.cost = cost

        self.candidates = candidates if candidates is not None else []

        self.metadata = metadata if metadata is not None else {}

        self.admitted = admitted
