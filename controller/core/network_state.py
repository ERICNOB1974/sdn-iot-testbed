class NetworkState:
    def __init__(self, topology):

        self.topology = topology

    def get_link_metrics(self, source, destination):

        return self.topology.graph[source][destination].get("metrics", {})

    def get_metric(self, source, destination, name, default=None):

        metrics = self.get_link_metrics(source, destination)

        return metrics.get(name, default)

    def set_metric(self, source, destination, name, value):

        metrics = self.topology.graph[source][destination].setdefault("metrics", {})

        metrics[name] = value

    def update_link_metrics(self, source, destination, metrics):

        current = self.topology.graph[source][destination].setdefault("metrics", {})

        current.update(metrics)

    def get_path_additive_metric(self, path, metric):

        total = 0

        for index in range(len(path) - 1):
            total += self.get_metric(path[index], path[index + 1], metric, 0)

        return total

    def get_path_bottleneck_metric(self, path, metric):

        values = []

        for index in range(len(path) - 1):
            value = self.get_metric(path[index], path[index + 1], metric)

            if value is not None:
                values.append(value)

        if not values:
            return None

        return min(values)
