class RoutingAlgorithm:
    decision_policy = "sticky"
    scheduling_mode = "per_flow"

    def compute(self, graph, context):

        raise NotImplementedError("El algoritmo debe implementar compute()")

    def compute_plan(self, graph, contexts):

        raise NotImplementedError("El algoritmo no implementa planificacion global")
