import json
import os

from datetime import datetime
from datetime import timezone


class ResultManager:
    def __init__(self, results_dir):

        self.results_dir = results_dir

        os.makedirs(self.results_dir, exist_ok=True)

    def save_routing_decision(
        self, algorithm, metric, source, destination, flow, decision
    ):

        filename = os.path.join(self.results_dir, "routing_decisions.jsonl")

        route_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "algorithm": algorithm,
            "metric": metric,
            "source_switch": "s{}".format(source),
            "destination_switch": "s{}".format(destination),
            "flow": flow.to_dict(),
            "decision": {
                "path": ["s{}".format(node) for node in decision.path],
                "cost": decision.cost,
                "candidates": [
                    ["s{}".format(node) for node in candidate]
                    for candidate in decision.candidates
                ],
                "metadata": decision.metadata,
            },
        }

        with open(filename, "a", encoding="utf-8") as file:
            json.dump(route_data, file)

            file.write("\n")
