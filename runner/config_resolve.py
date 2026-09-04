import argparse
from pathlib import Path

import yaml

from common.config_resolver import resolve_experiment_config


def main():

    parser = argparse.ArgumentParser(
        description="Resolve SDN-IoT experiment configuration"
    )

    parser.add_argument(
        "--config", required=True, help="Configuracion original del experimento"
    )

    parser.add_argument(
        "--output", required=True, help="Archivo YAML de configuracion resuelta"
    )

    args = parser.parse_args()

    resolved_config = resolve_experiment_config(args.config)

    output_path = Path(args.output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        yaml.safe_dump(resolved_config, file, sort_keys=False, allow_unicode=True)

    print(output_path)


if __name__ == "__main__":
    main()
