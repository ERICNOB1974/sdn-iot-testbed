import networkx as nx

from controller.routing.base import RoutingAlgorithm
from controller.routing.decision import RoutingDecision


class DijkstraRouting(RoutingAlgorithm):
    name = "dijkstra"

    def compute(self, graph, context):

        path = nx.shortest_path(
            graph, source=context.source, target=context.destination, weight="weight"
        )

        cost = nx.shortest_path_length(
            graph, source=context.source, target=context.destination, weight="weight"
        )

        return RoutingDecision(path=path, cost=cost)
