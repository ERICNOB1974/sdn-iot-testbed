#!/bin/bash

set -e

mkdir -p /var/run/openvswitch
mkdir -p /etc/openvswitch

DB=/etc/openvswitch/conf.db

if [ ! -f "$DB" ]; then
    ovsdb-tool create \
        "$DB" \
        /usr/share/openvswitch/vswitch.ovsschema
fi

ovsdb-server \
    --remote=punix:/var/run/openvswitch/db.sock \
    --remote=db:Open_vSwitch,Open_vSwitch,manager_options \
    --pidfile \
    --detach

ovs-vsctl --no-wait init

ovs-vswitchd \
    --pidfile \
    --detach

echo
echo " SDN-IoT Mininet environment"
echo

echo "Mininet:"
mn --version

echo
echo "Open vSwitch:"
ovs-vsctl --version | head -n 1

echo
echo "Python:"
python3 --version

echo
echo

exec "$@"
