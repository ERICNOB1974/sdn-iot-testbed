import argparse
from datetime import datetime

from common.component_loader import load_collectors
from common.component_loader import load_traffic_generator
from common.config_loader import load_yaml

from runner.topology_loader import load_topology
from runner.network_runtime import NetworkRuntime
from runner.result_writer import ResultWriter


class ExperimentRunner:
    def __init__(
        self,
        config_path,
        results_dir,
        run_id,
        start_time,
        git_commit,
        controller_version,
        openvswitch_version,
    ):

        self.config = load_yaml(config_path)

        self.results = ResultWriter(results_dir)

        self.run_id = run_id

        self.start_time = start_time

        self.git_commit = git_commit

        self.controller_version = controller_version

        self.openvswitch_version = openvswitch_version

        self.runtime = None

    def get_traffic_config(self):

        return self.config["traffic"]["config"]

    def build_metadata(self, traffic_result, status):

        end_time = datetime.now().astimezone().isoformat(timespec="seconds")

        metadata = {
            "experiment_id": self.config["experiment"]["id"],
            "run_id": self.run_id,
            "status": status,
            "start_time": self.start_time,
            "end_time": end_time,
            "git_commit": self.git_commit,
            "controller_environment": self.config["environment"]["controller"],
            "controller": self.controller_version,
            "controller_app": self.config["controller"]["app"],
            "openflow_port": self.config["controller"]["port"],
            "topology": self.config["topology"]["name"],
            "network_profile": self.config["network"]["name"],
            "routing_algorithm": self.config["routing"]["name"],
            "routing_metric": self.config["routing"]["metric"],
            "mininet": self.config["environment"]["mininet"].replace("mininet-", ""),
            "openvswitch": self.openvswitch_version,
            "openflow": self.config["environment"]["openflow"],
            "traffic": traffic_result.metadata,
        }

        if traffic_result.metrics:
            metadata["traffic_metrics"] = traffic_result.metrics

        return metadata

    def run(self):

        experiment_id = self.config["experiment"]["id"]

        print("Ejecutando experimento: {}".format(experiment_id))

        topology = load_topology(self.config)

        self.runtime = NetworkRuntime(
            topology=topology,
            controller_config=self.config["controller"],
            openflow_version=self.config["environment"]["openflow"],
        )

        traffic_config = self.get_traffic_config()

        try:
            net = self.runtime.start()

            traffic_generator = load_traffic_generator(self.config["traffic"])

            print("Ejecutando generador de trafico")

            traffic_result = traffic_generator(net, traffic_config)

            traffic_type = traffic_result.metadata.get("type", "traffic")

            self.results.write_text(
                "{}.txt".format(traffic_type), traffic_result.raw_output
            )

            collectors = load_collectors(self.config.get("collectors", []))

            for collector_name, collector in collectors:
                print("Ejecutando collector: {}".format(collector_name))

                collector_result = collector(net, self.config)

                self.results.write_text(
                    "{}.txt".format(collector_name), collector_result
                )

            metadata = self.build_metadata(
                traffic_result=traffic_result, status="success"
            )

            self.results.write_json("metadata.json", metadata)

        finally:
            if self.runtime is not None:
                self.runtime.stop()


def main():

    parser = argparse.ArgumentParser(description="SDN-IoT experiment runner")

    parser.add_argument(
        "--config", required=True, help="Configuracion YAML del experimento"
    )

    parser.add_argument(
        "--results-dir", required=True, help="Directorio de resultados del run"
    )

    parser.add_argument("--run-id", required=True, help="Identificador del run")

    parser.add_argument(
        "--start-time", required=True, help="Instante de inicio del experimento"
    )

    parser.add_argument("--git-commit", required=True, help="Commit Git utilizado")

    parser.add_argument(
        "--controller-version", required=True, help="Version del controlador"
    )

    parser.add_argument(
        "--openvswitch-version", required=True, help="Version de Open vSwitch"
    )

    args = parser.parse_args()

    runner = ExperimentRunner(
        config_path=args.config,
        results_dir=args.results_dir,
        run_id=args.run_id,
        start_time=args.start_time,
        git_commit=args.git_commit,
        controller_version=args.controller_version,
        openvswitch_version=args.openvswitch_version,
    )

    runner.run()


if __name__ == "__main__":
    main()
