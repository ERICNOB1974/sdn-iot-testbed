import re
import shlex
import time
import uuid

from traffic.result import TrafficResult


def _quote(value):
    return shlex.quote(str(value))


def _normalize_protocol(ip_protocol):
    protocols = {
        6: "TCP",
        17: "UDP",
    }

    if ip_protocol not in protocols:
        raise ValueError("Protocolo IP no soportado por D-ITG: {}".format(ip_protocol))

    return protocols[ip_protocol]


def _validate_flow(flow):
    required = [
        "id",
        "source",
        "destination",
        "traffic",
    ]

    for field in required:
        if field not in flow:
            raise ValueError(
                "El flujo D-ITG '{}' no define '{}'".format(
                    flow.get("id", "<sin-id>"),
                    field,
                )
            )

    if flow["source"] == flow["destination"]:
        raise ValueError("El origen y destino del flujo D-ITG no pueden ser iguales")

    traffic = flow["traffic"]

    required_traffic = [
        "ip_protocol",
        "source_port",
        "destination_port",
        "packet_size_bytes",
        "rate_pps",
        "duration_seconds",
    ]

    for field in required_traffic:
        if field not in traffic:
            raise ValueError(
                "El flujo D-ITG '{}' no define 'traffic.{}'".format(
                    flow["id"],
                    field,
                )
            )

    _normalize_protocol(traffic["ip_protocol"])

    if not 1 <= int(traffic["source_port"]) <= 65535:
        raise ValueError("source_port debe estar entre 1 y 65535")

    if not 1 <= int(traffic["destination_port"]) <= 65535:
        raise ValueError("destination_port debe estar entre 1 y 65535")

    if int(traffic["packet_size_bytes"]) <= 0:
        raise ValueError("packet_size_bytes debe ser mayor que cero")

    if float(traffic["rate_pps"]) <= 0:
        raise ValueError("rate_pps debe ser mayor que cero")

    if float(traffic["duration_seconds"]) <= 0:
        raise ValueError("duration_seconds debe ser mayor que cero")

    if float(traffic.get("start_seconds", 0)) < 0:
        raise ValueError("start_seconds debe ser mayor o igual que cero")

    if int(traffic.get("seed", 0)) < 0:
        raise ValueError("seed debe ser mayor o igual que cero")


def _parse_itgdec_summary(output):
    patterns = {
        "total_time_seconds": (
            r"Total time\s*=\s*([0-9.]+)\s+s",
            float,
        ),
        "packets_received": (
            r"Total packets\s*=\s*(\d+)",
            int,
        ),
        "minimum_delay_seconds": (
            r"Minimum delay\s*=\s*([0-9.]+)\s+s",
            float,
        ),
        "maximum_delay_seconds": (
            r"Maximum delay\s*=\s*([0-9.]+)\s+s",
            float,
        ),
        "average_delay_seconds": (
            r"Average delay\s*=\s*([0-9.]+)\s+s",
            float,
        ),
        "average_jitter_seconds": (
            r"Average jitter\s*=\s*([0-9.]+)\s+s",
            float,
        ),
        "delay_stddev_seconds": (
            r"Delay standard deviation\s*=\s*([0-9.]+)\s+s",
            float,
        ),
        "bytes_received": (
            r"Bytes received\s*=\s*(\d+)",
            int,
        ),
        "average_bitrate_kbps": (
            r"Average bitrate\s*=\s*([0-9.]+)\s+Kbit/s",
            float,
        ),
        "average_packet_rate_pps": (
            r"Average packet rate\s*=\s*([0-9.]+)\s+pkt/s",
            float,
        ),
        "packets_dropped": (
            r"Packets dropped\s*=\s*(\d+)",
            int,
        ),
        "packet_loss_percent": (
            r"Packets dropped\s*=\s*\d+\s+\(([0-9.]+)\s*%\)",
            float,
        ),
    }

    metrics = {}

    for name, (pattern, converter) in patterns.items():
        match = re.search(pattern, output)

        if match is None:
            raise RuntimeError(
                "ITGDec no contiene la metrica esperada '{}'".format(name)
            )

        metrics[name] = converter(match.group(1))

    return metrics


def run_ditg(net, config):
    flows = config.get("flows", [])

    if not flows:
        raise ValueError("El perfil D-ITG debe contener al menos un flujo")

    for flow in flows:
        _validate_flow(flow)

    run_id = uuid.uuid4().hex[:8]

    receivers = {}
    senders = []
    flow_metadata = []
    outputs = []
    flow_metrics = {}

    try:
        #
        # ---------------------------------------------------------
        # 1. INICIAR RECEPTORES
        # ---------------------------------------------------------
        #

        destination_names = sorted({flow["destination"] for flow in flows})

        for destination_name in destination_names:
            destination_host = net.get(destination_name)

            receiver_output = "/tmp/ditg-recv-{}-{}.txt".format(
                run_id,
                destination_name,
            )

            output_file = open(
                receiver_output,
                "w",
            )

            process = destination_host.popen(
                ["ITGRecv"],
                stdout=output_file,
                stderr=output_file,
            )

            receivers[destination_name] = {
                "host": destination_host,
                "process": process,
                "output": receiver_output,
                "output_file": output_file,
            }

        #
        # Dar tiempo a ITGRecv para abrir el canal de señalizacion.
        #

        time.sleep(1.0)

        #
        # Comprobar que ningun ITGRecv termino prematuramente.
        #

        for destination_name, receiver in receivers.items():
            process = receiver["process"]

            if process.poll() is not None:
                receiver["output_file"].flush()

                with open(
                    receiver["output"],
                    "r",
                ) as file:
                    output = file.read()

                raise RuntimeError(
                    "ITGRecv termino inesperadamente en {} con codigo {}:\n{}".format(
                        destination_name,
                        process.returncode,
                        output,
                    )
                )

        #
        # ---------------------------------------------------------
        # 2. INICIAR EMISORES
        # ---------------------------------------------------------
        #
        # start_seconds se interpreta respecto del comienzo de esta
        # fase. Los flujos se ordenan por su instante de inicio.
        #

        traffic_start = time.monotonic()

        ordered_flows = sorted(
            flows,
            key=lambda flow: float(flow["traffic"].get("start_seconds", 0)),
        )

        for flow in ordered_flows:
            flow_id = flow["id"]

            source_name = flow["source"]
            destination_name = flow["destination"]

            source_host = net.get(source_name)
            destination_host = net.get(destination_name)

            destination_ip = destination_host.IP()

            traffic = flow["traffic"]

            ip_protocol = int(traffic["ip_protocol"])
            protocol = _normalize_protocol(ip_protocol)

            source_port = int(traffic["source_port"])
            destination_port = int(traffic["destination_port"])

            packet_size = int(traffic["packet_size_bytes"])
            packet_rate = float(traffic["rate_pps"])

            duration_seconds = float(traffic["duration_seconds"])
            duration_ms = int(duration_seconds * 1000)

            start_seconds = float(traffic.get("start_seconds", 0))

            seed = traffic.get("seed")

            if seed is not None:
                seed = float(seed)

            target_start = traffic_start + start_seconds
            remaining = target_start - time.monotonic()

            if remaining > 0:
                time.sleep(remaining)

            sender_log = "/tmp/ditg-send-log-{}-{}.log".format(
                run_id,
                flow_id,
            )

            receiver_log = "/tmp/ditg-recv-log-{}-{}.log".format(
                run_id,
                flow_id,
            )

            sender_output = "/tmp/ditg-send-output-{}-{}.txt".format(
                run_id,
                flow_id,
            )

            output_file = open(
                sender_output,
                "w",
            )

            command = [
                "ITGSend",
                "-a",
                destination_ip,
                "-T",
                protocol,
                "-sp",
                str(source_port),
                "-rp",
                str(destination_port),
                "-C",
                str(packet_rate),
                "-c",
                str(packet_size),
                "-t",
                str(duration_ms),
            ]

            if seed is not None:
                command.extend(
                    [
                        "-s",
                        str(seed),
                    ]
                )

            command.extend(
                [
                    "-l",
                    sender_log,
                    "-x",
                    receiver_log,
                ]
            )

            actual_start_seconds = time.monotonic() - traffic_start

            process = source_host.popen(
                command,
                stdout=output_file,
                stderr=output_file,
            )

            senders.append(
                {
                    "id": flow_id,
                    "source": source_name,
                    "destination": destination_name,
                    "host": source_host,
                    "destination_host": destination_host,
                    "process": process,
                    "sender_output": sender_output,
                    "sender_log": sender_log,
                    "receiver_log": receiver_log,
                    "output_file": output_file,
                }
            )

            flow_metadata.append(
                {
                    "id": flow_id,
                    "source": source_name,
                    "destination": destination_name,
                    "destination_ip": destination_ip,
                    "ip_protocol": ip_protocol,
                    "protocol": protocol.lower(),
                    "source_port": source_port,
                    "destination_port": destination_port,
                    "packet_size_bytes": packet_size,
                    "rate_pps": packet_rate,
                    "duration_seconds": duration_seconds,
                    "start_seconds": start_seconds,
                    "actual_start_seconds": actual_start_seconds,
                    "seed": seed,
                }
            )

        #
        # ---------------------------------------------------------
        # 3. ESPERAR A TODOS LOS EMISORES
        # ---------------------------------------------------------
        #

        for sender in senders:
            return_code = sender["process"].wait()

            sender["output_file"].flush()

            if return_code != 0:
                with open(
                    sender["sender_output"],
                    "r",
                ) as file:
                    sender_output = file.read()

                raise RuntimeError(
                    "ITGSend fallo para {} con codigo {}:\n{}".format(
                        sender["id"],
                        return_code,
                        sender_output,
                    )
                )

        #
        # Dar tiempo al receptor para vaciar su buffer de logging.
        #

        time.sleep(1.0)

        #
        # ---------------------------------------------------------
        # 4. COMPROBAR LOGS, DECODIFICAR Y EXTRAER METRICAS
        # ---------------------------------------------------------
        #

        for sender in senders:
            source_host = sender["host"]
            destination_host = sender["destination_host"]

            sender["output_file"].flush()

            with open(
                sender["sender_output"],
                "r",
            ) as file:
                sender_output = file.read()

            #
            # Comprobar log del emisor.
            #

            sender_log_exists = source_host.cmd(
                "test -s {}; echo $?".format(_quote(sender["sender_log"]))
            ).strip()

            if sender_log_exists != "0":
                raise RuntimeError(
                    "D-ITG no genero el log del emisor para {}.\n"
                    "Salida de ITGSend:\n{}".format(
                        sender["id"],
                        sender_output,
                    )
                )

            #
            # Comprobar log del receptor.
            #

            receiver_log_exists = destination_host.cmd(
                "test -s {}; echo $?".format(_quote(sender["receiver_log"]))
            ).strip()

            if receiver_log_exists != "0":
                receiver = receivers[sender["destination"]]

                receiver["output_file"].flush()

                with open(
                    receiver["output"],
                    "r",
                ) as file:
                    receiver_output = file.read()

                raise RuntimeError(
                    "D-ITG no genero el log del receptor para {}.\n"
                    "Salida de ITGSend:\n{}\n"
                    "Salida de ITGRecv:\n{}".format(
                        sender["id"],
                        sender_output,
                        receiver_output,
                    )
                )

            #
            # Decodificar log del receptor.
            #

            decoded_output = destination_host.cmd(
                "ITGDec {} 2>&1".format(_quote(sender["receiver_log"]))
            )

            decoded_lower = decoded_output.lower()

            if "error opening log file" in decoded_lower or "error :" in decoded_lower:
                raise RuntimeError(
                    "ITGDec fallo para {}:\n{}".format(
                        sender["id"],
                        decoded_output,
                    )
                )

            #
            # Extraer metricas estructuradas del flujo.
            #

            flow_metrics[sender["id"]] = _parse_itgdec_summary(decoded_output)

            #
            # Conservar tambien la salida original de D-ITG.
            #

            outputs.append(
                "===== FLOW {} =====\n"
                "----- ITGSend -----\n"
                "{}\n"
                "----- ITGDec receiver-side -----\n"
                "{}\n".format(
                    sender["id"],
                    sender_output,
                    decoded_output,
                )
            )

    finally:
        #
        # ---------------------------------------------------------
        # 5. DETENER RECEPTORES Y CERRAR ARCHIVOS
        # ---------------------------------------------------------
        #

        for sender in senders:
            output_file = sender.get("output_file")

            if output_file is not None:
                output_file.close()

        for receiver in receivers.values():
            process = receiver.get("process")

            if process is not None:
                if process.poll() is None:
                    process.terminate()

                    try:
                        process.wait(timeout=2)
                    except Exception:
                        process.kill()
                        process.wait()

            output_file = receiver.get("output_file")

            if output_file is not None:
                output_file.close()

    #
    # -------------------------------------------------------------
    # 6. DEVOLVER RESULTADO
    # -------------------------------------------------------------
    #

    return TrafficResult(
        raw_output="\n".join(outputs),
        metadata={
            "type": "ditg",
            "flows": flow_metadata,
        },
        metrics={
            "flows": flow_metrics,
        },
    )
