#!/usr/bin/env python

try:
    # Builtin libs
    import argparse
    import time

    # Third-party libs
    from fabric import Config
    from fabric import Connection

    # Home-brew libs
    from lib import constants
    from lib.devices import SonicDevice
    from lib.utils import parse_topology, get_logger

except ImportError as e:
    raise ImportError (str(e) + "- required module not found")

logger = get_logger("Shutdown Interfaces")
SHUTDOWN_INTERFACES_DELAY = 15
INTERFACES_UP_DELAY = 60

def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--interface", dest="iface", help="First interface name to start shutdown from")
    return parser.parse_args()

def main():
    args = _parse_args()
    topo = parse_topology(args.topo)
    dut_device = topo.get_device_by_topology_id(constants.DUT_DEVICE_ID)
    dut = SonicDevice(dut_device.BASE_IP, dut_device.USERS[0].USERNAME, dut_device.USERS[0].PASSWORD)
    if str(args.iface) != "None":
        i = 0
        iface_index = int(args.iface.replace('Ethernet',''))
        while(i < 5):
            interfaces = dut.show_interface_status()
            if len(interfaces) > 0:
                if any(d['interface'] == args.iface for d in interfaces):
                    for iface in interfaces:
                        if int(iface['interface'].replace('Ethernet','')) >= iface_index:
                            dut.run('sudo config interface shutdown {}'.format(iface['interface']))
                else:
                    logger.error("Start interface is not exist on DUT")
                    return
                break
            else:
                i += 1
                logger.info("Interfaces are down, waiting to go up. retry number {} of 5 retries".format(i))
                time.sleep(INTERFACES_UP_DELAY)

        if i == 5:
            logger.error("Interfaces are down after 5 retries, aborting...")
            return

        time.sleep(SHUTDOWN_INTERFACES_DELAY)
    else:
        return

if __name__ == '__main__':
    main()
