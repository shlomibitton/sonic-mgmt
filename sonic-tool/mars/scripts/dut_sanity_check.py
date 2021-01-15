# Builtin libs
import argparse
import json
import os
import sys
import time

# Third-party libs
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.devices import SonicDevice
from lib.devices import SonicMgmtDevice
from lib.utils import parse_topology, get_logger, wait_until

logger = get_logger("DUTSanityCheck")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--dut-name", required=True, dest="dut_name",
                        help="Name of the dut")
    parser.add_argument("--sonic-topo", required=True, dest="sonic_topo",
                        help="The topo for SONiC testing, for example: t0, t1, t1-lag, ptf32, ...")
    parser.add_argument("--recover", nargs="?", default="no", dest="recover",
                        choices=["yes", "no", "true", "false", "True", "False"],
                        help="Whether try to recover in case of sanity check failed. Default: 'no'")
    parser.add_argument("--repo-name", dest="repo_name", help="Specify the sonic-mgmt repository name")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo")
    return parser.parse_args()


def find_down_ports(sonic_mgmt, dut_name, topo):
    """
    @summary: Check interface status on DUT.

    This function check all interfaces, port channels and VLAN interfaces. If any of them are down, name of the
    down interface will be returned in a list.

    @param sonic_mgmt: Instance of the SonicMgmtDevice class.
    @param dut_name: Name of the DUT.
    @param topo: The SONiC topology, for example: t0, t1, t1-lag, etc.
    @return: Return name of the down ports in a list.
    """
    logger.info("Get minigraph facts of dut on sonic_mgmt")
    mg_facts = sonic_mgmt.run_ansible("minigraph_facts", "inventory", "%s-%s" % (dut_name, topo),
                                      "-a host=%s" % dut_name).ansible_result["ansible_facts"]

    logger.info("Get current interface status on DUT")
    intf_facts = sonic_mgmt.run_ansible("interface_facts", "inventory",
                                        "%s-%s" % (dut_name, topo)).ansible_result["ansible_facts"]

    down_ports = []
    logger.info("Check Port, PortChannel, VLAN Interface status")
    interfaces = mg_facts["minigraph_ports"].keys() + mg_facts["minigraph_portchannels"].keys() + \
                 mg_facts["minigraph_vlans"].keys()
    for intf in interfaces:
        try:
            port = intf_facts["ansible_interface_facts"][intf]
            if not port["link"] or not port["active"]:
                down_ports.append(intf)
        except KeyError as e:
            down_ports.append(intf)

    if down_ports:
        logger.error("Found down ports: %s" % json.dumps(down_ports, indent=4))
    return down_ports


def all_ports_up(sonic_mgmt, dut_name, topo):
    return len(find_down_ports(sonic_mgmt, dut_name, topo)) <= 0


def sanity_check(dut, sonic_mgmt, dut_name, topo):
    """
    @summary: Perform sanity checks.

    This function performs sanity checks on the DUT device.

    @param dut: Instance of the SonicDevice class.
    @param sonic_mgmt: Instance of the SonicMgmtDevice class.
    @param dut_name: Name of the DUT.
    @param topo: The SONiC topology, for example: t0, t1, t1-lag, etc.
    @return: Returns a list of dictionaries. Each dictionary is a failure. It must has key "msg" to indicate details
             of the failed checking. If everything is OK, returns an empty list.
    """
    sanity_failures = []
    critical_services_status = dut.critical_services_status()
    if not all(critical_services_status.values()):
        sanity_failures.append({
            "msg": "Not all critical services are fully started. critical_services_status=" +
                   str(critical_services_status)
        })

    if not wait_until(200, 30, all_ports_up, sonic_mgmt, dut_name, topo):
        logger.error("Not all ports are up")
        sanity_failures.append({
            "msg": "Not all ports are up"
        })
    return sanity_failures


if __name__ == "__main__":
    args = _parse_args()

    topo = parse_topology(args.topo)

    repo_path = os.path.join(args.workspace_path, args.repo_name)

    dut_device = topo.get_device_by_topology_id(constants.DUT_DEVICE_ID)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)

    dut = SonicDevice(dut_device.BASE_IP, dut_device.USERS[0].USERNAME, dut_device.USERS[0].PASSWORD)
    sonic_mgmt_container = SonicMgmtDevice(sonic_mgmt_device.BASE_IP, sonic_mgmt_device.USERS[0].USERNAME,
                                           sonic_mgmt_device.USERS[0].PASSWORD, repo_path)

    # Record SONiC version in log
    dut.run("show version")
    dut.run("sudo sonic_installer list")
    dut.run("ip route | wc -l")

    timeout = max(500 - dut.get_uptime().seconds, 0)
    if not wait_until(timeout, 20, dut.critical_services_fully_started):
        logger.error("Not all critical services are started after 300 seconds")

    sanity_results = sanity_check(dut, sonic_mgmt_container, args.dut_name, args.sonic_topo)
    if not sanity_results:
        logger.info("Sanity check passed")
        sys.exit(0)

    logger.error("Sanity check failed:\n%s" % json.dumps(sanity_results, indent=4))

    if not args.recover or args.recover.lower() not in ["yes", "true"]:
        logger.error("Argument recover is not specified or is not evaluated to True, failed")
        sys.exit(1)

    logger.info("Try to reboot the DUT to recover")
    dut.connection.timeouts.command = 120
    dut.connection.connect_timeout = 10
    try:
        dut.run("sudo reboot")
    except Exception as e:
        logger.error("Exception raised while run 'sudo reboot': %s" % repr(e))

    logger.info("Close the connection and wait some time to reconnect")
    dut.connection.close()
    time.sleep(30)

    logger.info("Try to reconnect to %s after reboot" % dut.connection.host)
    start_time = time.time()
    elapsed_time = 0
    timeout = 120
    retry_interval = 5

    while elapsed_time < timeout:
        logger.info("elapsed=%d, timeout=%d" % (elapsed_time, timeout))
        try:
            dut.connection.open()
            break
        except Exception as e:
            logger.error("Failed to open connection to %s, exception: %s" % (dut.connection.host, repr(e)))
            time.sleep(retry_interval)
            elapsed_time = time.time() - start_time

    if elapsed_time >= timeout:
        logger.error("Retry connecting to %s timeout after %d seconds." % (dut.connection.host, timeout))
        logger.error("Failed to reconnect to %s after reboot." % dut.connection.host)
        sys.exit(1)

    logger.info("Done rebooting")

    if not wait_until(300, 20, dut.critical_services_fully_started):
        logger.error("Not all critical services are started after 300 seconds")
        sys.exit(1)

    sanity_results = sanity_check(dut, sonic_mgmt_container, args.dut_name, args.sonic_topo)
    if not sanity_results:
        logger.info("Sanity check passed")
        sys.exit(0)
    else:
        logger.error("Sanity check failed:\n%s" % json.dumps(sanity_results, indent=4))
        sys.exit(1)
