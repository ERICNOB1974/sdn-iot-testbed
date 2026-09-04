"""
Analiza y muestra los resultados principales del experimento EXP001
"""

import os
import re

RESULTS_DIR = "results/exp001"


def read_route():
    """
    Lee el archivo route.txt y muestra la ruta seleccionada por el algoritmo de ruteo junto con su costo
    """

    filename = os.path.join(RESULTS_DIR, "route.txt")

    if not os.path.exists(filename):
        print("No existe route.txt")
        return

    print("Ruta seleccionada:")

    with open(filename, "r") as file:
        for line in file:
            if line.startswith("path="):
                print(line.strip().replace("path=", ""))
            if line.startswith("cost="):
                print("Costo:", line.strip().replace("cost=", ""))


def read_ping():
    """
    Lee el archivo ping.txt y extrae las métricas principales
    """

    filename = os.path.join(RESULTS_DIR, "ping.txt")

    # Si no existe el archivo, devuelve que no hay nada para analizar
    if not os.path.exists(filename):
        print("No existe ping.txt")
        return

    with open(filename, "r") as file:
        content = file.read()

    # Buscar el porcentaje de paquetes perdidos
    loss_match = re.search(r"(\d+(?:\.\d+)?)% packet loss", content)

    rtt_match = re.search(r"=\s*([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)\s*ms", content)

    if loss_match:
        print("Packet loss:", loss_match.group(1), "%")

    if rtt_match:
        print("RTT promedio:", rtt_match.group(2), "ms")


print()
print("===== EXPERIMENTO EXP001 =====")
print()

read_route()

print()

read_ping()

print()
