FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates python3 python-is-python3 help2man python3-pip python3-setuptools python3-pexpect build-essential iproute2 iputils-ping net-tools ethtool socat psmisc procps iperf openvswitch-switch openvswitch-common && rm -rf /var/lib/apt/lists/* && python3 -m pip install --no-cache-dir PyYAML==6.0.2

WORKDIR /opt

RUN git clone --branch 2.3.0 --depth 1 https://github.com/mininet/mininet.git

WORKDIR /opt/mininet

RUN make install

WORKDIR /workspace

COPY docker/mininet/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["bash"]
