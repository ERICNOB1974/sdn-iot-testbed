import argparse

from common.config_loader import load_experiment_config


def get_value(config, key):

    value = config

    for part in key.split("."):
        value = value[part]

    return value


def main():

    parser = argparse.ArgumentParser(
        description="Consulta valores de una configuracion de experimento"
    )

    parser.add_argument("--config", required=True, help="Archivo YAML del experimento")

    parser.add_argument("--get", required=True, help="Clave a consultar")

    args = parser.parse_args()

    config = load_experiment_config(args.config)

    value = get_value(config, args.get)

    print(value)


if __name__ == "__main__":
    main()
