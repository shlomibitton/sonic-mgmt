#!/bin/bash

SWITCH=$1

SONIC_LOGIN="admin@${SWITCH}"
SONIC_PASS="YourPaSsWoRd"
SSH_PARAMS="-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
SONIC_SSH_CMD="sshpass -p ${SONIC_PASS} ssh ${SSH_PARAMS} ${SONIC_LOGIN}"

AddRouteForNTP () {
    NTP_IP="10.210.25.32"
    GATEWAY_IP=$(${SONIC_SSH_CMD} ip -4 address show dev eth0 | awk '/inet/ {print$2}' | sed -E 's/[0-9]+\/[0-9]+/1/')
    ADD_ROUTE=$(${SONIC_SSH_CMD} sudo ip route add ${NTP_IP} via ${GATEWAY_IP})
}

if [[ "${SWITCH}" = "arc-mtbc-1001" ]]; then
    AddRouteForNTP
fi

if [[ "${SWITCH}" = "mtbc-sonic-01-2410" ]]; then
    AddRouteForNTP
fi

if [[ "${SWITCH}" = "mtbc-sonic-03-2700" ]]; then
    AddRouteForNTP
fi

if [[ "${SWITCH}" = "mtbc-3700c-01" ]]; then
    AddRouteForNTP
fi
